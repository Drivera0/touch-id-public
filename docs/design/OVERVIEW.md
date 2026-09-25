---
title: README
type: meta
tags:
  - touchid
  - meta
---

# touchID — DIY Fingerprint Module for the NuPhy Air75 V3

> [!important] Read [[touchid/docs/design/DESIGN-SPEC|DESIGN-SPEC.md]] first
> It is the **master file** — every verified dimension, land pattern, housing
> number and design constraint, each traced to a vendor drawing or a geometric
> check. **If any other note in this folder disagrees with it, the other note is
> stale.** Outstanding work lives in
> [[touchid/cad/pcb-v2/OPEN-ISSUES|cad/pcb-v2/OPEN-ISSUES.md]].

> [!info] Where this fits
> This folder lives inside the parent `Projects/` Obsidian vault, alongside the Bluetooth Reminder App and MTG Project. Wikilinks here are folder-prefixed (`[[touchid/… |label]]`) so they resolve only within this folder, keeping the project isolated in the graph view.

## What this project is

A drop-in **fingerprint-authentication module** that replaces the swappable knob/keyswitch in the top-right corner slot of a **NuPhy Air75 V3**. Touch it and it types your Mac (or Windows) password — unlock, `sudo`, login — without paying $149 for Apple's Touch ID keyboard.

It's inspired by **[YubiKey](https://www.yubico.com/products/)** and by **[tinyTouch](https://github.com/ZimengXiong/tinyTouch)** by Zimeng Xiong (MIT licensed). tinyTouch is an ESP32-S3 + ZW101 fingerprint sensor that does an encrypted handshake with a small Mac helper app and types the stored password over USB HID.

> [!note] The core insight
> The Air75 V3 runs NuPhy's own closed firmware (no QMK, unlike the V2), so the keyboard's own chip can't be taught about a fingerprint sensor. The module is therefore an **independent sidecar**: it uses the corner slot as a mechanical mount (and hopefully a power source), but does all its own sensing, crypto, and talking to the computer. The keyboard never knows it exists. See [[touchid/docs/design/Architecture and Design|Architecture and Design]].

## Goals

- Working fingerprint-to-password on my own Air75 V3
- Learn embedded development, PCB design, and applied crypto from first principles, starting from a study of tinyTouch
- Eventually: a clean custom PCB that clicks into the slot like a factory part
- Possibly sell it (MIT license permits — see [[touchid/docs/design/Firmware and PCB|Firmware and PCB]])

## Status (as of 2026-08-18)

- [x] Confirmed inspiration repo, read code, confirmed MIT license
- [x] Pulled Air75 V3 internal photos from FCC filing; identified the corner daughterboard
- [x] Wrote a multimeter pin-test guide + interactive HTML logger (in the `Personal Project` working folder)
- [x] **Decided:** target architecture = **wireless, powered from the keyboard** (flush like the knob, no cable/port/hole) — contingent on the pin test
- [ ] **NEXT: run the pin test** to learn which slot pins carry power → see [[touchid/docs/bench/Pin Test Procedure|Pin Test Procedure]]
- [ ] Breadboard prototype with a XIAO ESP32-S3
- [ ] Custom PCB

## Current constraints + hardware decisions (2026-08-18)

- **Envelope:** module is ~**19 × 19 mm** square; everything fits *inside* (no overhang). Confirm by caliper measurement. → [[touchid/docs/design/Mechanical and Housing|Mechanical and Housing]]
- **Power/data:** target is **wireless, powered from the keyboard** (flush, no cable/hole) — contingent on the pin test finding a usable power pin. → [[touchid/docs/design/Architecture and Design|Architecture and Design]]
- **MCU:** ESP32-S3-MINI-1 is **too long (20.5 mm)**. Final wireless board uses **ESP32-C3-MINI-1 (13.2 × 16.6 mm)**; wired prototype uses a XIAO ESP32-S3 on breadboard. → [[touchid/docs/design/Firmware and PCB|Firmware and PCB]]
- **Sensor:** small (`≤`~16 mm body) FPC-ribbon sensor, prefer `0xEF01` family (ZW/GROW) to keep firmware. Shortlist in [[touchid/docs/design/Mechanical and Housing|Mechanical and Housing]].
- **PCB:** order fabbed **+ assembled (PCBA)** from JLCPCB/PCBWay — don't mill. → [[touchid/docs/design/Firmware and PCB|Firmware and PCB]]
- **Housing:** FDM **PETG + brass heat-set inserts** (screw-durable), or SLA tough resin for detail. Print at UBC (HATCH Form 2 / ECE farm) — access gated. → [[touchid/notes/UBC Facilities and Contacts|UBC Facilities and Contacts]]

## Notes in this folder

- [[touchid/docs/bench/Hardware Teardown|Hardware Teardown]] — what's inside the keyboard, the slot connectors (J4/J11), MCU, battery
- [[touchid/docs/bench/Pin Test Procedure|Pin Test Procedure]] — how to probe the 10 slot pins and record results
- [[touchid/docs/design/Architecture and Design|Architecture and Design]] — the sidecar model, power, data path, Mac/Windows, SSH
- [[touchid/docs/design/Firmware and PCB|Firmware and PCB]] — tinyTouch code review, improvements, chip choice, antenna, PCBA/assembly, atopile
- [[touchid/docs/design/Mechanical and Housing|Mechanical and Housing]] — 19 mm fit constraint, the stack, sensor shortlist, housing material + printing
- [[touchid/notes/UBC Facilities and Contacts|UBC Facilities and Contacts]] — scanner, printers, PCB, contacts, access rules
- [[touchid/notes/Roadmap|Roadmap]] — the phased build plan

> [!tip] Working files live elsewhere
> The hands-on artifacts (pin-test guide, `pin-test-results.csv`, `pin-test.html` logger, teardown guide) are in the **Personal Project** working folder, not in this vault. This vault is the knowledge base; that folder is the workbench.
