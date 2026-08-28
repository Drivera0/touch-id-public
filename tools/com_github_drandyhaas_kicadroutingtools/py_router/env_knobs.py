"""Read-once cache of the KICAD_* environment knobs.

The engine's experimental/diagnostic knobs were read with ``os.environ.get``
at their point of use -- some per net, per leg, or per congestion sample --
which both hammers the environ dict from hot paths and scatters the knob
inventory across a dozen modules. Every knob is read ONCE here, at import,
and stored as a plain module attribute; call sites read the attribute.

Semantics: a knob is its value at process start (first import). Harnesses that
pass knobs to CHILD processes via the environment are unaffected -- the child
re-reads at its own import (see memory: env vars must be EXPORTED for
subprocesses, an inline prefix misses children). Code that mutates
``os.environ`` mid-process and needs THIS process to see it calls
``refresh()`` afterwards.

Each attribute preserves the exact parse semantics its call site had (truthy
vs '1' vs default-on off-switch vs opt-in set) -- flipping one to a stricter
parse silently disables someone's recorded workflow. Argparse ``default=os.
environ.get(...)`` sites (route.py --ripup-* ) deliberately stay in place:
they are startup-once and self-document the override in --help.
"""
from __future__ import annotations

import os

_OFF = ('0', 'off', 'false')
_ON = ('1', 'true', 'on')


def _truthy(name: str) -> bool:
    return bool(os.environ.get(name))


def _on_default(name: str, default: str = '1') -> bool:
    return os.environ.get(name, default) not in _OFF


def _opt_in(name: str) -> bool:
    return os.environ.get(name, '') in _ON


def _f(name: str, dflt: float) -> float:
    try:
        return float(os.environ.get(name, str(dflt)) or dflt)
    except ValueError:
        return dflt


def _i(name: str, dflt: int) -> int:
    try:
        return int(os.environ.get(name, str(dflt)) or dflt)
    except ValueError:
        return dflt


def _s(name: str, dflt: str = '') -> str:
    return os.environ.get(name, dflt)


def refresh() -> None:
    """(Re)read every knob from os.environ (tests / in-process mutation)."""
    g = globals()

    # --- routing behavior switches (default ON, env turns OFF) -------------
    g['SEAM_REASK'] = _on_default('KICAD_SEAM_REASK', '')          # '' not in _OFF -> on
    g['ISLAND_LAUNCH'] = _on_default('KICAD_ISLAND_LAUNCH')
    g['MULTIPOINT_STUB_SWITCH'] = _on_default('KICAD_MULTIPOINT_STUB_SWITCH')
    g['HYBRID_COUPLE'] = _on_default('KICAD_HYBRID_COUPLE', '')
    g['BUS_MULTIPOINT_SPAN'] = _on_default('KICAD_BUS_MULTIPOINT_SPAN')
    g['BARE_BALL_ZONE_EXEMPT'] = _on_default('KICAD_BARE_BALL_ZONE_EXEMPT')
    g['DIRECT_FIRST'] = _on_default('KICAD_DIRECT_FIRST')
    g['IMPEDANCE_NECKDOWN'] = (_s('KICAD_IMPEDANCE_NECKDOWN', '1').strip().lower()
                               not in ('0', 'false', 'no', 'off'))
    g['NET_RESCUE'] = _s('KICAD_NET_RESCUE', '1') != '0'
    # Terminal geometry escalation ("better than shipping opens", 2026-08-05):
    # post-rescue whole-net retry with track width + via size marching down
    # together toward the fab floor. =0 disables for A/B debugging.
    g['TERMINAL_ESCALATION'] = _s('KICAD_TERMINAL_ESCALATION', '1') != '0'
    # PR #535's idea as a #189 escalation rung: when the in-pad unblock via
    # fails (or #581 forbids via-in-pad), search this radius (mm) around the
    # boxed pad for the first spot where a through-via is legal on every
    # layer and inject a pad->via escape stub (the plane-tap machinery does
    # the search + trace). =0 disables the off-pad rung.
    g['ESCAPE_STUB_RADIUS'] = _f('KICAD_ESCAPE_STUB_RADIUS', 1.0)
    # #529 dynamic iterations, DEFAULT ON (=0 reverts to static caps): full
    # searches run at min(base, CLAMP) and earn +1x base tranches while the
    # heuristic keeps approaching, up to a flat 1e7 ceiling. CLAMP defaults
    # to 1e7 = no clamping (corpus: -29 incomplete nets over 150 boards);
    # set CLAMP=200000 as the deliberate speed-over-completion dial.
    g['DYNAMIC_ITERATIONS'] = _s('KICAD_DYNAMIC_ITERATIONS', '1') != '0'
    g['DYNAMIC_ITERATIONS_CLAMP'] = _i('KICAD_DYNAMIC_ITERATIONS_CLAMP', 10_000_000)

    # --- opt-in experiments (env turns ON) ----------------------------------
    g['COLLINEAR_VIAS'] = _opt_in('KICAD_COLLINEAR_VIAS')  # #487: on-axis vias
    # Proximity composition: SUM across sources (per-net / per-category,
    # deduped max WITHIN each source) instead of a flat per-cell max. Adds a
    # density gradient (10 stubs price higher than 1) at the cost of steeper
    # fields in dense escape regions. Values: '1'/'sum' = sum everywhere;
    # 'zoned' = sum in open field, MAX inside BGA escape fields (zone +
    # bga_proximity_radius) -- the sum win comes from open-field density,
    # while inside the escape collar the stacked foreign-stub fields price a
    # net's MANDATORY approach (lpddr4 A/B: deficit 1->2, 6x search).
    # 'softcap' (#584) = the global blend max + ALPHA*(sum - max) per cell,
    # everywhere: keeps the max-mode floor plus a fraction of the crowd
    # pressure, so density still repels but stacked fields near mandatory
    # approaches can't explode. ALPHA=0 reproduces max, ALPHA=1 reproduces
    # sum (both exactly, up to integer-cost rounding).
    # Off = historical max semantics everywhere.
    # Default = historical MAX. Briefly 'zoned' (s2 rescan -30 on the curated
    # set) -- REVERTED with MAX_RIPUP=5: the sets-11-15 holdout showed the two
    # together erasing the other flips' gains on ordinary boards (v4 -2% vs
    # lean -45% vs old defaults) at +37% CPU. zoned/sum/softcap remain opt-in
    # (retry-tier on knob-sensitive boards).
    _ps = _s('KICAD_PROXIMITY_SUM', '').strip().lower()
    g['PROXIMITY_SUM_MODE'] = ('zoned' if _ps == 'zoned'
                               else 'softcap' if _ps == 'softcap'
                               else 'sum' if _ps in _ON else '')
    g['PROXIMITY_SUM'] = bool(g['PROXIMITY_SUM_MODE'])
    g['PROXIMITY_SOFTCAP_ALPHA'] = _f('KICAD_PROXIMITY_SOFTCAP_ALPHA', 0.3)
    # #585 item 1: layer-aware stub proximity. The stub's OWN layer keeps the
    # full cost; other layers pay cost/M (M = n_layers/2 by default, so a
    # 2-layer board is unchanged and a 6-layer board discounts 3x) -- a via
    # escape near the stub still needs track room on other layers, just less
    # of it. KICAD_STUB_LAYER_M overrides M (>= 1).
    # #585 item 8's two pseudo-stub gates, split so each can be A/B'd alone.
    # Both ON = f785a7e's shipped behaviour, restored. They were briefly
    # defaulted OFF on a two-board 2x2 whose spread turned out comparable to its
    # own noise; two corpus A/Bs then measured ON BETTER (by 3 on 148 boards, by
    # 2 on 129 with smoothing restored -- 7 boards better vs 4 worse). Setting
    # =0 gives the pre-f785a7e behaviour: any footprint with >= min_pads pads
    # emits, and the proxy never retires. Kept as separate knobs because the two
    # gates are wildly asymmetric -- on spartan6's final board the retire gate
    # removes 95%% of emitters (667 -> 33 pads), the package gate 33%%.
    g['FINE_PITCH_PSEUDO_STUBS'] = _on_default('KICAD_FINE_PITCH_PSEUDO_STUBS')
    g['PSEUDO_STUB_RETIRE'] = _on_default('KICAD_PSEUDO_STUB_RETIRE')
    g['STUB_LAYER_AWARE'] = _opt_in('KICAD_STUB_LAYER_AWARE')
    g['STUB_LAYER_M'] = _f('KICAD_STUB_LAYER_M', 0.0)  # 0 = auto n_layers/2
    # (#585 item 2 -- excluding plane-destined nets' stubs -- was DECIDED
    # AS-IS, no knob: a pour needs reserved access space exactly like tracks.)
    # #585 item 4: per-package proximity fields (BGA/QFN/QFP, radius scaled
    # sqrt(n_pads/1000) x bga_proximity_radius clamped [2, cap]). Screened
    # NEGATIVE as a default (glasgow 7->10, oc midchain 23->26 -- the sqrt
    # scaling SHRINKS large-BGA rings, and tiny DFN/SOT packages classified
    # QFN add clutter); opt-in pending a scale-up-only / pad-floor variant.
    g['PACKAGE_PROXIMITY'] = _opt_in('KICAD_PACKAGE_PROXIMITY')
    # #585 item 3a: pre-existing (input-board) copper of rippable registered
    # nets emits track-proximity ghosts like copper routed this run (only
    # matters when track_proximity_cost > 0).
    g['TRACK_PROX_PREEXISTING'] = _opt_in('KICAD_TRACK_PROX_PREEXISTING')
    # per-tranche quantum = max(CELLS grid cells, PCT% of tranche-start best_h)
    g['DYNAMIC_ITERATIONS_QUANTUM_CELLS'] = _f('KICAD_DYNAMIC_ITERATIONS_QUANTUM_CELLS', 2.0)
    g['DYNAMIC_ITERATIONS_QUANTUM_PCT'] = _f('KICAD_DYNAMIC_ITERATIONS_QUANTUM_PCT', 2.0)
    # plateau grace: consecutive quantum-failing tranches tolerated before
    # denial (progress judged cumulatively over the plateau; emulates a wider
    # window without a bigger base)
    g['DYNAMIC_ITERATIONS_GRACE'] = _i('KICAD_DYNAMIC_ITERATIONS_GRACE', 0)
    g['MULTIPOINT_DENSE_FIRST'] = _opt_in('KICAD_MULTIPOINT_DENSE_FIRST')
    g['FANOUT_DIRECT'] = _opt_in('KICAD_FANOUT_DIRECT')
    g['FANOUT_TOWARD_TARGETS'] = _opt_in('KICAD_FANOUT_TOWARD_TARGETS')
    # '' = follow the --plane-drop param (default auto); '0'/'off' forces the
    # plane-ball drop pass OFF, '1'/'auto' forces it ON -- the manifest-replay
    # A/B switch for #424 D2 (recorded chains carry no flag either way).
    g['FANOUT_PLANE_DROP'] = _s('KICAD_FANOUT_PLANE_DROP', '')
    # '0' reverts the surface-pour direct connect (plane-drop balls whose own-
    # layer same-net pour provably fills to the pad get NO via). Default ON.
    g['FANOUT_POUR_DIRECT'] = _s('KICAD_FANOUT_POUR_DIRECT', '1') != '0'
    g['STOP_CLEANUP'] = _opt_in('KICAD_STOP_CLEANUP')
    g['TAP_RELOCATION'] = _opt_in('KICAD_TAP_RELOCATION')  # phase-3 tap pocket moves
    # #536 octolinear route smoothing (cleanup_pipeline pass 9b): collapse
    # staircase micro-jogs into diagonal+axis shortcuts, DRC-checked, output
    # strictly octolinear. Tri-state like KICAD_FANOUT_PLANE_DROP: '' (unset,
    # default) = follow the FRONT's default -- ON for the single-ended route
    # step, OFF for diff pairs and the plane file-round-trip; '1' forces on,
    # '0' forces off. Protected copper (diff pairs, length/time-matched,
    # impedance-declared, locked) is never touched regardless. Pour cuts the
    # shortcut may inflict are the plane finalize / kicad-oracle recheck's
    # job, which runs after cleanup on both fronts.
    g['SMOOTH_ROUTE'] = _s('KICAD_SMOOTH_ROUTE', '')
    # #600 improvement gate: refuse to ship a board this run made WORSE (more
    # previously-connected nets broken than newly connected). '0' disables --
    # for A/B, and for the rare case where an operator genuinely wants the
    # regressed board on disk to inspect it.
    g['IMPROVEMENT_GATE'] = _s('KICAD_IMPROVEMENT_GATE', '1') != '0'
    g['PLANE_PARTIAL_RESTORE'] = _s('KICAD_PLANE_PARTIAL_RESTORE') == '1'
    g['DUMP_BATCH_KWARGS_CONTINUE'] = _s('KICAD_DUMP_BATCH_KWARGS_CONTINUE') == '1'

    # --- truthy diagnostics / overrides -------------------------------------
    g['UNBLOCK_DEBUG'] = _truthy('KICAD_UNBLOCK_DEBUG')
    g['TAP_CROSS_SCAN'] = _truthy('KICAD_TAP_CROSS_SCAN')
    g['OBSTACLE_AUDIT'] = _truthy('KICAD_OBSTACLE_AUDIT')
    g['PLANE_MAP_PARITY'] = _truthy('KICAD_PLANE_MAP_PARITY')
    g['SETTLE_DEBUG'] = _truthy('KICAD_SETTLE_DEBUG')
    g['LEGACY_GATE_ORACLE'] = _truthy('KICAD_LEGACY_GATE_ORACLE')
    g['NO_GATE_ORACLE'] = _truthy('KICAD_NO_GATE_ORACLE')
    g['GATE_DEBUG'] = _truthy('KICAD_GATE_DEBUG')
    g['NO_SWEEP_PLATED'] = _truthy('KICAD_NO_SWEEP_PLATED')
    g['NO_SOFT_JOINT_BRIDGE'] = _truthy('KICAD_NO_SOFT_JOINT_BRIDGE')
    g['BOARD_LEDGER'] = _truthy('KICAD_BOARD_LEDGER')
    # "x,y" via position string ('' = off; consumers test truthiness + parse)
    g['RESCUE_DEBUG_VIA'] = _s('KICAD_RESCUE_DEBUG_VIA')
    g['MEM_PROBE'] = _truthy('KICAD_MEM_PROBE')
    g['NO_STATIC_BASE'] = _truthy('KICAD_NO_STATIC_BASE')
    g['ALLOW_STAGGERED_BGA'] = _truthy('KICAD_ALLOW_STAGGERED_BGA')
    g['QFN_UNDERPAD_NO_ALT_STAGGER'] = _truthy('QFN_UNDERPAD_NO_ALT_STAGGER')
    g['LEGACY_ORACLE'] = _truthy('KICAD_LEGACY_ORACLE')
    g['NO_EXACT_FILL'] = _truthy('KICAD_NO_EXACT_FILL')
    g['NO_FILL_NETCLASS'] = _truthy('KICAD_NO_FILL_NETCLASS')  # fill-model A/B

    # --- numeric knobs -------------------------------------------------------
    # Rasterization memo budget (MB, shared convention across the capsule/
    # polygon caches in routing_utils/obstacle_map). Profiling: 64MB cycled
    # ~40x on orangecrab (69% hit rate where ~99% is available). Parallel
    # stress workers multiply per-process caches -- export a smaller value
    # there.
    g['RASTER_CACHE_MB'] = _f('KICAD_RASTER_CACHE_MB', 256.0)
    g['BUS_XLAYER_PCT'] = _i('KICAD_BUS_XLAYER_PCT', 35)
    g['BUS_OFFLANE_MULT'] = _f('KICAD_BUS_OFFLANE_MULT', 1.0)   # off-lane surcharge (1.0 = off)
    g['BUS_CORRIDOR_PROBE_VIA_MULT'] = _f('KICAD_BUS_CORRIDOR_PROBE_VIA_MULT', 20.0)
    g['BUS_MAX_CORRIDOR_LAYER_CHANGES'] = _i('KICAD_BUS_MAX_CORRIDOR_LAYER_CHANGES', 1)
    g['TAP_RELOCATION_MAX'] = _i('KICAD_TAP_RELOCATION_MAX', 2)
    g['SEAM_SE_RATIO'] = _f('KICAD_SEAM_SE_RATIO', 1.3)
    g['SEAM_SE_MAX'] = _i('KICAD_SEAM_SE_MAX', 16)
    g['HYBRID_COUPLE_RADIUS'] = _f('KICAD_HYBRID_COUPLE_RADIUS', 1.0)
    g['BUS_RIP_RESISTANCE'] = _s('KICAD_BUS_RIP_RESISTANCE', '')  # float-or-empty; consumer parses
    g['CONGESTION_COST'] = _f('KICAD_CONGESTION_COST', 0.0)
    g['CONGESTION_BIN'] = _f('KICAD_CONGESTION_BIN', 1.0)
    g['CONGESTION_THRESHOLD'] = _f('KICAD_CONGESTION_THRESHOLD', 0.30)
    g['CONGESTION2'] = {
        'cost': _f('KICAD_CONGESTION2_COST', 0.0),
        'thresh': _f('KICAD_CONGESTION2_THRESHOLD', 0.5),
        'bin': _f('KICAD_CONGESTION2_BIN', 1.0),
        'exempt_r': _f('KICAD_CONGESTION2_EXEMPT_R', 1.0),
        'ramp_top': _f('KICAD_CONGESTION2_RAMP_TOP', 2.0),
    }
    # History-based negotiated congestion (#590, PathFinder): permanent
    # per-cell bump at each conflict event. See history_congestion.py.
    # v2 (contest-targeted): the primary event charges the frontier∩blocker
    # INTERSECTION (the cells one net holds and another stalled against) at
    # the full increment; the v1 whole-footprint rip stamp and raw-frontier
    # charge were measured negative/inert and now default OFF behind weights.
    # #590 SHIPPED DEFAULT = the "v1flat_01" arm: the flat diffuse field at dose
    # 0.1 / cap 0.5, whole-footprint rip stamps at full weight, raw frontier at
    # 0.25, and NO escalation. Best of every arm tested on three corpora; see
    # the promotion note in history_congestion.py for the evidence AND for the
    # caveat (the win is concentrated on congested boards; a pre-registered
    # sets 21-27 test did not clear its own bar). KICAD_HISTORY_COST=0 restores
    # the pre-promotion OFF state for A/B.
    g['HISTORY'] = {
        'cost': _f('KICAD_HISTORY_COST', 0.1),            # 0 = disabled
        'cap': _f('KICAD_HISTORY_CAP', 0.5),              # 0 = uncapped
        'radius': _f('KICAD_HISTORY_RADIUS', 0.25),       # mm beyond half-width (rip stamp)
        'blocked_weight': _f('KICAD_HISTORY_BLOCKED_WEIGHT', 0.25),  # raw frontier residue
        'rip_weight': _f('KICAD_HISTORY_RIP_WEIGHT', 1.0),  # v1 whole-footprint rip stamp
        'escalate': _f('KICAD_HISTORY_ESCALATE', 0.0),   # repeat-contest multiplier (0 = flat)
        'max_cells': _i('KICAD_HISTORY_MAX_CELLS', 500_000),
    }

    # --- strings -------------------------------------------------------------
    g['HYBRID_LEG_DEBUG'] = _s('KICAD_HYBRID_LEG_DEBUG')   # truthy; '2' = verbose
    g['LEDGER_TRACE'] = _s('KICAD_LEDGER_TRACE')
    g['STOP_AFTER'] = _s('KICAD_STOP_AFTER')
    g['STOP_FILE'] = _s('KICAD_STOP_FILE')
    g['DUMP_BATCH_KWARGS'] = _s('KICAD_DUMP_BATCH_KWARGS')  # dump file path
    # raw override for underpad outer-ring count ('' = keep the caller's
    # default, which differs by escape method; consumer parses float/inf)
    g['UNDERPAD_OUTER_RINGS'] = _s('KICAD_UNDERPAD_OUTER_RINGS')


refresh()
