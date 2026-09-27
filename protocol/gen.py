"""Generate the Wollemi protocol code and reference from protocol/messages.toml.

Usage: python protocol/gen.py
Outputs:
  protocol/generated/wollemi_proto.py   ground / test implementation
  protocol/generated/wollemi_proto.h    flight implementation (header-only C99, no dynamic memory)
  docs/protocol-messages.md            message reference
"""
import os
import re
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SIZES = {"u8": 1, "u16": 2, "u32": 4, "i8": 1, "i16": 2, "i32": 4, "f32": 4}
PYFMT = {"u8": "B", "u16": "H", "u32": "I", "i8": "b", "i16": "h", "i32": "i", "f32": "f"}
CTYPE = {"u8": "uint8_t", "u16": "uint16_t", "u32": "uint32_t", "i8": "int8_t", "i16": "int16_t",
         "i32": "int32_t", "f32": "float"}
SEC_LEN = 8
TC_EXTRA = 8
SIG = 64
CRC = 2
PRIMARY = 6


def field_size(t):
    m = re.fullmatch(r"bytes\[(\d+)\]", t)
    return int(m.group(1)) if m else SIZES[t]


def load():
    return tomllib.load(open(os.path.join(HERE, "messages.toml"), "rb"))


def layout(msg):
    off, out = 0, []
    for name, t in msg["fields"]:
        out.append((name, t, off, field_size(t)))
        off += field_size(t)
    return out, off


def total_len(msg, payload):
    n = PRIMARY + SEC_LEN + payload + CRC
    if msg["kind"] == "tc":
        n += TC_EXTRA + SIG
    return n


def gen_python(cfg):
    nodes = cfg["nodes"]
    L = ['"""GENERATED from protocol/messages.toml by protocol/gen.py. Do not edit."""',
         "import struct", "", f"NODES = {nodes!r}", "NODE_NAMES = {v: k for k, v in NODES.items()}",
         f"SEC_LEN = {SEC_LEN}", f"TC_EXTRA = {TC_EXTRA}", f"SIG_LEN = {SIG}", "",
         "MESSAGES = {}", ""]
    for m in cfg["message"]:
        lay, size = layout(m)
        apid = (nodes[m["node"]] << 8) | m["id"]
        L.append(f"MESSAGES[{apid}] = dict(name={m['name']!r}, id={m['id']}, node={m['node']!r}, kind={m['kind']!r}, "
                 f"priority={m['priority']}, version={m.get('version', 1)}, payload_len={size}, "
                 f"fields={[(n, t, o, s) for n, t, o, s in lay]!r})")
    L += ['''
BY_NAME = {v["name"]: (k, v) for k, v in MESSAGES.items()}


def crc16(data, crc=0xFFFF):
    """CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF)."""
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _pack_fields(msg, values):
    out = bytearray()
    for name, t, off, size in msg["fields"]:
        v = values[name]
        if t.startswith("bytes"):
            v = bytes(v)
            if len(v) > size:
                raise ValueError(f"{name}: {len(v)} > {size} bytes")
            out += v + bytes(size - len(v))
        else:
            fmt = {"u8": ">B", "u16": ">H", "u32": ">I", "i8": ">b", "i16": ">h", "i32": ">i", "f32": ">f"}[t]
            out += struct.pack(fmt, v)
    return bytes(out)


def _unpack_fields(msg, data):
    vals = {}
    for name, t, off, size in msg["fields"]:
        raw = data[off:off + size]
        if t.startswith("bytes"):
            vals[name] = bytes(raw)
        else:
            fmt = {"u8": ">B", "u16": ">H", "u32": ">I", "i8": ">b", "i16": ">h", "i32": ">i", "f32": ">f"}[t]
            vals[name] = struct.unpack(fmt, raw)[0]
    return vals


def encode(name, values, seq=0, coarse=0, fine=0, priority=None, clock_quality=3,
           counter=0, valid_until=0, signature=None):
    """Build a complete packet (primary header, secondary header, payload, [signature], CRC)."""
    apid, msg = BY_NAME[name]
    prio = msg["priority"] if priority is None else priority
    payload = _pack_fields(msg, values)
    is_tc = msg["kind"] == "tc"
    sec = struct.pack(">IHBB", coarse, fine, ((clock_quality & 3) << 6) | (((prio - 1) & 3) << 4), msg["version"])
    body = sec
    if is_tc:
        body += struct.pack(">II", counter, valid_until)
    body += payload
    if is_tc:
        sig = bytes(signature) if signature is not None else bytes(SIG_LEN)
        if len(sig) != SIG_LEN:
            raise ValueError("signature must be 64 bytes")
        body += sig
    length = len(body) + 2 - 1
    word0 = (0 << 13) | ((1 if is_tc else 0) << 12) | (1 << 11) | (apid & 0x7FF)
    word1 = (3 << 14) | (seq & 0x3FFF)
    pkt = struct.pack(">HHH", word0, word1, length) + body
    return pkt + struct.pack(">H", crc16(pkt))


def decode(pkt):
    """Parse a packet; returns a dict, raises ValueError on structural or CRC errors."""
    if len(pkt) < 6 + SEC_LEN + 2:
        raise ValueError("too short")
    word0, word1, length = struct.unpack(">HHH", pkt[:6])
    if word0 >> 13 != 0:
        raise ValueError("bad CCSDS version")
    if length + 1 + 6 != len(pkt):
        raise ValueError("length field mismatch")
    if crc16(pkt[:-2]) != struct.unpack(">H", pkt[-2:])[0]:
        raise ValueError("CRC error")
    apid = word0 & 0x7FF
    msg = MESSAGES.get(apid)
    if msg is None:
        raise ValueError(f"unknown APID {apid:#x}")
    is_tc = (word0 >> 12) & 1
    if bool(is_tc) != (msg["kind"] == "tc"):
        raise ValueError("TC bit does not match the message kind")
    coarse, fine, flags, ver = struct.unpack(">IHBB", pkt[6:6 + SEC_LEN])
    pos = 6 + SEC_LEN
    out = dict(name=msg["name"], apid=apid, node=NODE_NAMES[apid >> 8], seq=word1 & 0x3FFF,
               tc=bool(is_tc), coarse=coarse, fine=fine, clock_quality=flags >> 6,
               priority=((flags >> 4) & 3) + 1, version=ver)
    if is_tc:
        out["counter"], out["valid_until"] = struct.unpack(">II", pkt[pos:pos + 8])
        pos += 8
    plen = msg["payload_len"]
    out["fields"] = _unpack_fields(msg, pkt[pos:pos + plen])
    pos += plen
    if is_tc:
        out["signature"] = bytes(pkt[pos:pos + SIG_LEN])
        out["signed_bytes"] = bytes(pkt[:pos])
    return out
''']
    return "\n".join(L) + "\n"


def gen_c(cfg):
    nodes = cfg["nodes"]
    H = ["/* GENERATED from protocol/messages.toml by protocol/gen.py. Do not edit. */",
         "#ifndef WOLLEMI_PROTO_H", "#define WOLLEMI_PROTO_H", "#include <stdint.h>", "#include <stddef.h>",
         "#include <string.h>", "",
         f"#define WL_SEC_LEN {SEC_LEN}", f"#define WL_TC_EXTRA {TC_EXTRA}", f"#define WL_SIG_LEN {SIG}", ""]
    for k, v in nodes.items():
        H.append(f"#define WL_NODE_{k} {v}")
    H += ["", "typedef struct {", "  uint16_t apid; uint16_t seq; uint32_t coarse; uint16_t fine; uint8_t clock_quality;",
          "  uint8_t priority; uint8_t version; uint32_t counter; uint32_t valid_until; uint8_t sig[WL_SIG_LEN];",
          "} wl_hdr_t;", "",
          """static inline uint16_t wl_crc16(const uint8_t *d, size_t n) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < n; i++) {
    crc ^= (uint16_t)d[i] << 8;
    for (int b = 0; b < 8; b++) crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
  }
  return crc;
}
static inline void wl_p16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)(v >> 8); p[1] = (uint8_t)v; }
static inline void wl_p32(uint8_t *p, uint32_t v) { wl_p16(p, (uint16_t)(v >> 16)); wl_p16(p + 2, (uint16_t)v); }
static inline uint16_t wl_g16(const uint8_t *p) { return (uint16_t)((p[0] << 8) | p[1]); }
static inline uint32_t wl_g32(const uint8_t *p) { return ((uint32_t)wl_g16(p) << 16) | wl_g16(p + 2); }
static inline void wl_pf(uint8_t *p, float f) { uint32_t u; memcpy(&u, &f, 4); wl_p32(p, u); }
static inline float wl_gf(const uint8_t *p) { uint32_t u = wl_g32(p); float f; memcpy(&f, &u, 4); return f; }
"""]
    for m in cfg["message"]:
        lay, size = layout(m)
        apid = (nodes[m["node"]] << 8) | m["id"]
        n = m["name"]
        tc = m["kind"] == "tc"
        tot = total_len(m, size)
        H.append(f"/* {n}: {m['doc']} */")
        H.append(f"#define WL_{n.upper()}_APID 0x{apid:03X}")
        H.append(f"#define WL_{n.upper()}_LEN {tot}")
        H.append("typedef struct {")
        for fn, t, off, sz in lay:
            H.append(f"  uint8_t {fn}[{sz}];" if t.startswith("bytes") else f"  {CTYPE[t]} {fn};")
        H.append(f"}} wl_{n}_t;")
        # pack
        H.append(f"static inline int wl_{n}_pack(uint8_t *buf, size_t cap, const wl_{n}_t *m, const wl_hdr_t *h) {{")
        H.append(f"  if (cap < WL_{n.upper()}_LEN) return -1;")
        H.append(f"  size_t o = 6; const uint16_t apid = WL_{n.upper()}_APID;")
        H.append(f"  wl_p16(buf, (uint16_t)((1u << 11) | {'(1u << 12) | ' if tc else ''}apid));")
        H.append("  wl_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));")
        H.append(f"  wl_p16(buf + 4, (uint16_t)(WL_{n.upper()}_LEN - 6 - 1));")
        H.append("  wl_p32(buf + o, h->coarse); wl_p16(buf + o + 4, h->fine);")
        H.append(f"  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = {m.get('version', 1)}; o += WL_SEC_LEN;")
        if tc:
            H.append("  wl_p32(buf + o, h->counter); wl_p32(buf + o + 4, h->valid_until); o += WL_TC_EXTRA;")
        for fn, t, off, sz in lay:
            if t.startswith("bytes"):
                H.append(f"  memcpy(buf + o, m->{fn}, {sz}); o += {sz};")
            elif sz == 1:
                H.append(f"  buf[o] = (uint8_t)m->{fn}; o += 1;")
            elif t == "f32":
                H.append(f"  wl_pf(buf + o, m->{fn}); o += 4;")
            elif sz == 2:
                H.append(f"  wl_p16(buf + o, (uint16_t)m->{fn}); o += 2;")
            else:
                H.append(f"  wl_p32(buf + o, (uint32_t)m->{fn}); o += 4;")
        if tc:
            H.append("  memcpy(buf + o, h->sig, WL_SIG_LEN); o += WL_SIG_LEN;")
        H.append("  wl_p16(buf + o, wl_crc16(buf, o)); o += 2;")
        H.append("  return (int)o;\n}")
        # unpack
        H.append(f"static inline int wl_{n}_unpack(const uint8_t *buf, size_t len, wl_{n}_t *m, wl_hdr_t *h) {{")
        H.append(f"  if (len != WL_{n.upper()}_LEN) return -1;")
        H.append("  if (wl_crc16(buf, len - 2) != wl_g16(buf + len - 2)) return -2;")
        H.append(f"  if ((wl_g16(buf) & 0x7FF) != WL_{n.upper()}_APID) return -3;")
        H.append("  size_t o = 6; h->apid = wl_g16(buf) & 0x7FF; h->seq = wl_g16(buf + 2) & 0x3FFF;")
        H.append("  h->coarse = wl_g32(buf + o); h->fine = wl_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;")
        H.append("  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += WL_SEC_LEN;")
        if tc:
            H.append("  h->counter = wl_g32(buf + o); h->valid_until = wl_g32(buf + o + 4); o += WL_TC_EXTRA;")
        for fn, t, off, sz in lay:
            if t.startswith("bytes"):
                H.append(f"  memcpy(m->{fn}, buf + o, {sz}); o += {sz};")
            elif sz == 1:
                H.append(f"  m->{fn} = ({CTYPE[t]})buf[o]; o += 1;")
            elif t == "f32":
                H.append(f"  m->{fn} = wl_gf(buf + o); o += 4;")
            elif sz == 2:
                H.append(f"  m->{fn} = ({CTYPE[t]})wl_g16(buf + o); o += 2;")
            else:
                H.append(f"  m->{fn} = ({CTYPE[t]})wl_g32(buf + o); o += 4;")
        if tc:
            H.append("  memcpy(h->sig, buf + o, WL_SIG_LEN);")
        H.append("  return 0;\n}\n")
    H.append("#endif /* WOLLEMI_PROTO_H */")
    return "\n".join(H) + "\n"


def gen_doc(cfg):
    nodes = cfg["nodes"]
    D = ["# Message reference (generated)", "",
         "Generated from `protocol/messages.toml` by `protocol/gen.py`; do not edit by hand.", "",
         "Packet layout: CCSDS primary header (6) | secondary header (8) | [TC: counter u32, valid_until u32] | "
         "payload | [TC: Ed25519 signature 64] | CRC-16/CCITT-FALSE (2). Big-endian.", "",
         "| Name | APID | Node | Kind | Prio | Total bytes | Description |", "|---|---|---|---|---|---|---|"]
    for m in cfg["message"]:
        lay, size = layout(m)
        apid = (nodes[m["node"]] << 8) | m["id"]
        D.append(f"| `{m['name']}` | 0x{apid:03X} | {m['node']} | {m['kind']} | P{m['priority']} | {total_len(m, size)} | {m['doc']} |")
    D.append("")
    for m in cfg["message"]:
        lay, size = layout(m)
        D.append(f"## `{m['name']}`")
        D.append(f"{m['doc']}  ")
        D.append(f"APID 0x{(nodes[m['node']] << 8) | m['id']:03X}, payload {size} bytes.")
        D.append("")
        D.append("| Offset | Field | Type | Bytes |")
        D.append("|---|---|---|---|")
        for fn, t, off, sz in lay:
            D.append(f"| {off} | `{fn}` | {t} | {sz} |")
        D.append("")
    return "\n".join(D) + "\n"


def main():
    cfg = load()
    os.makedirs(os.path.join(HERE, "generated"), exist_ok=True)
    open(os.path.join(HERE, "generated", "wollemi_proto.py"), "w", encoding="utf-8").write(gen_python(cfg))
    open(os.path.join(HERE, "generated", "wollemi_proto.h"), "w", encoding="utf-8").write(gen_c(cfg))
    open(os.path.join(ROOT, "docs", "protocol-messages.md"), "w", encoding="utf-8").write(gen_doc(cfg))
    print(f"Generated {len(cfg['message'])} messages: wollemi_proto.py, wollemi_proto.h, docs/protocol-messages.md")


if __name__ == "__main__":
    main()
