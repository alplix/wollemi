# Credits (draft)

Wollemi builds on the work of many open projects and communities. Nothing here implies endorsement by any of them.

## Closest precedents and inspiration

- **OreSat** (Portland State Aerospace Society and collaborators): open-source card/backplane CubeSat architecture, CAN bus with CANopen, open software framework. Wollemi's card and backplane concept is closest to OreSat and follows its CANopen conventions (`docs/decisions/0001-oresat-interoperability.md`).
- **LibreCube**, **UPSat** and the **Libre Space Foundation**, **AcubeSAT**, **EIRSAT-1**, **PULSE-A**: open-source satellite hardware and software, standards use (ECSS, CCSDS).
- **SatNOGS** and **TinyGS**: volunteer ground station networks and open satellite databases.
- **AMSAT** and **AMSAT-OSCAR 7**: proof that a satellite can outlive its battery and its first operators; sun-only survival mode.
- **ThrustMe**: first in-orbit demonstration of an iodine gridded-ion thruster; the propulsion assumptions use its published class figures.
- **CubeSat Design Specification** (Cal Poly and the CubeSat community): the envelope and rails.
- **CCSDS** standards (Space Packet, CFDP) and **AX.25** amateur packet radio.

## Software and tools used

- **KiCad** (electronics, DRC), **build123d** and **OpenCascade** (CAD), **numpy**, **scipy**, **Pillow**, **cryptography** (Ed25519 signing on the ground side), **sgp4** (orbit propagation), **Blender/Cycles** (the photorealistic renders in `mechanical/out/gallery/blender_*`), Python and GCC.
- **TweetNaCl** (Daniel J. Bernstein, Bernard van Gastel, Wesley Janssen, Tanja Lange, Peter Schwabe, Sjaak Smetsers): public-domain Ed25519 implementation used for verification in the firmware core (`firmware/third_party/tweetnacl`).
- **NASA Visible Earth "Blue Marble"** (`mechanical/blender_assets/earth_bluemarble.jpg`, land_ocean_ice_cloud_2048.jpg, https://visibleearth.nasa.gov/images/57735): public-domain Earth imagery (Reto Stockli, Robert Simmon and the MODIS teams) used as the Earth texture in the photorealistic renders; not a copyright claim on Earth, only attribution for the specific image.

## People and organisations

To be completed when the project is opened: authors, contributors, reviewers, sponsors, partner organisations, launch and licensing partners.
