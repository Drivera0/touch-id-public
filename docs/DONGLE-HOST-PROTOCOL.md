# DONGLE ↔ HOST PROTOCOL — USB HID

The host side of this exists and builds:
`software/mac-helper/Sources/App/DongleClient.swift`, with the framing
in `Sources/Shared/DongleProtocol.swift`. The dongle side does not exist
yet — this is the contract to write it against.

Chain: knob →(2.4 GHz ESB)→ dongle →(USB HID)→ host.

## Why HID, and why a vendor-defined usage page

- **No driver, no kext, no install.** Every OS binds HID itself, which
  is the "zero software for buyers" requirement in docs/CODING-PLAN.md.
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
BLE Auth Result of docs/AUTH-CRYPTO.md, so:

- the host verifies the HMAC itself and holds its own K,
- the hash ratchet still runs strictly between knob and host,
- a malicious or substituted dongle cannot forge a touch — it has no K,
- `AuthCrypto.swift` and `knobauth/crypto.py` stay byte-identical and
  their existing test vectors keep covering the real path.

The dongle's job is delivery plus link state, nothing more.

## OPEN QUESTION — one K or two?

docs/CODING-PLAN.md also wants the dongle to be the FIDO2 authenticator,
verifying knob proofs *itself* to gate its own signing. That needs a K on
the dongle. But the rule above needs a K on the host that the dongle
cannot know, or the Mac's lock screen is only as trustworthy as any USB
device someone plugs in.

Recommended: **two independent keys and ratchets** — `K_kd` shared
knob↔dongle for FIDO2 decisions, `K_kh` shared knob↔host relayed
transparently for the CTK lane. The knob keeps two slots' worth of key
state and answers each challenge with the matching key. Costs 32 bytes of
NVS and one selector byte in the ESB payload.

The alternative (dongle verifies, tells the host "ok") is simpler but
makes the dongle a trusted intermediary for Mac login. Decide before
writing the knob's ESB code, since it changes the on-air format.

## Dongle firmware checklist

- [ ] Composite USB: vendor HID (this) + boot keyboard; FIDO2 later
- [ ] 64-byte in/out reports, report ID 0, on the vendor interface
- [ ] ESB pairing with the knob; expose link state via STATUS
- [ ] Relay ARM → knob challenge; knob result → AUTH_RESULT verbatim
- [ ] Pass PROVISION_KEY/ENROLL/DELETE through to the knob, ACK the host
- [ ] Answer STATUS without waking the knob where possible (power budget)
- [ ] Pick VID/PID (host matches on usage page today, so dev is unblocked)
