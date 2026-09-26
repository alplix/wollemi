# Outreach LED package (optional, draft v0)

Idea from the operator: colourful LED lights on the spacecraft. This document records what is physically possible, how it is modelled, and the rules that keep it
from hurting the science mission. Tool: `python sim/led_visibility.py`.

## Two different things

1. **Status LEDs** (small, inside or on the outside of the frame): for integration, ground tests and launch preparation (power OK, CAN heartbeat, mode colour,
   "remove before flight"). Useful, tiny (< 0.1 W), never visible from orbit.
2. **Flasher** (the crowd-pleaser): a collimated RGB LED that flashes toward the ground.

## What a flasher can do from 700 km (on axis, clear sky)

| Light | Beam | Intensity | Magnitude at 700-1000 km |
|---|---|---|---|
| 1 W (100 lm) | 120 deg | 32 cd | 11.5 - 12.3 (invisible) |
| 1 W | 10 deg | 4200 cd | 6.2 - 7.0 (naked-eye limit) |
| **10 W (1000 lm)** | **10 deg** | **42 000 cd** | **3.7 - 4.5 (easily visible)** |
| 10 W | 30 deg | 4700 cd | 6.1 - 6.8 |
| 30 W | 5 deg | 500 000 cd | 1.0 - 1.8 |

Reference: the naked-eye limit is about magnitude 6, the ISS about -4. A 10 degree beam covers a ground swath about 120 km wide, so an observer must be near the
ground track; the nadir-pointing attitude keeps the beam on the Earth during imaging orbits. Colour: an RGB emitter can flash red, green, blue or white; the eye
sees colour on objects brighter than roughly magnitude 3-4, so a 10 W unit shows colour only for a well-placed observer, and a long-exposure camera records it easily.

## What is in the design

- Module `OUTREACH: RGB LED flasher (10 W burst, 10 deg collimated, nadir) + status LEDs`: 0.09 kg, 100 cm3, 10 W at 1 % duty (0.1 W average), at the nadir end of column Q3
  behind a window in the nadir plate (`configs/12u_science.toml`, `12u_geometry.toml`, `12u_layout.toml`); CAD model includes the window.
- Constant-current driver with PWM colour mixing, hardware maximum on-time and thermal cut-off; enabled only by a signed, time-tagged command.

## Rules (why it will not hurt the mission)

- **Never during imaging or observations**: the telescope also looks at nadir, so flashes are allowed only in eclipse or twilight passes when the camera is off; the mode
  manager should forbid the LED in SCIENCE mode (to add to `gk_modes`).
- **Off in safe and survival modes**, and inside the power budget only from the battery in burst mode.
- **Sky courtesy**: bright, unannounced satellites are unpopular with astronomers and the public. Publish flash times and locations, keep the flasher short (seconds per pass),
  and consider an "event only" policy (for example a few dates a year, coordinated with observing communities).
- **Regulation and safety**: at these ranges the eye exposure is negligible, but check national rules for light emission and any launch-provider restriction on bright pulsed sources.
- **The telescope must not be blinded**: the LED sits in a different column from the telescope tube and is baffled from its aperture.

## Open items

- Choose emitter and optics (a 10 degree TIR lens on a high-power RGB LED) and verify the estimated luminous flux and thermal behaviour.
- Pointing accuracy needed to place the beam on a chosen site (attitude knowledge of a few arcminutes is enough for a 10 degree beam).
- Decide whether the flasher stays in the flight configuration or becomes a ground-test-only status board.
