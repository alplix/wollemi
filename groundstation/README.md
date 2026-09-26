# Ground station kit software

| File | Role |
|---|---|
| `predict.py` | Pass prediction, Doppler and pass statistics with SGP4 (`pip install sgp4`) |
| `decode.py` | Reference decoder for Ginkgo packets (hex, `.gpk` streams), uses `protocol/generated/ginkgo_proto.py` |

```
python groundstation/predict.py --days 7                       # demo orbit, four sites
python groundstation/predict.py --tle L1 L2 --lat 39.93 --lon 32.86 --alt 0.9
python groundstation/decode.py --demo
python groundstation/decode.py --file capture.gpk
```

Design, link margins and hardware plan: `docs/ground-station-kit.md`. Signature verification of telecommands (Ed25519) is still to be added
with a vetted library. The demo orbit is synthetic; use operator-provided elements after launch.
