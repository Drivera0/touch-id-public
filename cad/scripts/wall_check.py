"""
wall_check.py -- DFM wall-thickness + tier-junction audit for housing STLs.

Two checks, born from JLC3DP's 2026-09-01 DFM email:
1. THIN WALLS: slice the mesh along all three axes, erode each cross-section
   by threshold/2; whatever vanishes was thinner than the threshold. Reports
   feature locations. (Matches what Magics/VoxelDance flag as red.)
2. TIER JUNCTION CONTACT: the user diagnosed JLC's "0.13" tag correctly --
   it was the CONTACT WIDTH between the lower and upper tier walls at the
   z=2.90 step, invisible to per-slice thickness (each slice looks fine; the
   vertical load path between them was 0.135 mm). This check intersects the
   solid's XY footprint just below and just above every horizontal step and
   reports the minimum overlap width in the wall band.

Usage: python3 wall_check.py <stl> [thin_threshold=1.0] [junction_z=2.90]
Exit 0 = report only; findings are printed, judgment is the engineer's.
"""
import sys
import numpy as np
import trimesh
from shapely.ops import unary_union
from collections import Counter


def polys_at(m, z, normal=(0, 0, 1), origin=None):
    o = origin if origin is not None else [0, 0, z]
    s = m.section(plane_origin=o, plane_normal=list(normal))
    if s is None:
        return None
    p2, _ = s.to_2D()
    try:
        return unary_union(list(p2.polygons_full))
    except Exception:
        return None


def thin_scan(m, thr):
    print(f"-- thin-wall scan (<{thr:.2f} mm), 3 axes --")
    hits = Counter()
    for axis, normal in (('z', (0, 0, 1)), ('x', (1, 0, 0)), ('y', (0, 1, 0))):
        i = 'zxy'.index(axis)
        lo, hi = m.bounds[0][2 - i if axis == 'z' else i], m.bounds[1][2 - i if axis == 'z' else i]
        lo, hi = m.bounds[0]['xyz'.index(axis)], m.bounds[1]['xyz'.index(axis)]
        for c in np.arange(lo + 0.1, hi, 0.25):
            origin = [c if axis == 'x' else 0, c if axis == 'y' else 0,
                      c if axis == 'z' else 0]
            poly = polys_at(m, c, normal, origin)
            if poly is None or poly.is_empty:
                continue
            thin = poly.difference(poly.buffer(-thr / 2).buffer(thr / 2 + 0.01))
            if thin.area > 0.3:
                geoms = getattr(thin, 'geoms', [thin])
                for g in geoms:
                    if g.area > 0.3:
                        hits[(axis, round(g.centroid.x, 0), round(g.centroid.y, 0))] += 1
    if not hits:
        print("   none found")
    for (axis, u, v), n in hits.most_common(15):
        print(f"   {axis}-slices near section-uv ({u},{v}): {n} slices")
    return hits


def junction_scan(m, z, eps=0.03):
    print(f"-- tier-junction contact at z={z:.2f} --")
    below = polys_at(m, z - eps)
    above = polys_at(m, z + eps)
    if below is None or above is None:
        print("   no material at this z")
        return None
    contact = below.intersection(above)
    # width of the contact band: erode until it disappears
    width = 0.0
    for w in np.arange(0.05, 3.0, 0.05):
        if contact.buffer(-w / 2).is_empty:
            width = w
            break
    print(f"   contact area {contact.area:.1f} mm^2; MIN band width ~{width:.2f} mm")
    # where is it thinnest? erode to just before vanishing, report survivors
    core = contact.buffer(-(width - 0.10) / 2) if width > 0.15 else contact
    geoms = getattr(core, 'geoms', [core])
    kept = [(g.centroid.x, g.centroid.y, g.area) for g in geoms if not g.is_empty]
    for x, y, a in kept[:8]:
        print(f"   thick zone at ({x:6.2f},{y:6.2f}) a={a:.1f}")
    return width


if __name__ == '__main__':
    stl = sys.argv[1]
    thr = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    jz = float(sys.argv[3]) if len(sys.argv) > 3 else 2.90
    m = trimesh.load(stl)
    print(f"== {stl}  bounds {np.round(m.bounds,2).tolist()} ==")
    thin_scan(m, thr)
    junction_scan(m, jz)
