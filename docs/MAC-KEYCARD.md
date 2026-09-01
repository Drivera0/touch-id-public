# MAC KEYCARD — the knob as a smart card via CryptoTokenKit

The tinyTouch "keycard" idea, reborn without USB: a Mac app presents a
software smart card to macOS (CryptoTokenKit persistent token). macOS
pairs smart cards with **local accounts natively** — after pairing, the
login window, lock screen, and `sudo` accept the card. Our card only
signs when the knob's challenge-proof says your finger touched it.

## What it covers / doesn't

| surface | covered? |
|---|---|
| lock screen / login window (after boot unlock) | ✅ touch to unlock |
| `sudo`, system auth prompts | ✅ |
| FileVault pre-boot (first login after reboot) | ❌ password once per boot — our software isn't loaded yet |
| Safari/Chrome password autofill | ❌ separate lane (goal 2: extension/typer/FIDO2) |

## Architecture (software/mac-helper/)

```
KnobToken.app (menu-bar app)
 ├─ KnobClient.swift    CoreBluetooth central — our GATT protocol
 ├─ AuthCrypto.swift    HMAC verify + one-step ratchet (port of
 │                      knobauth/crypto.py, same test vectors)
 └─ TokenExtension (CTK persistent token, extension point
    com.apple.ctk-tokens)
     └─ exposes 1 ECDSA P-256 key + self-signed cert; every sign
        request → XPC to the app → knob touch proof → sign
```

- **v1 key location:** generated on the Mac, Keychain-held, ACL'd to
  the app. Touch gating is enforced by the app (it refuses to sign
  without a verified proof). Phase 2: wrap the key with knob-held
  material so the gate is cryptographic, or move signing into the knob
  (firmware ECDSA) for the purist version.
- The app is also the Mac home of everything the Windows helper does
  (vault release, ssh confirm) — same wire contract, docs/AUTH-CRYPTO.md.

## Build (on the Mac)

1. Xcode + `brew install xcodegen`
2. `cd software/mac-helper && xcodegen && open KnobToken.xcodeproj`
3. Set your signing team on both targets (free Apple ID works for
   local development; CTK tokens need no restricted entitlement).
4. Run the app once (registers the extension), approve it in
   System Settings → Privacy & Security → Extensions → Smart Cards.

## Pair with your account

```sh
sc_auth identities                  # the knob token should be listed
sc_auth pair -u $USER -h <hash>     # or the System Settings pairing prompt
```

macOS will now show the card option at lock/login; `sudo` gains it via
the SmartCard PAM module (`/etc/pam.d/sudo`: ensure pam_smartcard.so).

## Open items

- Generate the self-signed cert at first launch (SecKeyCreateRandomKey
  + SecCertificate creation) — stubbed in TokenDriver.
- XPC wiring app<->extension (App Group `group.com.drivera.knobtoken`).
- Port of the ratchet resync rule is in AuthCrypto.swift; keep it
  byte-identical to the Python (tests/test_crypto.py is the authority).
