# CODING PLAN & PROGRESS

Living checklist for the software/firmware side. Read this first when
switching between Windows and Mac work. Check boxes as tasks complete.
Decisions below are LOCKED as of 2026-08-31 — the user is 100% on board.

---

## THE PRODUCT, IN ONE PARAGRAPH (what the user wants — do not drift)

A fingerprint knob that lives in the NuPhy Air75 V3 keyboard, paired with
a tiny USB-C dongle. Together they are a **fingerprint FIDO2 security key**
(the YubiKey Bio idea, but the sensor lives in your keyboard). You touch
the knob instead of typing passwords. The whole point is **seamless, zero
software for buyers** — it works because it speaks standards every OS and
browser already support. Custom helper software is a personal/power-user
extra, NEVER a requirement for a buyer.

## LOCKED ARCHITECTURE (settled this conversation — do not relitigate)

1. **Two devices: KNOB + DONGLE.** Not a single USB-C stick. The knob
   keeps the frozen v7 PCB + ZW0922 sensor, harvest-powered, in the
   keyboard. The dongle is its USB face.
2. **Knob<->dongle link = proprietary 2.4 GHz (Nordic ESB/Gazell), NOT
   BLE.** We own both ends, so ESB wins on power (harvest budget) and
   latency. Security is app-layer (HMAC challenge-proof + ratchet), so
   dropping BLE's link encryption loses nothing.
3. **FIDO2 lives on the DONGLE, not the knob.** Dongle is always
   USB-powered → it holds the per-site keys and does the signing (the
   authenticator). The knob only sends "verified: the owner's finger —
   authorized" over 2.4 GHz. Keeps crypto off the sleepy knob.
4. **Fingerprint matching stays ON the knob's sensor** (ZW0922,
   match-on-sensor). Templates never leave the knob. (Cannot claim
   "secure element" — commodity part — say "on-device, never
   transmitted" instead.)
5. **The dongle is a Logitech-receiver-class device**: nRF52840 does
   radio + USB in one chip; production dongle is a tiny sealed USB-C nub
   (custom PCB — see docs/DONGLE-PCB-HANDOFF.md). Dev on a Seeed XIAO
   nRF52840.
6. **The knob<->dongle authenticated protocol already exists** — the
   HMAC challenge/proof + hash ratchet we built (docs/AUTH-CRYPTO.md),
   tested in software/windows-helper/tests. It becomes the ESB payload.

## WHAT THE PRODUCT DELIVERS (the user's goals, and the mechanism)

- **Web logins / GitHub / Google / passkeys** — FIDO2 on the dongle,
  native in every browser, zero install. PRIMARY GOAL PATH.
- **SSH (VS Code, git)** — FIDO2 `ed25519-sk` keys, touch per use, no
  helper. Interim: ssh-agent confirm (already built).
- **Password autofill** — passkeys replace passwords where supported;
  browser extension for legacy passwords; typer as fallback.
- **Mac lock screen / login / sudo** — CryptoTokenKit keycard (native,
  appless). Now dongle-mediated, not BLE-direct.
- **Windows lock screen** — dongle types the login password as a USB
  keyboard after a knob proof (works now); custom credential provider
  or WBF Hello driver later for native.
- Honest gaps everyone has: FileVault/BitLocker pre-boot wants a typed
  password once per full reboot; consumer lock screens aren't FIDO2.

---

## TASKS

### Firmware — knob (Zephyr, nRF52840, board touchid_module) — mostly DONE
- [x] Custom board DTS, LFRC clock, pin map from netlist
- [x] Power state machine (U4 sequencing, VBAT_OK gating)
- [x] EF-01 sensor driver (verified vs Hi-Link manual, host-tested)
- [x] Fake sensor tool for jig-day (firmware/tools/fake_zw0922.py)
- [ ] **Swap knob radio from BLE GATT to ESB** toward the dongle
      (currently ble.c is BLE peripheral; becomes ESB peer)
- [ ] **Two key slots in NVS** (`K_kd`, `K_kh`) with independent ratchet
      state and per-key resync; answer each challenge with the key its
      selector byte names (authkey.c currently stores a single K)
- [ ] Per-bond/per-host handling if knob ever pairs >1 dongle
- [ ] Sleep/advertising → sleep/ESB-listen policy vs ~6 uA budget
- [ ] First flash + on-hardware verification (needs knob PCB)

### Firmware — dongle (nRF52840, dev on XIAO) — NOT STARTED
- [ ] Bring-up: flash a XIAO, USB enumerates, LED blinks
- [ ] **Vendor HID control channel to the host** — the Mac host side is
      already written and waiting: docs/DONGLE-HOST-PROTOCOL.md has the
      full report format and a firmware checklist
- [ ] ESB link to the knob (pair, exchange the HMAC challenge/proof)
- [ ] Port the auth crypto to the dongle (reuse authkey.c). **Two keys,
      decided 2026-08-31**: `K_kd` knob↔dongle gates FIDO2 signing,
      `K_kh` knob↔host is relayed opaquely for the Mac lane. MAC input
      unchanged (existing vectors stay valid); selector byte rides with
      the challenge on ESB only. See docs/DONGLE-HOST-PROTOCOL.md.
- [ ] **USB HID keyboard personality** — type a stored login password
      after a verified knob proof (Windows lock-screen route)
- [ ] **FIDO2/CTAP2 authenticator** — fork OpenSK; knob touch = user
      verification; per-site keys on the dongle
- [ ] U2F (CTAP1) fallback (near-free with OpenSK)
- [ ] Per-host secret storage (Mac vs Windows login passwords)

### Mac software (software/mac-helper/, Swift) — TOKEN WORKS, TRANSPORT MID-REWORK
- [x] xcodegen project, AuthCrypto Swift port (verified against the
      Python vectors), CTK token extension
- [x] First-launch key + self-signed cert generation (CertBuilder emits
      the X.509 by hand; checked against `openssl x509`)
- [x] Keychain persistence for the ratcheting key (KeyStore)
- [x] App↔extension sign bridge, gating every signature on a verified
      touch — CFMessagePort, not NSXPC (a plain app can't host a launchd
      mach service); Sources/Shared/KnobIPC.swift says why
- [x] **PROVEN END TO END on this Mac (simulated knob, 2026-08-31):**
      `sudo id -u` → `0` authenticated by the card, password never
      typed; signature verifies against the card's cert; and with the
      simulator off it correctly FAILS, so the touch gate is
      load-bearing. Needed three things nobody documents: the token must
      support **ECDH key exchange** (login unwraps a secret to the card —
      a signature-only key fails pairing with CTK -8), the key needs
      `canPerformKeyExchange`, and the cert needs **keyAgreement** in
      keyUsage. Pairing lives in AuthenticationAuthority, not
      AltSecurityIdentities.
- [x] Build + verify on a real Mac: token loads, keychain vends the
      identity, login window lists it, `sudo` PAM already smartcard-ready.
      macOS 26+ landmines documented in docs/MAC-KEYCARD.md — flat
      `com.apple.ctk.class-id` keys (the documented legacy dict
      **crash-loops ctkd**), never set NSExtensionPrincipalClass,
      TKTokenDriver.Configuration is blocking XPC, and `sc_auth pair` is
      broken → pair via `dscl` AltSecurityIdentities pubkeyhash
- [~] **Rework: talk to the DONGLE over USB, not the knob over BLE** —
      host side DONE and building: `KnobTransport` seam, `DongleClient`
      over IOHIDManager (vendor usage page 0xFF00, no driver/TCC prompt),
      wire format in docs/DONGLE-HOST-PROTOCOL.md. BLE client preserved
      in software/mac-helper/archive/ble-direct/. **Blocked on dongle
      firmware existing before it can be run against hardware.**
- [ ] Custom TKTokenAuthOperation = knob touch (still the stock PIN op:
      the lock screen shows a PIN field, type anything — the touch is
      the real gate)
- [ ] Remove the menu-bar app; fold link into the CTK token extension
      (appless, seamless — user requirement). Now plausible: with USB
      instead of BLE the extension could own the link itself. Open
      question is where provisioning/enrollment UI lives — a setup-only
      app that isn't resident is probably the answer.

### Windows software (software/windows-helper/, Python) — HELPER DONE
- [x] Vault (Credential Locker), git credential adapter, askpass
      (passphrase + touch-to-approve), typer, serve daemon, tests
- [ ] Repoint from BLE to the dongle transport once dongle firmware exists
- [ ] Browser extension (Chrome/Edge) + native-messaging bridge (autofill)
- [ ] Later: custom credential provider (native lock-screen login)
- [ ] Much later: WBF Hello sensor driver (knob becomes Windows Hello)

### Cross-cutting
- [ ] Browser extension (serves BOTH OSes for legacy-password autofill)
- [ ] Key-wrapping hardening: vault entries encrypted with knob-held
      material so the PC stores only ciphertext (phase 2)

---

## WORKING NOTES FOR WHOEVER PICKS THIS UP (Windows or Mac session)

- Env: Zephyr v4.2.0 workspace at ~/zephyrproject; Mac work needs Xcode.
- The auth crypto is the shared contract: docs/AUTH-CRYPTO.md. Python is
  the reference implementation with tests; Swift port must stay identical.
- Do NOT reintroduce BLE between knob and host — the transport is
  ESB knob<->dongle, USB dongle<->host. BLE-direct sketches predate this.
- Do NOT propose a single self-contained USB-C fingerprint stick — the
  user chose knob+dongle deliberately.
- Hardware for the dongle: docs/DONGLE-PCB-HANDOFF.md.
