# TweetNaCl (third party)

Public-domain compact NaCl implementation (Bernstein et al.), version 20140427, from https://tweetnacl.cr.yp.to/. Used only for Ed25519
signature verification of telecommands (`firmware/common/gk_auth.c`).

SHA-256: `tweetnacl.c` 02e65bc3013ff2168983365e55906bc783c4c7e0a60d8100f17bb303a17175c4, `tweetnacl.h` 43f29ad721d9927b747b0100ab4160c119e7bb180c7c98a66e4bf79d31244287.

Notes: TweetNaCl is designed for compactness and auditability, not speed; verification takes far longer than optimised libraries, which is acceptable
for a few telecommands per pass. Before flight, review a maintained library (for example a formally verified Ed25519) and re-run `firmware/tests/run_tests.py`.
