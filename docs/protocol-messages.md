# Message reference (generated)

Generated from `protocol/messages.toml` by `protocol/gen.py`; do not edit by hand.

Packet layout: CCSDS primary header (6) | secondary header (8) | [TC: counter u32, valid_until u32] | payload | [TC: Ed25519 signature 64] | CRC-16/CCITT-FALSE (2). Big-endian.

| Name | APID | Node | Kind | Prio | Total bytes | Description |
|---|---|---|---|---|---|---|
| `beacon` | 0x001 | SUP | tm | P1 | 36 | Survival beacon: minimal state, decodable by any listener; sent by the supervisor even in sun-only mode. |
| `hk_sup` | 0x002 | SUP | tm | P1 | 31 | Supervisor housekeeping. |
| `hk_fc` | 0x103 | FCA | tm | P1 | 32 | Flight controller housekeeping and mode manager state. |
| `hk_power` | 0x104 | FCA | tm | P1 | 54 | Power subsystem sample. |
| `hk_thermal` | 0x105 | FCA | tm | P1 | 51 | Temperatures (0.1 degC) at defined sensor points and heater state. |
| `hk_adcs` | 0x106 | FCA | tm | P1 | 49 | Attitude solution, wheel state and pointing mode. |
| `sci_mag` | 0x110 | FCA | tm | P1 | 117 | Magnetometer sample block: 3 axes, 16 samples at 10 Hz, nT/1e-1 units. |
| `sci_tsi` | 0x111 | FCA | tm | P1 | 24 | Total solar irradiance radiometer: irradiance in mW/m2 and shutter/cavity state. |
| `sci_dose` | 0x112 | FCA | tm | P1 | 30 | Radiation dosimeter counters and integrated dose. |
| `sci_particle` | 0x113 | FCA | tm | P1 | 82 | Energetic particle spectrometer: 16 electron and 16 proton channels, 10 s integration. |
| `sci_xray` | 0x114 | FCA | tm | P1 | 35 | Solar X-ray/UV monitor: band fluxes and flare flag. |
| `sci_grb` | 0x115 | FCA | tm | P1 | 83 | GRB detector: binned counts (1 s) in 4 energy channels; trigger information. |
| `sci_csac` | 0x116 | FCA | tm | P2 | 23 | Chip-scale atomic clock state and offset versus GNSS PPS. |
| `sci_seu` | 0x117 | FCA | tm | P1 | 42 | Radiation experiments: bit-flip counters per memory type and per compute node (Jetson, CM5, MCU classes). |
| `event` | 0x120 | FCA | tm | P1 | 28 | Event log record (FDIR action, mode change, fault); every FDIR action is logged at priority 1. |
| `mmu_status` | 0x330 | MMU | tm | P1 | 30 | Mass memory unit state: stripe width, devices alive, usage, scrub progress. |
| `obj_ack` | 0x631 | GND | tc | P1 | 100 | Ground acknowledgment that an object arrived and verified; allows deletion of the onboard copy. |
| `mode_set` | 0x140 | FCA | tc | P1 | 90 | Request a spacecraft mode (NOMINAL, SCIENCE, BURN, ECLIPSE, SAFE). |
| `power_switch` | 0x141 | FCA | tc | P1 | 90 | Switch a latching current limiter on or off. |
| `time_set` | 0x142 | FCA | tc | P2 | 95 | Set or adjust the spacecraft time base. |
| `seq_load` | 0x143 | FCA | tc | P1 | 113 | Load a time-tagged command sequence entry (absolute time or orbit-position trigger). |
| `burn_schedule` | 0x144 | FCA | tc | P1 | 103 | Schedule an electric-thruster burn (validated on the ground for power, attitude and thermal state). |
| `key_rotate` | 0x045 | SUP | tc | P1 | 185 | Install a new operational public key signed by the root key. |
| `ota_begin` | 0x150 | FCA | tc | P2 | 126 | Start an update: target node, image size, manifest hash. |
| `ota_commit` | 0x151 | FCA | tc | P2 | 92 | Verify and switch to the new slot; the node must confirm within the timeout or roll back. |
| `ota_confirm` | 0x052 | SUP | tc | P1 | 90 | Confirm a successfully booted update. |
| `relay_msg` | 0x460 | PAYL | public | P3 | 98 | Public store-and-forward message (amateur band, unencrypted). |

## `beacon`
Survival beacon: minimal state, decodable by any listener; sent by the supervisor even in sun-only mode.  
APID 0x001, payload 20 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `mode` | u8 | 1 |
| 1 | `node_health` | u8 | 1 |
| 2 | `batt_a_mv` | u16 | 2 |
| 4 | `batt_b_mv` | u16 | 2 |
| 6 | `batt_c_mv` | u16 | 2 |
| 8 | `bus_a_mv` | u16 | 2 |
| 10 | `solar_ma` | u16 | 2 |
| 12 | `temp_body_dc` | i16 | 2 |
| 14 | `uptime_s` | u32 | 4 |
| 18 | `reset_count` | u16 | 2 |

## `hk_sup`
Supervisor housekeeping.  
APID 0x002, payload 15 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `watchdog_flags` | u16 | 2 |
| 2 | `lcl_trips` | u16 | 2 |
| 4 | `power_state` | u32 | 4 |
| 8 | `last_fdir_action` | u16 | 2 |
| 10 | `cmd_counter` | u32 | 4 |
| 14 | `key_id` | u8 | 1 |

## `hk_fc`
Flight controller housekeeping and mode manager state.  
APID 0x103, payload 16 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `mode` | u8 | 1 |
| 1 | `level` | u8 | 1 |
| 2 | `seq_running` | u16 | 2 |
| 4 | `cpu_load_pct` | u8 | 1 |
| 5 | `ram_free_kb` | u16 | 2 |
| 7 | `cmd_accepted` | u32 | 4 |
| 11 | `cmd_rejected` | u32 | 4 |
| 15 | `clock_quality` | u8 | 1 |

## `hk_power`
Power subsystem sample.  
APID 0x104, payload 38 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `pack_a_mv` | u16 | 2 |
| 2 | `pack_b_mv` | u16 | 2 |
| 4 | `pack_c_mv` | u16 | 2 |
| 6 | `pack_a_ma` | i16 | 2 |
| 8 | `pack_b_ma` | i16 | 2 |
| 10 | `pack_c_ma` | i16 | 2 |
| 12 | `solar_string_ma` | bytes[12] | 12 |
| 24 | `soc_a_pct` | u8 | 1 |
| 25 | `soc_b_pct` | u8 | 1 |
| 26 | `load_mw` | u32 | 4 |
| 30 | `gen_mw` | u32 | 4 |
| 34 | `lcl_state` | u32 | 4 |

## `hk_thermal`
Temperatures (0.1 degC) at defined sensor points and heater state.  
APID 0x105, payload 35 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `temp_dc` | bytes[32] | 32 |
| 32 | `heater_state` | u16 | 2 |
| 34 | `radiator_state` | u8 | 1 |

## `hk_adcs`
Attitude solution, wheel state and pointing mode.  
APID 0x106, payload 33 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `quat` | bytes[16] | 16 |
| 16 | `rate_mdps` | bytes[6] | 6 |
| 22 | `wheel_rpm` | bytes[8] | 8 |
| 30 | `pointing_mode` | u8 | 1 |
| 31 | `sun_angle_cdeg` | u16 | 2 |

## `sci_mag`
Magnetometer sample block: 3 axes, 16 samples at 10 Hz, nT/1e-1 units.  
APID 0x110, payload 101 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `t0_fine` | u16 | 2 |
| 2 | `n` | u8 | 1 |
| 3 | `samples` | bytes[96] | 96 |
| 99 | `temp_dc` | i16 | 2 |

## `sci_tsi`
Total solar irradiance radiometer: irradiance in mW/m2 and shutter/cavity state.  
APID 0x111, payload 8 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `irradiance_mw_m2` | u32 | 4 |
| 4 | `cavity_temp_dc` | i16 | 2 |
| 6 | `shutter` | u8 | 1 |
| 7 | `quality` | u8 | 1 |

## `sci_dose`
Radiation dosimeter counters and integrated dose.  
APID 0x112, payload 14 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `dose_urad` | u32 | 4 |
| 4 | `counts_low` | u32 | 4 |
| 8 | `counts_high` | u32 | 4 |
| 12 | `temp_dc` | i16 | 2 |

## `sci_particle`
Energetic particle spectrometer: 16 electron and 16 proton channels, 10 s integration.  
APID 0x113, payload 66 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `integ_ds` | u16 | 2 |
| 2 | `electrons` | bytes[32] | 32 |
| 34 | `protons` | bytes[32] | 32 |

## `sci_xray`
Solar X-ray/UV monitor: band fluxes and flare flag.  
APID 0x114, payload 19 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `integ_ds` | u16 | 2 |
| 2 | `bands` | bytes[16] | 16 |
| 18 | `flare_flag` | u8 | 1 |

## `sci_grb`
GRB detector: binned counts (1 s) in 4 energy channels; trigger information.  
APID 0x115, payload 67 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `t0_fine` | u16 | 2 |
| 2 | `counts` | bytes[64] | 64 |
| 66 | `trigger_flag` | u8 | 1 |

## `sci_csac`
Chip-scale atomic clock state and offset versus GNSS PPS.  
APID 0x116, payload 7 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `offset_ns` | i32 | 4 |
| 4 | `lock` | u8 | 1 |
| 5 | `temp_dc` | i16 | 2 |

## `sci_seu`
Radiation experiments: bit-flip counters per memory type and per compute node (Jetson, CM5, MCU classes).  
APID 0x117, payload 26 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `sram_flips` | u32 | 4 |
| 4 | `fram_flips` | u32 | 4 |
| 8 | `nand_slc_errs` | u32 | 4 |
| 12 | `nand_tlc_errs` | u32 | 4 |
| 16 | `nand_qlc_errs` | u32 | 4 |
| 20 | `jetson_err` | u16 | 2 |
| 22 | `cm5_err` | u16 | 2 |
| 24 | `mcu_err` | u16 | 2 |

## `event`
Event log record (FDIR action, mode change, fault); every FDIR action is logged at priority 1.  
APID 0x120, payload 12 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `event_id` | u16 | 2 |
| 2 | `severity` | u8 | 1 |
| 3 | `source_node` | u8 | 1 |
| 4 | `arg0` | u32 | 4 |
| 8 | `arg1` | u32 | 4 |

## `mmu_status`
Mass memory unit state: stripe width, devices alive, usage, scrub progress.  
APID 0x330, payload 14 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `devices_alive` | u8 | 1 |
| 1 | `stripe_data` | u8 | 1 |
| 2 | `stripe_parity` | u8 | 1 |
| 3 | `used_gb` | u16 | 2 |
| 5 | `free_gb` | u16 | 2 |
| 7 | `scrub_pct` | u8 | 1 |
| 8 | `corrected_errs` | u32 | 4 |
| 12 | `uncorrectable` | u16 | 2 |

## `obj_ack`
Ground acknowledgment that an object arrived and verified; allows deletion of the onboard copy.  
APID 0x631, payload 12 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `object_id` | u32 | 4 |
| 4 | `hash8` | bytes[8] | 8 |

## `mode_set`
Request a spacecraft mode (NOMINAL, SCIENCE, BURN, ECLIPSE, SAFE).  
APID 0x140, payload 2 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `mode` | u8 | 1 |
| 1 | `reason` | u8 | 1 |

## `power_switch`
Switch a latching current limiter on or off.  
APID 0x141, payload 2 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `lcl_id` | u8 | 1 |
| 1 | `state` | u8 | 1 |

## `time_set`
Set or adjust the spacecraft time base.  
APID 0x142, payload 7 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `coarse` | u32 | 4 |
| 4 | `fine` | u16 | 2 |
| 6 | `mode` | u8 | 1 |

## `seq_load`
Load a time-tagged command sequence entry (absolute time or orbit-position trigger).  
APID 0x143, payload 25 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `slot` | u16 | 2 |
| 2 | `trigger_type` | u8 | 1 |
| 3 | `trigger_value` | u32 | 4 |
| 7 | `cmd_apid` | u16 | 2 |
| 9 | `cmd_args` | bytes[16] | 16 |

## `burn_schedule`
Schedule an electric-thruster burn (validated on the ground for power, attitude and thermal state).  
APID 0x144, payload 15 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `start_coarse` | u32 | 4 |
| 4 | `duration_s` | u32 | 4 |
| 8 | `dir_x_mm` | i16 | 2 |
| 10 | `dir_y_mm` | i16 | 2 |
| 12 | `dir_z_mm` | i16 | 2 |
| 14 | `thrust_pct` | u8 | 1 |

## `key_rotate`
Install a new operational public key signed by the root key.  
APID 0x045, payload 97 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `key_id` | u8 | 1 |
| 1 | `pubkey` | bytes[32] | 32 |
| 33 | `root_sig` | bytes[64] | 64 |

## `ota_begin`
Start an update: target node, image size, manifest hash.  
APID 0x150, payload 38 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `target_node` | u8 | 1 |
| 1 | `slot` | u8 | 1 |
| 2 | `size` | u32 | 4 |
| 6 | `hash` | bytes[32] | 32 |

## `ota_commit`
Verify and switch to the new slot; the node must confirm within the timeout or roll back.  
APID 0x151, payload 4 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `target_node` | u8 | 1 |
| 1 | `slot` | u8 | 1 |
| 2 | `confirm_timeout_s` | u16 | 2 |

## `ota_confirm`
Confirm a successfully booted update.  
APID 0x052, payload 2 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `target_node` | u8 | 1 |
| 1 | `slot` | u8 | 1 |

## `relay_msg`
Public store-and-forward message (amateur band, unencrypted).  
APID 0x460, payload 82 bytes.

| Offset | Field | Type | Bytes |
|---|---|---|---|
| 0 | `from_call` | bytes[8] | 8 |
| 8 | `to_call` | bytes[8] | 8 |
| 16 | `msg_id` | u16 | 2 |
| 18 | `text` | bytes[64] | 64 |

