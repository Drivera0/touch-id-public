# DONGLE ↔ HOST PROTOCOL — USB HID

The host side of this exists and builds:
`software/mac-helper/Sources/App/DongleClient.swift`, with the framing
in `Sources/Shared/DongleProtocol.swift`. The dongle side does not exist
yet — this is the contract to write it against.

Chain: knob →(2.4 GHz ESB)→ dongle →(USB HID)→ host.

## Why HID, and why a vendor-defined usage page

- **No driver, no kext, no install.** Every OS binds HID itself, which
  is the "zero software for buyers" requirement in docs/firmware/CODING-PLAN.md.
- **Usage page 0xFF00, usage 0x01.** Vendor-defined pages do *not*
  trigger macOS's Input Monitoring TCC prompt — only keyboard/pointer
  usages do. Windows likewise gives raw access to vendor pages without
  admin rights.
- **Separate HID interface from the others.** The same dongle also
  exposes a boot keyboard (for the Windows lock-screen typing route) and
  later FIDO2/CTAP on usage page 0xF1D0. Three interfaces, one composite
  device; this control channel must not share the FIDO page.

## Framing

64-byte reports both directions, **no report IDs** (report ID 0):

```
byte 0      opcode
byte 1      reserved (0)
bytes 2..3  payload length, big-endian
bytes 4..63 payload, zero-padded
```

Anything longer than 60 payload bytes is invalid; nothing today needs it.

### Host → dongle

| op | name | payload |
|---|---|---|
| 0x01 | ARM | nonce(16) |
| 0x02 | PROVISION_KEY | K(32) |
| 0x03 | ENROLL | slot(2, BE) |
| 0x04 | DELETE_SLOT | slot(2, BE) |
| 0x05 | DELETE_ALL | — |
| 0x06 | STATUS | — |

### Dongle → host

| op | name | payload |
|---|---|---|
| 0x81 | AUTH_RESULT | status(1) slot(2, BE) mac(32) |
| 0x82 | STATUS_REPLY | flags(1) |
| 0x83 | ACK | opcode(1) code(1) |

ACK codes: `0x00` ok, `0x01` bad request, `0x02` knob unreachable,
`0x03` busy. STATUS_REPLY flags: bit 0 knob linked, bit 1 knob has a key.

## The relay rule (important)

**The dongle does not interpret the auth exchange for this lane.** ARM's
nonce goes to the knob unmodified; the knob's 35-byte Auth Result comes
back to the host unmodified as AUTH_RESULT. That payload is exactly the
BLE Auth Result of docs/firmware/AUTH-CRYPTO.md, so:

- the host verifies the HMAC itself and holds its own K,
- the hash ratchet still runs strictly between knob and host,
- a malicious or substituted dongle cannot forge a touch — it has no K,
- `AuthCrypto.swift` and `knobauth/crypto.py` stay byte-identical and
  their existing test vectors keep covering the real path.

The dongle's job is delivery plus link state, nothing more.

## DECIDED (2026-08-31): two keys, two ratchets

The dongle is also the FIDO2 authenticator, so it must verify knob
proofs *itself* to gate its own signing — that needs a key on the
dongle. But the relay rule needs a key on the host that the dongle
cannot know, or Mac login is only as trustworthy as whatever USB device
is plugged in. So there are two, with independent ratchets:

| key | shared between | gates |
|---|---|---|
| `K_kd` | knob ↔ dongle | the dongle's own FIDO2 signing |
| `K_kh` | knob ↔ host | the Mac CTK lane (relayed, opaque to the dongle) |

Consequences, all cheap:

- **The MAC input does not change.** It stays
  `HMAC(K, nonce ‖ status ‖ slot_be16)` exactly as in docs/firmware/AUTH-CRYPTO.md,
  so `crypto.py`, `AuthCrypto.swift` and every existing test vector stay
  valid. Two keys need no format change because a verifier holding the
  wrong key simply fails the MAC — key confusion is not possible, so the
  selector never needs to be authenticated.
- **The selector lives on the ESB link only**, as one byte alongside the
  challenge nonce, telling the knob which key to answer with. It never
  crosses USB.
- **This USB protocol is unchanged.** Host-side ops are always the host
  lane: `PROVISION_KEY` installs `K_kh`. `K_kd` is established during ESB
  pairing and never crosses USB, so the host never learns the dongle's
  key and the dongle never learns the host's.
- **The knob stores two key slots** with independent ratchet state; the
  one-step resync rule applies per key, separately.

## Dongle firmware checklist

- [ ] Composite USB: vendor HID (this) + boot keyboard; FIDO2 later
- [ ] 64-byte in/out reports, report ID 0, on the vendor interface
- [ ] ESB pairing with the knob; expose link state via STATUS
- [ ] Relay ARM → knob challenge; knob result → AUTH_RESULT verbatim
- [ ] Pass PROVISION_KEY/ENROLL/DELETE through to the knob, ACK the host
- [ ] Answer STATUS without waking the knob where possible (power budget)
- [ ] Pick VID/PID (host matches on usage page today, so dev is unblocked)
