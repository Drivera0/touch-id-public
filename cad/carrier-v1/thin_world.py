"""
thin_world.py -- find thin material and report it in WORLD mm.

wall_check.py reports hits in trimesh's arbitrary per-section 2D frame, which
is fine for spotting a cluster and useless for finding it on the part.  This
voxelises instead: a Euclidean distance transform gives every solid voxel its
distance to the nearest surface, so 2 x EDT is the local thickness, and the
coordinates that come out are the part's own.

    python3 thin_world.py <stl> [threshold=1.5] [voxel=0.35]
    from thin_world import scan;  scan("flash_frame.stl", 2.0)   -> [] if clean
"""
import sys
import numpy as np
import trimesh
from scipy import ndimage


def scan(stl, thr=1.5, pitch=0.35, verbose=True):
    """Returns [] when nothing is thinner than thr, else one entry per region:
    (volume_mm3, (x0,y0,z0), (x1,y1,z1), thickest_point_mm)."""
    m = trimesh.load(stl)
    vg = m.voxelized(pitch=pitch).fill()
    occ = vg.matrix
    if verbose:
        print(f"== {stl}  thin < {thr} mm  (voxel {pitch} mm, grid {occ.shape}) ==")

    edt = ndimage.distance_transform_edt(occ, sampling=pitch)
    thick = edt >= thr / 2.0                 # spine of anything at least thr thick
    if not thick.any():
        if verbose:
            print("   the whole part is thinner than the threshold")
        return [(float(occ.sum()) * pitch**3, tuple(m.bounds[0]), tuple(m.bounds[1]), 0.0)]

    # every solid voxel within thr/2 of that spine belongs to a thick feature
    grow = ndimage.distance_transform_edt(~thick, sampling=pitch) <= thr / 2.0 + pitch
    thin = occ & ~grow
    n = int(thin.sum())
    if verbose:
        print(f"   thin voxels: {n}  ({n*pitch**3:.2f} mm3)")
    if n == 0:
        if verbose:
            print("   none found")
        return []

    out = []
    lab, k = ndimage.label(thin)
    sizes = ndimage.sum(thin, lab, range(1, k + 1))
    for idx in np.argsort(sizes)[::-1]:
        vol = sizes[idx] * pitch**3
        if vol < 0.05:                       # single stray voxels are mesh noise
            continue
        pts = np.argwhere(lab == idx + 1)
        w = vg.indices_to_points(pts)
        lo, hi = w.min(axis=0), w.max(axis=0)
        t = float(2 * edt[lab == idx + 1].max())
        out.append((float(vol), tuple(lo), tuple(hi), t))
        if verbose:
            print(f"   {vol:7.2f} mm3  x {lo[0]:7.2f}..{hi[0]:7.2f}  "
                  f"y {lo[1]:7.2f}..{hi[1]:7.2f}  z {lo[2]:6.2f}..{hi[2]:6.2f}   "
                  f"thickest point {t:.2f} mm")
    return out


if __name__ == "__main__":
    scan(sys.argv[1],
         float(sys.argv[2]) if len(sys.argv) > 2 else 1.5,
         float(sys.argv[3]) if len(sys.argv) > 3 else 0.35)
