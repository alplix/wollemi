# Public relay policy (draft v0)

Covers `OPEN-3` (any licensed amateur can send and fetch short messages) and `OPEN-6` (rate limits and quotas protect the relay from flooding). The relay carries the `relay_msg`
message (`protocol/messages.toml`, APID 96, kind `public`, priority P3): unsigned, 64-byte text, an 8-byte `from_call` and `to_call`, a 16-bit `msg_id`. Model: a satellite store-and-forward
digipeater, similar in spirit to amateur-satellite PACSAT/APRS relays.

## Why priority alone is not enough

P3 (best effort) already means relay traffic is only sent when P1 (housekeeping) and P2 (science) have nothing queued for that pass, which protects the mission data budget automatically.
It does **not** stop one operator from submitting so many messages that the onboard relay queue itself fills up and crowds out every other operator's messages, so a queue-level policy is
needed as well.

## Quotas

| Limit | Value | Enforced by | Reason |
|---|---|---|---|
| Message size | 64 bytes text (fixed by the wire format) | protocol format | no policy choice needed |
| Submissions per callsign per UTC day | 5 messages | ground ingestion service (below) | keeps one operator from dominating the queue |
| Onboard relay queue depth | 256 pending messages (~21 KB; negligible against the 8x128 GB mass memory) | flight software (`gk_cmdq`-class queue, FDIR-visible) | bounds worst-case memory and, more importantly, worst-case backlog |
| Queue policy when full | drop the oldest undelivered message (FIFO) | flight software | a full queue must not block new submissions or other traffic |
| Undelivered message lifetime | 7 days, then dropped | flight software | stale messages (e.g. from a station outage) should not linger forever |
| Downlink share | none guaranteed; opportunistic only, after P1/P2 | priority scheduler (already in `docs/protocol.md`) | protects science and housekeeping data on a busy day |

These are policy defaults for the reference design, not hard physical limits; a real deployment can tune them (for example after seeing real submission volume) without a protocol change,
since the quota logic lives in ground software and in a small piece of flight software, not in the wire format.

## Submission path (ground infrastructure, not part of the spacecraft)

1. **Open ingestion service**: a simple, publicly reachable web form or API (run by the project or a volunteer, not part of the flight system) accepts `to_call`/`text` submissions from any
   station, checks the per-callsign daily quota, and queues accepted messages.
2. **Upload**: during a command-upload pass, the operator's ground station (or any anchor station with a transmit licence, `docs/ground-station-kit.md`) batches the queued messages into
   `relay_msg` packets and uplinks them alongside normal commanding; no special spacecraft-side submission channel is needed.
3. **Delivery**: any station that receives the spacecraft's S-band or UHF downlink can decode `relay_msg` packets addressed to any callsign (`groundstation/decode.py`) and forward them to
   the intended recipient by whatever means (the spacecraft does not know or care how delivery to `to_call` actually happens on the ground).

## Trust and abuse

- **No strong authentication.** Unlike telecommands, `relay_msg` is unsigned (amateur-band rule, `OPEN-4`/`OPEN-5`): anyone can put any text in `from_call`. This matches how existing amateur
  digipeaters and BBS relays already work, and is disclosed here so operators do not mistake `from_call` for a verified identity.
- **Content is not moderated onboard.** The spacecraft neither reads nor filters the text; moderation, if any, happens at the ground ingestion service (item 1 above), which can reject or
  blocklist a submitting callsign before a message ever reaches the queue. This keeps moderation policy (which can change) out of the flight software (which should not need updates for it).
- **Flooding beyond the quota** (for example many callsigns coordinating to fill the queue) is not fully preventable from a single onboard rule; the queue-depth cap and FIFO drop keep the
  failure mode bounded (old messages are dropped, not a crash or a stuck queue) rather than eliminating the possibility.

## Status

Traced as `OPEN-3` and `OPEN-6` (`mission/traceability.toml`); covered by test `GND-02` (`mission/tests.toml`, fuzz and interoperability of the public message set, quota and abuse drills). The
ground ingestion service itself is not yet built; this document is the specification it should implement.
