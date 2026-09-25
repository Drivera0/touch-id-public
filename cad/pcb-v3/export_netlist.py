"""
Render netlist_v3.py into formats that open outside Python:
    netlist_v3.csv   — one row per pin (ref, pin, net, part)
    netlist_v3_nets.csv — one row per net
    NETLIST-V3.md    — readable tables + the flags

Imports netlist_v3 rather than restating it, so the two cannot drift apart.
Run:  python export_netlist.py
"""
import csv
import os
from collections import defaultdict

import netlist_v3 as N

HERE = os.path.dirname(os.path.abspath(__file__))

nets = defaultdict(list)
for p in N.PARTS:
    for pin, net in p["pins"].items():
        if net != "NC":
            nets[net].append(f"{p['ref']}-{pin}")


def _key(p):
    r = p["ref"]
    head = r.rstrip("0123456789") or r
    tail = r[len(head):]
    return (head, int(tail) if tail.isdigit() else 0)


PARTS = sorted(N.PARTS, key=_key)

# ---------------------------------------------------------------- pins CSV --
with open(os.path.join(HERE, "netlist_v3.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ref", "pin", "net", "part", "note"])
    for p in PARTS:
        for pin in sorted(p["pins"]):
            w.writerow([p["ref"], pin, p["pins"][pin], p["name"], p["note"]])

# ---------------------------------------------------------------- nets CSV --
with open(os.path.join(HERE, "netlist_v3_nets.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["net", "connections", "pins"])
    for n in sorted(nets, key=lambda k: (-len(nets[k]), k)):
        w.writerow([n, len(nets[n]), " ".join(nets[n])])

# -------------------------------------------------------------------- md ----
L = []
A = L.append
A("---")
A("title: TouchID v3 netlist")
A("type: project")
A("tags:\n  - touchid\n  - pcb\n  - netlist")
A("updated: 2026-08-27")
A("---\n")
A("# TouchID v3 netlist\n")
A("**Generated from `netlist_v3.py` by `export_netlist.py` — do not hand-edit.**")
A("Edit the Python and re-run, or the two will disagree.\n")
nc = sum(1 for p in N.PARTS for v in p["pins"].values() if v == "NC")
A(f"{len(N.PARTS)} parts · {sum(len(p['pins']) for p in N.PARTS)} pins · "
  f"{nc} deliberate no-connects · {len(nets)} nets · no single-pin nets\n")

A("> [!warning] Structurally complete is not the same as settled")
A("> Every pin is accounted for and no net has fewer than two connections. The")
A("> six flags at the bottom are open **design** questions, not wiring errors.\n")

A("---\n\n## Nets\n")
A("| Net | # | Connections |")
A("|---|---|---|")
for n in sorted(nets, key=lambda k: (-len(nets[k]), k)):
    A(f"| `{n}` | {len(nets[n])} | {', '.join(nets[n])} |")

A("\n---\n\n## Parts, pin by pin\n")
for p in PARTS:
    A(f"### {p['ref']} — {p['name']}\n")
    if p["note"]:
        A(f"> {p['note']}\n")
    A("| Pin | Net |")
    A("|---|---|")
    for pin in sorted(p["pins"]):
        net = p["pins"][pin]
        A(f"| {pin} | {'*(no connect)*' if net == 'NC' else '`' + net + '`'} |")
    A("")

A("---\n\n## Flags — carried from `PART-LIBRARY.md` §9\n")
A("These print on every run of `netlist_v3.py`. They are not cosmetic.\n")
for where, txt in N.FLAGS:
    A(f"### {where}\n")
    A(f"{txt}\n")

with open(os.path.join(HERE, "NETLIST-V3.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")

print("wrote netlist_v3.csv, netlist_v3_nets.csv, NETLIST-V3.md")
print(f"  {len(N.PARTS)} parts, {sum(len(p['pins']) for p in N.PARTS)} pins, "
      f"{len(nets)} nets")
