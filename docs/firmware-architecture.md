# Firmware and flight-software architecture (draft v0)

Design rule number one: **the spacecraft must keep producing and returning long-record science even
after the Linux computers are gone.** Everything below follows from the tiered lifetime in
`docs/longevity.md`.

## 1. Processors and roles

| Node | Hardware | OS / runtime | Role | Expected life |
|---|---|---|---|---|
| **SUP** | MSP430FR (FRAM) | bare metal C, tiny cooperative loop | Supervisor: watchdog for every node, power-cycling, beacon, survival mode, key store, deployment sequencer | 50+ yr |
| **FC-A / FC-B** | STM32H7 x2 (hot standby) | Zephyr RTOS, C (Rust for new modules) | Flight controller: mode manager, FDIR, power and thermal control, ADCS, scheduler, TM/TC, long-life instrument data path | 30-50 yr |
| **MMU** | RP2350 / STM32 class | Zephyr or bare metal | Mass memory unit: erasure-coded object store, scrubbing, quotas | 25-50 yr (adaptive stripes) |
| **PAY-L** | Raspberry Pi CM5 | Linux (read-only root, overlay) | Always-on data handling, S-band/CFDP engine, compression, relay | 10-15 yr |
| **PAY-H** | Jetson Orin Nano | Linux (read-only root, overlay) | Heavy compute: imaging pipeline, hyperspectral processing, target selection, AI | 10-15 yr |

Each node has an immutable boot stage (ROM/OTP or write-protected flash) that is never updated in
flight, plus two application slots (A/B).

## 2. Buses

- **Control plane:** CAN-FD, two redundant buses (A and B). Every node is on both. Carries commands,
  housekeeping, time, mode changes, heartbeat. Low rate, robust, deterministic.
- **Data plane:** switched Gigabit Ethernet between PAY-L, PAY-H, MMU and the S-band modem.
- **Point-to-point:** UART/SPI/I2C from FC to each instrument; PPS discrete lines for time.
- **Power switching:** each node and instrument behind a latching current limiter controlled by FC and SUP.

Time: CSAC + GNSS PPS disciplined time base on FC-A; distributed over CAN-FD; all data stamped in TAI
with the clock quality flag.

## 3. Layers (per node)

1. Boot stage (immutable) + A/B image selection + confirm-or-rollback.
2. RTOS and drivers (Zephyr baseline; the kernel sits behind a thin OS-abstraction API so it can be
   replaced later).
3. Component framework: components with typed ports (commands, telemetry, events, parameters),
   generated from one protocol description shared by flight and ground.
4. Application components (instrument drivers, ADCS, power, thermal, scheduler, mode manager, FDIR).
5. Data services: CCSDS Space Packets, CFDP file transfer, object store client.

## 4. Modes and degradation ladder

`LAUNCH/DEPLOY` -> `COMMISSION` -> `NOMINAL` <-> `SCIENCE` (imaging campaigns) <-> `BURN` (electric
thruster, minimal services) <-> `ECLIPSE` (heavy loads off) -> `SAFE` -> `SURVIVAL`.

| Level | What runs | Trigger |
|---|---|---|
| L0 full | everything | normal |
| L1 no heavy compute | FC, MMU, long-life science chain, comms; Jetson off (Pi optional) | PAY-H or PAY-L lost, or power/thermal limits |
| L2 sun-only | SUP, FC, beacon, long-life science while lit | main packs faded (see longevity) |
| L3 survival | SUP + beacon on the survival bus, direct from the solar string | FC loss, deep power fault |

Transitions are decided by SUP (hardware watchdog, power state) and FC (FDIR); FC cannot override SUP.

## 5. The long-life science chain (mandatory rule)

Instruments with multi-decade records (magnetometer, TSI radiometer, dosimeter, particle spectrometer,
X-ray/UV monitor, GRB counts, CSAC, housekeeping, attitude, SEU/flash experiments):

- are acquired and time-stamped by **FC**, never by Linux nodes;
- are logged as CCSDS packets straight into the **MMU** (and a small FRAM ring as backup);
- are downlinked by the FC/MMU path (CFDP over the S-band modem's serial/Ethernet port, or over UHF for
  priority-1 subsets) even when PAY-L and PAY-H are dead;
- use **self-describing, versioned formats** so the archive stays readable in 50 years.

A static check in the build (planned: `sim/chain_check.py`) will fail the build if a long-life stream
declares a Linux data path.

## 6. Mass memory unit protocol

- Append-only, log-structured **object store**: object = header + payload; each block carries CRC-32C,
  each object a BLAKE2 hash and a priority class (P1..P3).
- **Erasure coding 6+2** across 8 devices; stripe width narrows automatically as devices die
  (rebuild, then re-stripe); catalogue replicated in FRAM on SUP-independent storage plus the MMU.
- Periodic **scrubbing** (read, verify, rewrite) scheduled around thermal and power state; radiation-induced
  bit errors corrected before they accumulate.
- Quotas per priority: raw ring buffer with automatic eviction; P1 data is never evicted before it is
  acknowledged by the ground (CFDP finished + hash confirmed).
- Interfaces: control over CAN-FD, bulk over Ethernet (put/get/list/verify/delete-after-ack).

## 7. Commanding, security and open access

- **Control commands** are signed (Ed25519) with a monotonically increasing counter and a validity window;
  key hierarchy: offline root key, rotating operational keys, keys stored in SUP FRAM (never in Linux).
  Signed, not encrypted: everything stays readable on the air (amateur-band rule).
- **Public relay traffic** (LoRa store-and-forward, telemetry) needs no key; it is rate limited and quota
  bound on PAY-L, isolated from control (separate VLAN and no path to FC commands).
- **Time-tagged command queue** on FC: absolute time or orbit-position triggers, with dependency and
  abort conditions; survives resets (FRAM-backed).
- Collision-avoidance burns are ordinary time-tagged sequences validated on the ground against power, attitude
  and thermal state (sun-biased, minimal-service burn mode).

## 8. Onboard tasking and autonomy

- Ground uploads **goals** (targets, cadence, priority); PAY-H proposes a plan (cloud cover, sun angle,
  storage, energy) and FC validates and executes it. If PAY-H is dead FC falls back to pre-loaded schedules.
- Imaging pipeline: PAY-H selects and compresses; results go to MMU with metadata; PAY-L handles the downlink
  queue by priority (P1 first, imaging fills the remainder).
- Data budget and priorities follow `configs/12u_data.toml`.

## 9. Updates (OTA)

- Signed manifest + hash; chunked transfer via CFDP over many passes, resumable; delta updates where possible.
- Written to the inactive slot, verified, then booted once; the node must send a **confirm** to SUP/FC within
  a timeout or the boot stage rolls back.
- Order for multi-node updates: PAY-H, PAY-L, MMU, FC-B, then FC-A (the standby is always updated first).
- The boot stage and SUP core are never updated in flight; SUP parameters and non-critical modules may be.

## 10. FDIR

- Heartbeats over both CAN buses, watchdogs (hardware on every node, supervised by SUP).
- Fault tree per subsystem (power, thermal, comms, attitude, storage, compute) with staged responses:
  retry -> restart component -> power-cycle node -> switch to redundant unit -> lower degradation level.
- Latch-up and over-current handled in hardware (LCLs) with SUP retry policy; SEU handling via ECC,
  scrubbing and TMR-style voting on critical variables (FC-A/FC-B compare).
- Every FDIR action is logged as a P1 event.

## 11. Verification and tooling

- One flight code base; hardware-in-the-loop and software-only runs use the same binaries against a digital twin
  driven by the `sim/` models (power, thermal, orbit, data budget).
- Configuration lives in the same TOML files as the design (`configs/`), so a derived mission changes
  configuration, not code.
- Protocol description (packets, files, commands) is a single source that generates both flight and ground code
  (`docs/protocol.md`, planned).

## 12. Open items

- Choose the component framework (F Prime or a small in-house one) and Zephyr vs Rust runtime per node.
- Detailed protocol specification, file formats and archive package format.
- FC-A/FC-B hot-standby scheme (lockstep vs primary/monitor) and clock strategy.
- Key ceremony, revocation and the operator-of-record process (needs the licensed operator, see requirements).
- Real-time budget and CPU/memory sizing per node once instruments are chosen.
