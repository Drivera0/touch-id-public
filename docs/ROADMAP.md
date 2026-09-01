# ROADMAP — the user's stated goals (2026-08-31), in priority order

> **SPEC-CONFORMANCE TARGET (certified fingerprint-key checklist).**
> Achievable (3/4):
> - Biometric AND PIN login — CTAP2 has PIN built in; touch = primary,
>   PIN = fallback (entered on the host during the browser dialog, since
>   the device has no keypad).
> - FIDO U2F + WebAuthn/FIDO2 — via OpenSK on the nRF52840.
> - Cross-OS/browser (Windows, macOS, ChromeOS, Linux, Chrome, Edge) —
>   free with FIDO2-over-USB; scope is the SECURITY-KEY role (web login,
>   passkeys), not desktop lock-screen on all of them.
> NOT claimable as-is (1/4):
> - "Fingerprint template in a certified SECURE ELEMENT." We can say
>   "template stored + matched ON-DEVICE, never transmitted" (true for
>   ZW0922 match-on-sensor / any match-on-chip sensor), but NOT
>   "secure element" — that needs a CC/EAL-certified part + certification
>   we don't have. Wording gap, not a design failure. A real SE is a
>   future hardware (>v7) change.

> **PRODUCT PIVOT (2026-08-31): FIDO2 IS THE PRODUCT.** For future
> buyers, the sellable core is the knob+dongle as a fingerprint FIDO2
> security key (the YubiKey Bio pattern): zero installs — browsers,
> OSes, GitHub/Google, password managers (Bitwarden/1Password/
> KeePassXC unlock), and OpenSSH (ed25519-sk) already speak it.
> OpenSK (nRF52840) is the implementation base. Everything below the
> FIDO2 line — vault/helper, HID typing, Mac keycard, WBF driver — is
> the user's personal power setup / enthusiast extras, NOT a purchase
> prerequisite. Lock screens remain the one surface FIDO2 doesn't
> reach on consumer machines.

> **HARDWARE DIRECTION DECIDED (2026-08-31): KNOB + DONGLE.** User chose
> to keep the knob-in-keyboard (wireless, harvest-powered, v7 board) with
> a USB dongle as its FIDO2/USB face — NOT the simpler single USB-C
> fingerprint stick. BLE is therefore required (it is the knob<->dongle
> link), and the two-device challenge-proof protocol we built stays load-
> bearing. Dev dongle = Nordic PCA10059 (~$10, flash once over USB, no
> jig); a production dongle can be a small custom USB-C device (nRF52840
> has native USB). The round 18mm ZW0922 stays the knob's sensor.
>
> **The dongle is the knob's wired ambassador: radio to the knob, real
> USB device to the OS.**
>
> **KNOB<->DONGLE TRANSPORT (2026-08-31): proprietary 2.4 GHz (Nordic
> ESB/Gazell), not BLE.** BLE is itself 2.4 GHz; the choice is protocol.
> Since we own both ends, BLE's interoperability is wasted — ESB wins on
> POWER (critical for the ~6 uA harvest budget: shorter radio-on, no
> connection upkeep) and LATENCY, with simpler pairing. ESB has no link
> encryption, but our security is app-layer (HMAC challenge-proof +
> ratchet, docs/AUTH-CRYPTO.md), transport-independent, so nothing is
> lost. Consequence: the knob can no longer talk to a host DIRECTLY over
> BLE — everything routes host->USB->dongle->2.4 GHz->knob, so the dongle
> is mandatory (already the decision). The Mac keycard's BLE-direct
> sketch (KnobClient.swift) becomes dongle-mediated. nRF52840 does both,
> so this is a firmware choice, reversible if needed.
> - Lock screens: dongle types the login password as a USB keyboard,
>   but only after the knob's challenge-proof — password never on the
>   knob, never on the radio. Beats knob-HID on every axis.
> - FIDO2: dongle is a USB security key (the transport everything
>   supports, incl. Safari); knob touch = user verification. OpenSK is
>   the reference implementation on this exact board.
> - Bonus: two dongles = real-hardware BLE protocol testing before the
>   knob PCB arrives.

## GOAL 1: unlock the lock screen (Windows AND Mac)

The flagship. Three routes, all compatible with each other:

| route | works | cost | status |
|---|---|---|---|
| firmware HID mode: knob types the login password as a real BLE keyboard — lock screens accept real keyboards | both OSes, day one with hardware | login password stored on knob; types at whatever it's paired to | NOT BUILT — next firmware feature |
| Windows credential provider (DLL loaded into the lock screen; the Duo mechanism) | Windows login only | C++ COM, system install, wrapped password storage | phase 2 |
| **Windows Biometric Framework (WBF) driver** — knob becomes a REAL Windows Hello fingerprint sensor: login, UAC, Chrome's manager, Hello prompts all accept it. Binds to the USB dongle; engine adapter maps our match-on-sensor slots. The Windows north star. (CDF would have been easier but is deprecated/removed.) | Windows, total integration | hardest build in the project: WBDI driver + 3 adapter DLLs in the biometric service; attestation signing or test-signing mode | endgame, after the dongle bridge works |
| macOS **CryptoTokenKit token** — helper presents the knob as a smart card; macOS natively pairs cards with local accounts (login/unlock/sudo). The "keycard" idea from tinyTouch's deleted smartcard firmware, reborn without USB. Preferred over an authorization plugin. | Mac, properly | Swift/CTK work, needs a Mac | phase 2 |

Recommended order: HID mode first (fast, works everywhere), platform
plug-ins after the module is proven in daily use.

Multi-host requirements (user has Mac + Windows, 2026-08-31):
- bonds for both machines; secrets stored PER-BOND (login password and
  vault key K each tagged to the bond that provisioned them — the
  encryption handshake proves host identity, so the knob can never type
  the wrong machine's password). NOTE: current firmware stores a single
  K; per-bond storage is a required change for HID mode.
- switching: prefer last-used host; finger held ~3 s = drop host and
  connect to the other bond (the sensor is the only button).
- production flashes set APPROTECT (debug-port lockout) since the login
  password lives in knob flash.

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
