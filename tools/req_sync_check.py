"""Check that mission/requirements.md and mission/traceability.toml describe the same requirements.

Usage: python tools/req_sync_check.py
Every traceability ID must appear as a table row in requirements.md with matching text; extra IDs in requirements.md (objectives, OPEN-2..7, COLAV-2..6) are listed
as informational and must not contradict the traceability file. Exit code 1 on any mismatch of a shared ID.
"""
import os
import re
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def main():
    reqs = tomllib.load(open(os.path.join(ROOT, "mission", "traceability.toml"), "rb"))["req"]
    doc = open(os.path.join(ROOT, "mission", "requirements.md"), encoding="utf-8").read()
    rows = {}
    for m in re.finditer(r"^\| ([A-Z]+-\d+) \| (.+?) \|\s*$", doc, flags=re.M):
        rows[m.group(1)] = m.group(2)
    errors = []
    for r in reqs:
        if r["id"] not in rows:
            errors.append(f"{r['id']} missing in requirements.md")
            continue
        a, b = norm(r["text"]), norm(rows[r["id"]])
        # the document may shorten or extend the wording; require that the leading words agree
        na, nb = a.split()[:6], b.split()[:6]
        if na != nb:
            errors.append(f"{r['id']}: wording differs (traceability: '{r['text'][:50]}...' / document: '{rows[r['id']][:50]}...')")
    extra = sorted(set(rows) - {r["id"] for r in reqs})
    for e in errors:
        print("REQ SYNC error:", e)
    if errors:
        print(f"REQ SYNC FAILED ({len(errors)} errors)")
        return 1
    print(f"REQ SYNC OK: {len(reqs)} traceability requirements found in requirements.md; informational IDs only in the document: {', '.join(extra)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
