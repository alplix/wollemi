# Architecture (draft v0)

## Principle: platform + payload

```
 +--------------------------- Bus (reusable) ----------------------------+
 |  Structure | EPS (solar, MPPT, battery) | OBC (main + watchdog MCU)   |
 |  Comms (UHF LoRa) | Thermal | Harness/backplane                     |
 +-----------------------------------------------------------------------+
        | standard payload interface (power + data + sync)
 +--------+---------+---------+---------+
 | SEU exp | Magnetometer | Camera | Any future payload |
 +---------+--------------+--------+--------------------+
```

A new mission replaces payload modules and edits one config file; the bus stays.

## Payload interface (proposed)

- Power: `VBAT` (unregulated, 6-8.4 V), `3V3`, `5V`, each switchable and current-limited per slot.
- Data: CAN (primary), I2C/SPI (simple sensors), UART (debug).
- Discrete: `PPS` time sync, `PWR_EN`, `FAULT`.
- Mechanical: PC/104-style stack or card-edge slots, fixed hole pattern, defined keep-out zones.
- Each payload declares its power, mass and data needs in a TOML block (see `configs/`).

## Reliability approach (COTS in LEO)

- Two MCUs: main OBC plus independent watchdog/supervisor.
- Latch-up protection: current sensing and power cycling per rail.
- Critical data in FRAM with checksums; ECC or scrubbing for RAM where possible.
- Safe mode: beacon-only, deployable panels stay deployed, minimal loads.

## Density levers

1. Deployable solar wings (biggest gain).
2. PCB as structure, fewer connectors and harness.
3. Integrated SoC for RF and control; high-efficiency converters.
4. Duty cycling with battery buffering.
5. On-board processing to reduce downlink volume.

## Scaling

Form factor is a config parameter (`units`); structure, panel area and battery
count follow from it. Same bus targets 1U to 6U.
