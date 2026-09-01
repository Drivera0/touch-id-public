# ROADMAP — the user's stated goals (2026-08-31), in priority order

## GOAL 1: unlock the lock screen (Windows AND Mac)

The flagship. Three routes, all compatible with each other:

| route | works | cost | status |
|---|---|---|---|
| firmware HID mode: knob types the login password as a real BLE keyboard — lock screens accept real keyboards | both OSes, day one with hardware | login password stored on knob; types at whatever it's paired to | NOT BUILT — next firmware feature |
| Windows credential provider (DLL loaded into the lock screen; the Duo mechanism) | Windows, properly | C++ COM, system install, wrapped password storage | phase 2 |
| macOS authorization plugin (the Jamf Connect mechanism) | Mac, properly | needs a Mac to build/test | phase 2 |

Recommended order: HID mode first (fast, works everywhere), platform
plug-ins after the module is proven in daily use.

## GOAL 2: fingerprint autofill of passwords (Apple Touch-ID-autofill style)

- Today: `knobauth.typer` types a vault secret into the focused field
  after a touch (works, but manual).
- The real UX: **browser extension + native-messaging bridge** to the
  helper — password field shows "fill with fingerprint", touch, filled.
  One extension serves Chrome/Edge on both OSes. NOT BUILT.
- The endgame: firmware speaks **FIDO2 over BLE** — the knob becomes a
  genuine passkey/security key, sites like GitHub accept it natively,
  no browser software at all. Large firmware project; nRF52840 is
  capable. Future.

## GOAL 3: fingerprint-gated SSH (VS Code, GitHub)

DONE (helper side, 2026-08-31): two modes in `knobauth.askpass`:
- passphrase release ("Enter passphrase for key ...") — vault `ssh:<key>`
- **touch-to-approve** ("Allow use of key ...?") via `ssh-add -c`: the
  agent holds the key; every use by VS Code/git demands a knob touch;
  no secret is released at all. Daemon op: `confirm`.

Future upgrade: FIDO2 (goal 2 endgame) enables `ed25519-sk` SSH keys —
hardware-resident SSH keys, the strongest form.

## Supporting hardening (enables goal 1 & 2 storage)

**Knob-wrapped vault entries**: encrypt each Locker/Keychain entry with
a key held on the knob (sensor Notepad pages are a candidate home), so
the PC stores only ciphertext and a physical touch is cryptographically
required per release. Design discussed 2026-08-31; NOT BUILT.

## Already done

EF-01 driver (host-tested) · GATT auth service · LESC + HMAC + ratchet ·
Windows helper (vault, git adapter, askpass both modes, typer, serve
daemon) · fake sensor tool · flash checklist.

## Blocked on hardware

First flash, protocol verification on the real ZW0922, power
measurement, BL_FLAG thresholds, sleep/advertising tuning.
