# SPDX-FileCopyrightText: 2026 Wollemi contributors
# SPDX-License-Identifier: Apache-2.0
"""GENERATED from protocol/messages.toml by protocol/gen.py. Do not edit."""
import struct

NODES = {'SUP': 0, 'FCA': 1, 'FCB': 2, 'MMU': 3, 'PAYL': 4, 'PAYH': 5, 'GND': 6, 'ALL': 7}
NODE_NAMES = {v: k for k, v in NODES.items()}
SEC_LEN = 8
TC_EXTRA = 8
SIG_LEN = 64

MESSAGES = {}

MESSAGES[1] = dict(name='beacon', id=1, node='SUP', kind='tm', priority=1, version=1, payload_len=20, fields=[('mode', 'u8', 0, 1), ('node_health', 'u8', 1, 1), ('batt_a_mv', 'u16', 2, 2), ('batt_b_mv', 'u16', 4, 2), ('batt_c_mv', 'u16', 6, 2), ('bus_a_mv', 'u16', 8, 2), ('solar_ma', 'u16', 10, 2), ('temp_body_dc', 'i16', 12, 2), ('uptime_s', 'u32', 14, 4), ('reset_count', 'u16', 18, 2)])
MESSAGES[2] = dict(name='hk_sup', id=2, node='SUP', kind='tm', priority=1, version=1, payload_len=15, fields=[('watchdog_flags', 'u16', 0, 2), ('lcl_trips', 'u16', 2, 2), ('power_state', 'u32', 4, 4), ('last_fdir_action', 'u16', 8, 2), ('cmd_counter', 'u32', 10, 4), ('key_id', 'u8', 14, 1)])
MESSAGES[259] = dict(name='hk_fc', id=3, node='FCA', kind='tm', priority=1, version=1, payload_len=16, fields=[('mode', 'u8', 0, 1), ('level', 'u8', 1, 1), ('seq_running', 'u16', 2, 2), ('cpu_load_pct', 'u8', 4, 1), ('ram_free_kb', 'u16', 5, 2), ('cmd_accepted', 'u32', 7, 4), ('cmd_rejected', 'u32', 11, 4), ('clock_quality', 'u8', 15, 1)])
MESSAGES[260] = dict(name='hk_power', id=4, node='FCA', kind='tm', priority=1, version=1, payload_len=38, fields=[('pack_a_mv', 'u16', 0, 2), ('pack_b_mv', 'u16', 2, 2), ('pack_c_mv', 'u16', 4, 2), ('pack_a_ma', 'i16', 6, 2), ('pack_b_ma', 'i16', 8, 2), ('pack_c_ma', 'i16', 10, 2), ('solar_string_ma', 'bytes[12]', 12, 12), ('soc_a_pct', 'u8', 24, 1), ('soc_b_pct', 'u8', 25, 1), ('load_mw', 'u32', 26, 4), ('gen_mw', 'u32', 30, 4), ('lcl_state', 'u32', 34, 4)])
MESSAGES[261] = dict(name='hk_thermal', id=5, node='FCA', kind='tm', priority=1, version=1, payload_len=35, fields=[('temp_dc', 'bytes[32]', 0, 32), ('heater_state', 'u16', 32, 2), ('radiator_state', 'u8', 34, 1)])
MESSAGES[262] = dict(name='hk_adcs', id=6, node='FCA', kind='tm', priority=1, version=1, payload_len=33, fields=[('quat', 'bytes[16]', 0, 16), ('rate_mdps', 'bytes[6]', 16, 6), ('wheel_rpm', 'bytes[8]', 22, 8), ('pointing_mode', 'u8', 30, 1), ('sun_angle_cdeg', 'u16', 31, 2)])
MESSAGES[272] = dict(name='sci_mag', id=16, node='FCA', kind='tm', priority=1, version=1, payload_len=101, fields=[('t0_fine', 'u16', 0, 2), ('n', 'u8', 2, 1), ('samples', 'bytes[96]', 3, 96), ('temp_dc', 'i16', 99, 2)])
MESSAGES[273] = dict(name='sci_tsi', id=17, node='FCA', kind='tm', priority=1, version=1, payload_len=8, fields=[('irradiance_mw_m2', 'u32', 0, 4), ('cavity_temp_dc', 'i16', 4, 2), ('shutter', 'u8', 6, 1), ('quality', 'u8', 7, 1)])
MESSAGES[274] = dict(name='sci_dose', id=18, node='FCA', kind='tm', priority=1, version=1, payload_len=14, fields=[('dose_urad', 'u32', 0, 4), ('counts_low', 'u32', 4, 4), ('counts_high', 'u32', 8, 4), ('temp_dc', 'i16', 12, 2)])
MESSAGES[275] = dict(name='sci_particle', id=19, node='FCA', kind='tm', priority=1, version=1, payload_len=66, fields=[('integ_ds', 'u16', 0, 2), ('electrons', 'bytes[32]', 2, 32), ('protons', 'bytes[32]', 34, 32)])
MESSAGES[276] = dict(name='sci_xray', id=20, node='FCA', kind='tm', priority=1, version=1, payload_len=19, fields=[('integ_ds', 'u16', 0, 2), ('bands', 'bytes[16]', 2, 16), ('flare_flag', 'u8', 18, 1)])
MESSAGES[277] = dict(name='sci_grb', id=21, node='FCA', kind='tm', priority=1, version=1, payload_len=67, fields=[('t0_fine', 'u16', 0, 2), ('counts', 'bytes[64]', 2, 64), ('trigger_flag', 'u8', 66, 1)])
MESSAGES[278] = dict(name='sci_csac', id=22, node='FCA', kind='tm', priority=2, version=1, payload_len=7, fields=[('offset_ns', 'i32', 0, 4), ('lock', 'u8', 4, 1), ('temp_dc', 'i16', 5, 2)])
MESSAGES[279] = dict(name='sci_seu', id=23, node='FCA', kind='tm', priority=1, version=1, payload_len=26, fields=[('sram_flips', 'u32', 0, 4), ('fram_flips', 'u32', 4, 4), ('nand_slc_errs', 'u32', 8, 4), ('nand_tlc_errs', 'u32', 12, 4), ('nand_qlc_errs', 'u32', 16, 4), ('jetson_err', 'u16', 20, 2), ('cm5_err', 'u16', 22, 2), ('mcu_err', 'u16', 24, 2)])
MESSAGES[288] = dict(name='event', id=32, node='FCA', kind='tm', priority=1, version=1, payload_len=12, fields=[('event_id', 'u16', 0, 2), ('severity', 'u8', 2, 1), ('source_node', 'u8', 3, 1), ('arg0', 'u32', 4, 4), ('arg1', 'u32', 8, 4)])
MESSAGES[816] = dict(name='mmu_status', id=48, node='MMU', kind='tm', priority=1, version=1, payload_len=14, fields=[('devices_alive', 'u8', 0, 1), ('stripe_data', 'u8', 1, 1), ('stripe_parity', 'u8', 2, 1), ('used_gb', 'u16', 3, 2), ('free_gb', 'u16', 5, 2), ('scrub_pct', 'u8', 7, 1), ('corrected_errs', 'u32', 8, 4), ('uncorrectable', 'u16', 12, 2)])
MESSAGES[1585] = dict(name='obj_ack', id=49, node='GND', kind='tc', priority=1, version=1, payload_len=12, fields=[('object_id', 'u32', 0, 4), ('hash8', 'bytes[8]', 4, 8)])
MESSAGES[320] = dict(name='mode_set', id=64, node='FCA', kind='tc', priority=1, version=1, payload_len=2, fields=[('mode', 'u8', 0, 1), ('reason', 'u8', 1, 1)])
MESSAGES[321] = dict(name='power_switch', id=65, node='FCA', kind='tc', priority=1, version=1, payload_len=2, fields=[('lcl_id', 'u8', 0, 1), ('state', 'u8', 1, 1)])
MESSAGES[322] = dict(name='time_set', id=66, node='FCA', kind='tc', priority=2, version=1, payload_len=7, fields=[('coarse', 'u32', 0, 4), ('fine', 'u16', 4, 2), ('mode', 'u8', 6, 1)])
MESSAGES[323] = dict(name='seq_load', id=67, node='FCA', kind='tc', priority=1, version=1, payload_len=25, fields=[('slot', 'u16', 0, 2), ('trigger_type', 'u8', 2, 1), ('trigger_value', 'u32', 3, 4), ('cmd_apid', 'u16', 7, 2), ('cmd_args', 'bytes[16]', 9, 16)])
MESSAGES[324] = dict(name='burn_schedule', id=68, node='FCA', kind='tc', priority=1, version=1, payload_len=15, fields=[('start_coarse', 'u32', 0, 4), ('duration_s', 'u32', 4, 4), ('dir_x_mm', 'i16', 8, 2), ('dir_y_mm', 'i16', 10, 2), ('dir_z_mm', 'i16', 12, 2), ('thrust_pct', 'u8', 14, 1)])
MESSAGES[69] = dict(name='key_rotate', id=69, node='SUP', kind='tc', priority=1, version=1, payload_len=97, fields=[('key_id', 'u8', 0, 1), ('pubkey', 'bytes[32]', 1, 32), ('root_sig', 'bytes[64]', 33, 64)])
MESSAGES[336] = dict(name='ota_begin', id=80, node='FCA', kind='tc', priority=2, version=1, payload_len=38, fields=[('target_node', 'u8', 0, 1), ('slot', 'u8', 1, 1), ('size', 'u32', 2, 4), ('hash', 'bytes[32]', 6, 32)])
MESSAGES[337] = dict(name='ota_commit', id=81, node='FCA', kind='tc', priority=2, version=1, payload_len=4, fields=[('target_node', 'u8', 0, 1), ('slot', 'u8', 1, 1), ('confirm_timeout_s', 'u16', 2, 2)])
MESSAGES[82] = dict(name='ota_confirm', id=82, node='SUP', kind='tc', priority=1, version=1, payload_len=2, fields=[('target_node', 'u8', 0, 1), ('slot', 'u8', 1, 1)])
MESSAGES[1120] = dict(name='relay_msg', id=96, node='PAYL', kind='public', priority=3, version=1, payload_len=82, fields=[('from_call', 'bytes[8]', 0, 8), ('to_call', 'bytes[8]', 8, 8), ('msg_id', 'u16', 16, 2), ('text', 'bytes[64]', 18, 64)])

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

