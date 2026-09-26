# Card connector pinouts (generated)

Generated from `electronics/card_pinout.toml` by `electronics/gen_card.py`; do not edit by hand.

## GK-P power and control, 2 x 30

| Pin pair | Row A (odd) | Row B (even) |
|---|---|---|
| 1 (pins 1, 2) | VBAT_A | VBAT_B |
| 2 (pins 3, 4) | VBAT_A | VBAT_B |
| 3 (pins 5, 6) | VBAT_A | VBAT_B |
| 4 (pins 7, 8) | VBAT_A | VBAT_B |
| 5 (pins 9, 10) | VBAT_A | VBAT_B |
| 6 (pins 11, 12) | GND | GND |
| 7 (pins 13, 14) | CAN_A_H | CAN_A_L |
| 8 (pins 15, 16) | GND | GND |
| 9 (pins 17, 18) | CAN_B_H | CAN_B_L |
| 10 (pins 19, 20) | GND | GND |
| 11 (pins 21, 22) | PPS_P | PPS_N |
| 12 (pins 23, 24) | GND | GND |
| 13 (pins 25, 26) | SYNC_P | SYNC_N |
| 14 (pins 27, 28) | GND | GND |
| 15 (pins 29, 30) | SLOT_ID0 | SLOT_ID1 |
| 16 (pins 31, 32) | SLOT_ID2 | SLOT_ID3 |
| 17 (pins 33, 34) | SLOT_SEL0 | SLOT_SEL1 |
| 18 (pins 35, 36) | SLOT_SEL2 | SLOT_SEL3 |
| 19 (pins 37, 38) | KILL_N | FAULT_N |
| 20 (pins 39, 40) | GND | GND |
| 21 (pins 41, 42) | I2C_SCL | I2C_SDA |
| 22 (pins 43, 44) | UART_TX | UART_RX |
| 23 (pins 45, 46) | GND | GND |
| 24 (pins 47, 48) | SWD_CLK | SWD_IO |
| 25 (pins 49, 50) | NRST_DBG | VREF |
| 26 (pins 51, 52) | GND | GND |
| 27 (pins 53, 54) | RESET_N | RSV |
| 28 (pins 55, 56) | RSV | RSV |
| 29 (pins 57, 58) | RSV | RSV |
| 30 (pins 59, 60) | RSV | RSV |

Pin counts: CAN_A_H x1, CAN_A_L x1, CAN_B_H x1, CAN_B_L x1, FAULT_N x1, GND x16, I2C_SCL x1, I2C_SDA x1, KILL_N x1, NRST_DBG x1, PPS_N x1, PPS_P x1, RESET_N x1, RSV x7, SLOT_ID0 x1, SLOT_ID1 x1, SLOT_ID2 x1, SLOT_ID3 x1, SLOT_SEL0 x1, SLOT_SEL1 x1, SLOT_SEL2 x1, SLOT_SEL3 x1, SWD_CLK x1, SWD_IO x1, SYNC_N x1, SYNC_P x1, UART_RX x1, UART_TX x1, VBAT x10, VREF x1

## GK-D data, 2 x 15 (data-plane cards only)

| Pin pair | Row A (odd) | Row B (even) |
|---|---|---|
| 1 (pins 1, 2) | ETH0_P | ETH0_N |
| 2 (pins 3, 4) | GND | GND |
| 3 (pins 5, 6) | ETH1_P | ETH1_N |
| 4 (pins 7, 8) | GND | GND |
| 5 (pins 9, 10) | ETH2_P | ETH2_N |
| 6 (pins 11, 12) | GND | GND |
| 7 (pins 13, 14) | ETH3_P | ETH3_N |
| 8 (pins 15, 16) | GND | GND |
| 9 (pins 17, 18) | LANE0_P | LANE0_N |
| 10 (pins 19, 20) | GND | GND |
| 11 (pins 21, 22) | LANE1_P | LANE1_N |
| 12 (pins 23, 24) | GND | GND |
| 13 (pins 25, 26) | GND | GND |
| 14 (pins 27, 28) | RSV | RSV |
| 15 (pins 29, 30) | RSV | RSV |

Pin counts: ETH0_N x1, ETH0_P x1, ETH1_N x1, ETH1_P x1, ETH2_N x1, ETH2_P x1, ETH3_N x1, ETH3_P x1, GND x14, LANE0_N x1, LANE0_P x1, LANE1_N x1, LANE1_P x1, RSV x4

