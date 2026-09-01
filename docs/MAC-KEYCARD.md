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
 ├─ KnobTransport.swift  the seam: requestTouch/provision/enroll
 ├─ DongleClient.swift   USB HID to the dongle (vendor page 0xFF00);
 │                       docs/DONGLE-HOST-PROTOCOL.md
 ├─ AuthCrypto.swift     HMAC verify + one-step ratchet (port of
 │                       knobauth/crypto.py, same test vectors)
 └─ TokenExtension (CTK persistent token, extension point
    com.apple.ctk-tokens)
     └─ exposes 1 ECDSA P-256 key + self-signed cert; every sign
        request → CFMessagePort to the app → knob touch proof → sign
```

Transport: knob →(2.4 GHz ESB)→ dongle →(USB HID)→ Mac. The dongle
relays the knob's proof verbatim, so the Mac verifies the HMAC itself
and the ratchet still runs knob↔Mac. The earlier BLE-direct client is
kept in `software/mac-helper/archive/ble-direct/` — it works against
the knob's *current* firmware, which is still a BLE peripheral.

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
4. Run the app once (registers the extension), then enable it. The
   Smart Cards pane may not exist on macOS 26+; this always works:
   `pluginkit -e use -i com.drivera.KnobToken.TokenExtension`

## Pair with your account

```sh
sc_auth identities                  # the knob token should be listed
sc_auth pair -u $USER -h <hash>     # or the System Settings pairing prompt
```

If `sc_auth pair` fails with CryptoTokenKit **-8 (badParameter)**, the
token's key is being rejected as *unsuitable*, not the pairing: macOS
smart-card login does not merely sign — it wraps a secret to the card
and unwraps it via **ECDH at login**. A signature-only key cannot pair.
The token must therefore:

- support `.performKeyExchange` with `ecdhKeyExchangeStandard`
  (`TokenDriver.swift`),
- set `canPerformKeyExchange` on its `TKTokenKeychainKey`, and
- carry **keyAgreement** in the certificate's keyUsage, not just
  digitalSignature (`CertBuilder.swift`).

With those three, pairing succeeds and `sc_auth identities` reports
"Paired identities which are used for authentication".

Pairing lives in the user's **AuthenticationAuthority** (`;tokenidentity;<HASH>`,
legacy `;pubkeyhash;<HASH>`) — *not* AltSecurityIdentities. `sc_auth` is a
shell script; read it for the truth.

## VERIFIED WORKING (2026-08-31, simulated knob)

With a `SimulatedTransport` standing in for the hardware, on this Mac:

- `sudo id -u` → `0`, authenticated **by the card**, account password
  never entered.
- The signature returned through CryptoTokenKit verifies against the
  card's own certificate, and a tampered message is rejected.
- **The gate is load-bearing:** with the simulator off and no hardware
  present, the identical `sudo` attempt fails. No proof, no root.

So the whole Mac lane is proven end to end except the radio and the
finger. Run it yourself with:
`open --env KNOBTOKEN_SIMULATE=1 ~/Applications/KnobToken.app`
(debug builds only; the simulator approves every touch, which is why it
is compiled out of release and gated on that variable).

## macOS 26+ gotchas (all hit in practice, 2026-08-31)

- **NSExtensionAttributes schema changed.** Use flat keys
  `com.apple.ctk.class-id` and `com.apple.ctk.driver-class` (see the
  system PlatformSSOToken/pivtoken appexes). The old documented
  `com.apple.ctk-token-driver`/`ClassID` dict yields a nil class-id,
  and the per-user ctkd **crash-loops** (`abort`, "key cannot be nil")
  — which in turn makes `TKTokenDriver.Configuration` calls and
  `sc_auth` hang forever. Never call those on the main thread.
- **Do not set NSExtensionPrincipalClass.** ExtensionFoundation then
  instantiates the driver via the generic NSExtensionRequestHandling
  path, rejects it ("does not conform"), and the token never comes up
  (SecItem returns errSecInternal -26276). CTK's TKTokenService finds
  the driver by `com.apple.ctk.driver-class` alone.
- The extension needs no Settings toggle:
  `pluginkit -e use -i com.drivera.KnobToken.TokenExtension`.

macOS will now show the card option at lock/login; `sudo` gains it via
the SmartCard PAM module (`/etc/pam.d/sudo`: ensure pam_smartcard.so).

## App <-> extension bridge (what "XPC" became)

A plain app can't host an NSXPC mach service (that needs a launchd
agent), so the bridge is a **CFMessagePort** named
`group.com.drivera.knobtoken.sign`: the app registers it dynamically,
and the sandboxed extension may look it up because the sandbox permits
mach-lookup of names prefixed by an app group the process holds. Wire
format in `Sources/Shared/KnobIPC.swift`. The extension's sign request
blocks (45 s cap) while the app arms a challenge and waits for the
verified touch.

## First-run checklist (after build + extension approval)

1. Menu bar → **Provision key** (writes K to the knob, stores it in
   the Keychain — the Mac twin of `knobauth provision`).
2. Menu bar → **Enroll finger** → pick a slot; touch, lift, touch.
3. Menu bar → **Set up smart card** (creates the P-256 key +
   self-signed cert, registers the persistent token).
4. **Test touch** to confirm the whole proof path, then pair (below).

## Open items

- Custom TKTokenAuthOperation so the PIN sheet reads "touch the knob"
  instead of accepting any PIN (the touch is still the real gate).
- Port of the ratchet resync rule is in AuthCrypto.swift; keep it
  byte-identical to the Python (tests/test_crypto.py is the authority).
- vault/ssh-confirm parity with the Windows helper.
