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

These magnitudes are on the standard **photopic** (daylight, colour-vision) brightness scale, which is what "magnitude 6 naked-eye limit" normally means for a source bright enough to trigger colour
vision. Reference: the naked-eye limit is about magnitude 6, the ISS about -4. A 10 degree beam covers a ground swath about 120 km wide, so an observer must be near the ground track; a beam fixed
on nadir only reaches an observer close to overhead (a 45 deg elevation observer at 700 km is about 40 deg off nadir, well outside a 10 deg beam), so hitting a chosen ground observer needs the
beam actively steered by the attitude system, not just left pointing at nadir. Colour: an RGB emitter can flash red, green, blue or white; the eye sees colour on objects brighter than roughly
magnitude 3-4, so a 10 W unit shows colour only for a well-placed, steered observer, and a long-exposure camera records it easily regardless of colour vision.

## A purple light: what it is good for (`python sim/led_visibility.py`)

The operator wants a **purple/violet light visible from Earth and from other objects in space**. Physics splits that in two, and a review pass corrected the naked-eye
part: the mag-6 naked-eye limit at a dark site is a **scotopic** (dark-adapted, rod-vision) threshold, not the daylight photopic scale used for colour matching; rods are much
more sensitive to blue/violet and much less sensitive to red than photopic values suggest (the Purkinje effect). `sim/led_visibility.py` now reports both scales:

| Observer | Violet 405 nm | Blue 450 nm | Red 630 nm | (all at 10 W electrical, 10 deg beam) |
|---|---|---|---|---|
| Naked eye, photopic (colour-matching) scale | mag 11.7: invisible | mag 7.0: marginal | mag 5.1: visible | old (misleading) picture |
| Naked eye, scotopic (dark-adapted detection) scale | mag 8.1: **invisible** | mag 4.3: **easily visible** | mag 9.9: **invisible** | the physically correct picture |
| Long-exposure camera on the ground (1000 km) | mag ~5: clearly recorded | mag ~4: clearly recorded | mag ~5: clearly recorded | broadband, not eye-referenced |
| Another spacecraft's camera or star tracker at 100 km / 10 km | mag ~0 / ~-5: very bright | similar | similar | broadband, not eye-referenced |

The old picture had it backwards: **red is nearly undetectable to a dark-adapted naked eye** at this power (a red flash bright enough to look red to the eye needs to trigger
colour vision, which needs far more power than the scotopic detection threshold), while **blue is easily visible at just 10 W**, no power boost needed. Violet stays invisible
to the eye at any reasonable power and remains an excellent **optical beacon for cameras** (ground astro-photographers, cameras and star trackers on nearby spacecraft, inspection
or rendezvous demonstrations). Design choice, updated: **violet 405 nm as the camera beacon** (invisible to the eye, purple in photographs) **plus blue 450 nm as the naked-eye-visible
channel** (visible at 10 W with no boost) **plus red** only for colour richness in photographs, not for naked-eye detection; a blue-violet combination is what a ground observer actually
sees as a purple-blue flash, and a colour photograph of the red + blue + violet combination looks magenta/purple.

Extra uses of the violet beacon: optical tracking test (cameras can measure the spacecraft position and attitude from its flash pattern), identification by pattern (for example a
pulse code that spells the spacecraft ID), and demonstration of spacecraft-to-spacecraft optical detection.

Caution: 405 nm is near-ultraviolet; irradiance at these ranges is many orders of magnitude below eye-safety limits, but confirm against the photobiological safety standard for the chosen emitter.

## What is in the design

- Module `OUTREACH: RGB LED flasher (violet 405 nm main + red + blue, 10 W burst, 10 deg collimated, nadir) + status LEDs`: 0.09 kg, 100 cm3, 10 W at 1 % duty (0.1 W average), at the nadir end of column Q3
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
- Pointing accuracy needed to place the beam on a chosen site (attitude knowledge of a few arcminutes is enough for a 10 degree beam); a beam fixed on nadir only reaches observers close to overhead, so hitting a chosen site needs the beam steered off nadir.
- Decide whether the flasher stays in the flight configuration or becomes a ground-test-only status board.
