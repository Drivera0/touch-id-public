# ZW0922 UART PROTOCOL — EF-01, verified against the Hi-Link manual

**The authority is in the vault:**
`datasheets/HiLink-Fingerprint-Protocol-0xEF01-V1.1.pdf` (103 pp, Hi-Link
"Fingerprint module product user manual"). The ZW0922 *spec sheet* has no
protocol in it — checked page by page 2026-08-31, as were the public
ZW0901/ZW101 sheets; Hi-Link keeps the byte protocol in this separate
manual. Every frame the firmware sends was diffed against it (frame
format §3.1, commands §3.3) — all match.

Cross-corroboration: GavinnnTann/HLK-ZW-Fingerprint-Sensor (Arduino lib,
lists ZW09xx as EF-01) and the tinyTouch .ino (same command flow, shipped).
User decision 2026-08-31: build on EF-01, GATT + helper transport.

**Remaining risk (small): the manual is family-generic, not
ZW0922-stamped.** First hardware conversation = `PS_VfyPwd` ping after
power-on. If it times out at 57600 8N1, ask Hi-Link (sales@hlktech.com)
for a ZW0922-specific protocol doc rather than thrashing.

## Wire format (implemented in firmware/app/src/sensor_zw0922.c)

```
EF 01 | FF FF FF FF | PID | LEN_H LEN_L | INS params... | CS_H CS_L
        address       1B    body + 2      body            16-bit sum
```

- PID: 0x01 command (host→module), 0x07 ack, 0x02/0x08 data stream
- LEN counts body plus the two checksum bytes
- CS = (PID + LEN_H + LEN_L + sum of body bytes) & 0xFFFF
- ack body = confirm code, then payload
- worked example from the manual: GetImage = `EF01 FFFFFFFF 01 0003 01 0005`

## Commands used (all verified against manual §3.3)

| INS | manual name | params | notes |
|---|---|---|---|
| 0x01 | PS_GetImage | — | cc 0x02 = no finger |
| 0x02 | PS_GenChar | BufferID | |
| 0x04 | PS_Search | BufferID, StartPage(2), PageNum(2) | reply: page(2), score(2); cc 0x09 = not found |
| 0x05 | PS_RegModel | — | merge buf1+buf2 |
| 0x06 | PS_StoreChar | BufferID, PageID(2) | |
| 0x0C | PS_DeletChar | PageID(2), N(2) | |
| 0x0D | PS_Empty | — | |
| 0x13 | PS_VfyPwd | Password(4)=0 | the power-on ping |

Deliberately NOT used: HiSpeedSearch (0x1B) — an AS608-era extension
absent from the Hi-Link manual's core set and rejected by some ZW
firmwares; plain PS_Search always works. LED commands (PS_ControlBLN
0x3C) — ZW09xx is a passive-LED variant, and this board wires no LED.

Available if ever useful (in the manual, not implemented):
PS_GetRandomCode 0x14 (on-module RNG), PS_ReadSysPara 0x0F,
PS_Read/WriteNotepad (32-byte user flash pages — a possible home for a
provisioned HMAC key that never transits BLE).

## Confirm-code → errno mapping

0x00 OK → 0 · 0x02 no finger → -EAGAIN · 0x09 not found → -ENOENT ·
timeout → -ETIMEDOUT · bad frame/checksum → -EBADMSG · anything else
→ -EIO (code logged).
