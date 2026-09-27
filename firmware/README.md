# Firmware core (host-testable)

Pure C99 logic that will run unchanged on the flight controller and supervisor; hardware access sits behind a HAL that is not written yet.

| Module | Role |
|---|---|
| `common/wl_auth.*` | Telecommand authentication: CRC, TC check, validity window, replay counter, Ed25519 (TweetNaCl), current + previous key |
| `common/wl_modes.*` | Mode manager and degradation ladder (LAUNCH, DEPLOY, COMMISSION, NOMINAL, SCIENCE, SCIENCE_LITE, BURN, ECLIPSE, SAFE, SURVIVAL; levels L0-L3) |
| `common/wl_fdir.*` | Heartbeat monitoring and escalation retry -> restart -> power-cycle -> switch redundant -> degrade |
| `common/wl_cmdq.*` | Time-tagged command queue (absolute time and orbit position triggers, mode masks, validity windows) |
| `common/wl_ota.*` | A/B update state machine with confirm-or-rollback |
| `../protocol/generated/wollemi_proto.h` | Generated packet code shared with the ground software |

```
pip install cryptography
python firmware/tests/run_tests.py     # builds with gcc -Wall -Wextra -Werror, runs 68 unit checks and the Ed25519 cross-checks
```

The cross-checks sign telecommands in Python (`cryptography`) and verify them in C: valid, replay, expired, wrong key, previous key, forged,
tampered with valid CRC, bad CRC, truncated.

Not done yet: HAL, Zephyr integration and drivers, persistent storage of the counter and keys (FRAM), real-time budget, the key-rotation command handler,
the object store client, and a hardware-in-the-loop harness.
