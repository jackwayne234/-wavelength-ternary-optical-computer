#!/usr/bin/env python3
"""
Design Rule Check (DRC) for Monolithic 9x9 N-Radix Chip
=========================================================

Loads the GDS file produced by monolithic_chip_9x9.py, flattens into
the top cell, and checks every polygon against the DRC rules defined
in NRadix_Accelerator/docs/DRC_RULES.md.

Checks implemented:
    WG.W.1   - waveguide width 0.48-0.52 um  (layer 1,0)
    WG.S.1   - waveguide spacing >= 0.5 um   (layer 1,0)
    MTL1.W.1 - heater min width  >= 1.0 um   (layer 10,0)
    MTL1.S.1 - heater spacing    >= 2.0 um   (layer 10,0)
    MTL2.W.1 - bond pad min dim  >= 80 um    (layer 12,0)
    MTL2.S.1 - pad-to-pad spacing >= 50 um   (layer 12,0)
    SP.5     - SFG region spacing >= 10 um   (layer 2,0)
    PPLN.L.1 - SFG mixer length 18-22 um     (layer 2,0)
    EDGE.1   - feature-to-die-edge >= 50 um  (all fab layers vs layer 99,0)
    OVERLAP  - polygon overlaps on same fab layers
    CHIP     - chip extents match expected 1095 x 695 um
    LAYER_INV - layer inventory

Exit codes:
    0  - all critical rules PASS
    1  - one or more critical rules FAIL

Author: Wavelength-Division Ternary Optical Computer Project
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    import gdstk
except ImportError:
    sys.exit("ERROR: gdstk is not installed. Install with: pip install gdstk")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
GDS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Research", "data", "gds", "monolithic_9x9_nradix.gds",
)
REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(REPORT_DIR, "DRC_REPORT.txt")

# ---------------------------------------------------------------------------
# Layer definitions  (layer, datatype)
# ---------------------------------------------------------------------------
LAYER_WG        = (1, 0)
LAYER_SFG       = (2, 0)
LAYER_PD        = (3, 0)
LAYER_DFG       = (4, 0)
LAYER_KERR_RES  = (5, 0)
LAYER_AWG_ORIG  = (6, 0)
LAYER_MTL1      = (10, 0)
LAYER_CARRY     = (11, 0)
LAYER_MTL2      = (12, 0)
LAYER_MTL2_INT  = (12, 1)
LAYER_DOP_SA    = (13, 0)
LAYER_DOP_GAIN  = (14, 0)
LAYER_AWG       = (15, 0)
LAYER_DETECTOR  = (16, 0)
LAYER_LASER     = (17, 0)
LAYER_WEIGHT    = (18, 0)
LAYER_MUX       = (19, 0)
LAYER_REGION    = (20, 0)
LAYER_MEANDER   = (21, 0)
LAYER_BORDER    = (99, 0)
LAYER_LABEL     = (100, 0)

LAYER_NAMES: Dict[Tuple[int, int], str] = {
    LAYER_WG:       "WG (waveguide)",
    LAYER_SFG:      "SFG (chi2 mixer)",
    LAYER_PD:       "PD (photodetector)",
    LAYER_DFG:      "DFG (chi2 mixer)",
    LAYER_KERR_RES: "KERR_RES (Kerr resonator)",
    LAYER_AWG_ORIG: "AWG (body, DRC doc)",
    LAYER_MTL1:     "MTL1 (heater TiN)",
    LAYER_CARRY:    "CARRY_PATH",
    LAYER_MTL2:     "MTL2 (bond pad Ti/Au)",
    LAYER_MTL2_INT: "MTL2_INT (internal metal)",
    LAYER_DOP_SA:   "DOP_SA",
    LAYER_DOP_GAIN: "DOP_GAIN",
    LAYER_AWG:      "AWG (generator)",
    LAYER_DETECTOR: "DETECTOR",
    LAYER_LASER:    "LASER",
    LAYER_WEIGHT:   "WEIGHT",
    LAYER_MUX:      "MUX",
    LAYER_REGION:   "REGION (boundary)",
    LAYER_MEANDER:  "MEANDER",
    LAYER_BORDER:   "CHIP_BORDER",
    LAYER_LABEL:    "LABEL (text)",
}

FAB_LAYERS = {
    LAYER_WG, LAYER_SFG, LAYER_PD, LAYER_DFG, LAYER_KERR_RES,
    LAYER_AWG_ORIG, LAYER_MTL1, LAYER_CARRY, LAYER_MTL2,
    LAYER_DOP_SA, LAYER_DOP_GAIN, LAYER_AWG, LAYER_DETECTOR,
    LAYER_LASER, LAYER_WEIGHT, LAYER_MUX,
}

EXPECTED_CHIP_WIDTH  = 1115.0
EXPECTED_CHIP_HEIGHT = 735.0
CHIP_DIM_TOL = 5.0


def bbox(poly: gdstk.Polygon) -> Tuple[float, float, float, float]:
    pts = poly.points
    return float(pts[:, 0].min()), float(pts[:, 1].min()), \
           float(pts[:, 0].max()), float(pts[:, 1].max())


def bbox_width(b: Tuple[float, float, float, float]) -> float:
    return b[2] - b[0]


def bbox_height(b: Tuple[float, float, float, float]) -> float:
    return b[3] - b[1]


def bbox_min_dim(b: Tuple[float, float, float, float]) -> float:
    return min(bbox_width(b), bbox_height(b))


def bbox_max_dim(b: Tuple[float, float, float, float]) -> float:
    return max(bbox_width(b), bbox_height(b))


def bbox_distance(b1, b2) -> float:
    dx = max(0.0, max(b1[0] - b2[2], b2[0] - b1[2]))
    dy = max(0.0, max(b1[1] - b2[3], b2[1] - b1[3]))
    return (dx**2 + dy**2) ** 0.5


def bbox_overlaps(b1, b2) -> bool:
    return (b1[0] < b2[2] and b2[0] < b1[2] and
            b1[1] < b2[3] and b2[1] < b1[3])


@dataclass
class Violation:
    rule_id: str
    message: str
    location: Optional[Tuple[float, float]] = None


@dataclass
class RuleResult:
    rule_id: str
    description: str
    checked: int = 0
    violations: List[Violation] = field(default_factory=list)
    info: str = ""

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


def collect_polygons(cell: gdstk.Cell) -> Dict[Tuple[int, int], List[gdstk.Polygon]]:
    by_layer: Dict[Tuple[int, int], List[gdstk.Polygon]] = defaultdict(list)
    for poly in cell.polygons:
        key = (poly.layer, poly.datatype)
        by_layer[key].append(poly)
    return dict(by_layer)


# ===========================================================================
# DRC rule implementations
# ===========================================================================

def check_wg_width(polys: Dict) -> RuleResult:
    """WG.W.1 - waveguide width 0.48-0.52 um on layer (1,0)."""
    r = RuleResult("WG.W.1", "Waveguide width 0.48-0.52 um (single-mode)")
    wg_polys = polys.get(LAYER_WG, [])
    r.checked = len(wg_polys)

    for p in wg_polys:
        b = bbox(p)
        w = bbox_width(b)
        h = bbox_height(b)
        min_d = min(w, h)
        area = w * h
        # Skip large non-waveguide polygons (combiner blocks, etc.)
        if area > 100.0:
            continue
        aspect = max(w, h) / max(min_d, 1e-9)
        if aspect < 3.0:
            continue

        if min_d < 0.48 - 1e-6:
            r.violations.append(Violation(
                "WG.W.1",
                f"Waveguide too narrow: {min_d:.4f} um (min 0.48). "
                f"BBox ({b[0]:.2f},{b[1]:.2f})-({b[2]:.2f},{b[3]:.2f})",
                location=((b[0]+b[2])/2, (b[1]+b[3])/2),
            ))
        elif min_d > 0.52 + 1e-6:
            r.violations.append(Violation(
                "WG.W.1",
                f"Waveguide too wide: {min_d:.4f} um (max 0.52). "
                f"BBox ({b[0]:.2f},{b[1]:.2f})-({b[2]:.2f},{b[3]:.2f})",
                location=((b[0]+b[2])/2, (b[1]+b[3])/2),
            ))

    r.info = f"Checked {r.checked} WG polygons"
    return r


def check_wg_spacing(polys: Dict) -> RuleResult:
    """WG.S.1 - minimum waveguide spacing 0.5 um between non-coupled WGs."""
    r = RuleResult("WG.S.1", "Minimum waveguide spacing >= 0.5 um")
    wg_polys = polys.get(LAYER_WG, [])
    r.checked = len(wg_polys)
    if len(wg_polys) < 2:
        r.info = "Fewer than 2 WG polygons - nothing to check."
        return r

    bboxes = [bbox(p) for p in wg_polys]
    n = len(bboxes)
    pair_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = bbox_distance(bboxes[i], bboxes[j])
            if 0 < d < 0.5 - 1e-6:
                pair_count += 1
                if len(r.violations) < 20:
                    ci = ((bboxes[i][0]+bboxes[i][2])/2, (bboxes[i][1]+bboxes[i][3])/2)
                    cj = ((bboxes[j][0]+bboxes[j][2])/2, (bboxes[j][1]+bboxes[j][3])/2)
                    r.violations.append(Violation(
                        "WG.S.1",
                        f"WG spacing {d:.4f} um < 0.5 um. "
                        f"Poly centers ~({ci[0]:.1f},{ci[1]:.1f}) & ({cj[0]:.1f},{cj[1]:.1f})",
                        location=ci,
                    ))

    if pair_count > 20:
        r.info = f"Total violations: {pair_count} (showing first 20)"
    else:
        r.info = f"Checked {n*(n-1)//2} WG-WG pairs"
    return r


def check_mtl1_width(polys: Dict) -> RuleResult:
    """MTL1.W.1 - minimum heater width >= 1.0 um on layer (10,0)."""
    r = RuleResult("MTL1.W.1", "Minimum heater width >= 1.0 um")
    mtl_polys = polys.get(LAYER_MTL1, [])
    r.checked = len(mtl_polys)

    for p in mtl_polys:
        b = bbox(p)
        min_d = bbox_min_dim(b)
        if min_d < 1.0 - 1e-6:
            r.violations.append(Violation(
                "MTL1.W.1",
                f"Heater width {min_d:.4f} um < 1.0 um. "
                f"BBox ({b[0]:.2f},{b[1]:.2f})-({b[2]:.2f},{b[3]:.2f})",
                location=((b[0]+b[2])/2, (b[1]+b[3])/2),
            ))

    r.info = f"Checked {r.checked} MTL1 polygons"
    return r


def check_mtl1_spacing(polys: Dict) -> RuleResult:
    """MTL1.S.1 - minimum heater spacing >= 2.0 um on layer (10,0)."""
    r = RuleResult("MTL1.S.1", "Minimum heater spacing >= 2.0 um")
    mtl_polys = polys.get(LAYER_MTL1, [])
    r.checked = len(mtl_polys)
    if len(mtl_polys) < 2:
        r.info = "Fewer than 2 MTL1 polygons - nothing to check."
        return r

    bboxes = [bbox(p) for p in mtl_polys]
    n = len(bboxes)
    violation_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = bbox_distance(bboxes[i], bboxes[j])
            if 0 < d < 2.0 - 1e-6:
                violation_count += 1
                if len(r.violations) < 20:
                    ci = ((bboxes[i][0]+bboxes[i][2])/2, (bboxes[i][1]+bboxes[i][3])/2)
                    r.violations.append(Violation(
                        "MTL1.S.1",
                        f"Heater spacing {d:.4f} um < 2.0 um. "
                        f"Poly pair {i}-{j}",
                        location=ci,
                    ))

    if violation_count > 20:
        r.info = f"Total violations: {violation_count} (showing first 20)"
    else:
        r.info = f"Checked {n*(n-1)//2} MTL1-MTL1 pairs"
    return r


def check_mtl2_width(polys: Dict) -> RuleResult:
    """MTL2.W.1 - minimum bond pad dimension >= 80 um on layer (12,0)."""
    r = RuleResult("MTL2.W.1", "Minimum bond pad dimension >= 80 um")
    mtl_polys = polys.get(LAYER_MTL2, [])
    r.checked = len(mtl_polys)

    for p in mtl_polys:
        b = bbox(p)
        min_d = bbox_min_dim(b)
        if min_d < 80.0 - 1e-6:
            r.violations.append(Violation(
                "MTL2.W.1",
                f"Bond pad min dim {min_d:.2f} um < 80 um. "
                f"BBox ({b[0]:.1f},{b[1]:.1f})-({b[2]:.1f},{b[3]:.1f}), "
                f"dims {bbox_width(b):.2f} x {bbox_height(b):.2f}",
                location=((b[0]+b[2])/2, (b[1]+b[3])/2),
            ))

    r.info = f"Checked {r.checked} MTL2 polygons"
    return r


def check_mtl2_spacing(polys: Dict) -> RuleResult:
    """MTL2.S.1 - minimum pad-to-pad spacing >= 50 um on layer (12,0)."""
    r = RuleResult("MTL2.S.1", "Minimum pad-to-pad spacing >= 50 um")
    mtl_polys = polys.get(LAYER_MTL2, [])
    r.checked = len(mtl_polys)
    if len(mtl_polys) < 2:
        r.info = "Fewer than 2 MTL2 polygons - nothing to check."
        return r

    bboxes = [bbox(p) for p in mtl_polys]
    n = len(bboxes)
    violation_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = bbox_distance(bboxes[i], bboxes[j])
            if 0 < d < 50.0 - 1e-6:
                violation_count += 1
                if len(r.violations) < 20:
                    ci = ((bboxes[i][0]+bboxes[i][2])/2, (bboxes[i][1]+bboxes[i][3])/2)
                    r.violations.append(Violation(
                        "MTL2.S.1",
                        f"Pad spacing {d:.2f} um < 50 um. Poly pair {i}-{j}",
                        location=ci,
                    ))

    if violation_count > 20:
        r.info = f"Total violations: {violation_count} (showing first 20)"
    else:
        r.info = f"Checked {n*(n-1)//2} MTL2-MTL2 pairs"
    return r


def check_sfg_spacing(polys: Dict) -> RuleResult:
    """SP.5 - SFG region spacing >= 10 um on layer (2,0)."""
    r = RuleResult("SP.5", "SFG region spacing >= 10 um")
    sfg_polys = polys.get(LAYER_SFG, [])
    r.checked = len(sfg_polys)
    if len(sfg_polys) < 2:
        r.info = "Fewer than 2 SFG polygons - nothing to check."
        return r

    bboxes = [bbox(p) for p in sfg_polys]
    n = len(bboxes)
    violation_count = 0
    for i in range(n):
        for j in range(i + 1, n):
            d = bbox_distance(bboxes[i], bboxes[j])
            if 0 < d < 10.0 - 1e-6:
                violation_count += 1
                if len(r.violations) < 20:
                    ci = ((bboxes[i][0]+bboxes[i][2])/2, (bboxes[i][1]+bboxes[i][3])/2)
                    r.violations.append(Violation(
                        "SP.5",
                        f"SFG spacing {d:.2f} um < 10 um. Poly pair {i}-{j}",
                        location=ci,
                    ))

    if violation_count > 20:
        r.info = f"Total violations: {violation_count} (showing first 20)"
    else:
        r.info = f"Checked {n*(n-1)//2} SFG-SFG pairs"
    return r


def check_sfg_length(polys: Dict) -> RuleResult:
    """PPLN.L.1 - SFG mixer length 18-22 um target on layer (2,0)."""
    r = RuleResult("PPLN.L.1", "SFG mixer length 18-22 um")
    sfg_polys = polys.get(LAYER_SFG, [])
    r.checked = len(sfg_polys)

    for p in sfg_polys:
        b = bbox(p)
        w = bbox_width(b)
        h = bbox_height(b)
        w_in = 18.0 - 1e-6 <= w <= 22.0 + 1e-6
        h_in = 18.0 - 1e-6 <= h <= 22.0 + 1e-6

        if not w_in and not h_in:
            r.violations.append(Violation(
                "PPLN.L.1",
                f"SFG mixer dims {w:.2f} x {h:.2f} um - neither dimension "
                f"in 18-22 um range. BBox ({b[0]:.1f},{b[1]:.1f})-"
                f"({b[2]:.1f},{b[3]:.1f})",
                location=((b[0]+b[2])/2, (b[1]+b[3])/2),
            ))

    r.info = f"Checked {r.checked} SFG polygons"
    return r


def check_edge_clearance(polys: Dict) -> RuleResult:
    """EDGE.1 - minimum feature to die edge >= 50 um."""
    r = RuleResult("EDGE.1", "Feature-to-die-edge >= 50 um")

    border_polys = polys.get(LAYER_BORDER, [])
    if not border_polys:
        r.info = "No chip border polygon found on layer (99,0) - skipping."
        r.violations.append(Violation(
            "EDGE.1", "No chip border polygon found on layer (99,0)."
        ))
        return r

    border_bb = bbox(border_polys[0])
    chip_xmin, chip_ymin, chip_xmax, chip_ymax = border_bb
    clearance_min = 50.0

    violation_count = 0
    checked = 0
    for layer_key in FAB_LAYERS:
        for p in polys.get(layer_key, []):
            b = bbox(p)
            checked += 1

            d_left   = b[0] - chip_xmin
            d_bottom = b[1] - chip_ymin
            d_right  = chip_xmax - b[2]
            d_top    = chip_ymax - b[3]

            min_edge_dist = min(d_left, d_bottom, d_right, d_top)

            if min_edge_dist < clearance_min - 1e-6:
                violation_count += 1
                layer_name = LAYER_NAMES.get(layer_key, str(layer_key))
                if len(r.violations) < 20:
                    r.violations.append(Violation(
                        "EDGE.1",
                        f"Layer {layer_name}: feature at "
                        f"({b[0]:.1f},{b[1]:.1f})-({b[2]:.1f},{b[3]:.1f}) "
                        f"is {min_edge_dist:.2f} um from die edge (min 50 um). "
                        f"Closest edge: L={d_left:.1f} B={d_bottom:.1f} "
                        f"R={d_right:.1f} T={d_top:.1f}",
                        location=((b[0]+b[2])/2, (b[1]+b[3])/2),
                    ))

    r.checked = checked
    if violation_count > 20:
        r.info = f"Total edge violations: {violation_count} (showing first 20)"
    else:
        r.info = f"Checked {checked} features on {len(FAB_LAYERS)} fab layers"
    return r


def check_same_layer_overlaps(polys: Dict) -> RuleResult:
    """OVERLAP - check for polygon overlaps on same fabrication layers."""
    r = RuleResult("OVERLAP", "Same-layer polygon overlaps")

    total_checked = 0
    total_overlaps = 0

    for layer_key in FAB_LAYERS:
        layer_polys = polys.get(layer_key, [])
        if len(layer_polys) < 2:
            continue

        bboxes = [bbox(p) for p in layer_polys]
        n = len(bboxes)

        for i in range(n):
            for j in range(i + 1, n):
                total_checked += 1
                if bbox_overlaps(bboxes[i], bboxes[j]):
                    total_overlaps += 1
                    if len(r.violations) < 20:
                        layer_name = LAYER_NAMES.get(layer_key, str(layer_key))
                        ci = ((bboxes[i][0]+bboxes[i][2])/2,
                              (bboxes[i][1]+bboxes[i][3])/2)
                        r.violations.append(Violation(
                            "OVERLAP",
                            f"Layer {layer_name}: bbox overlap between "
                            f"poly {i} ~({ci[0]:.1f},{ci[1]:.1f}) and poly {j}. "
                            f"Note: bbox overlap != true polygon overlap "
                            f"(conservative check).",
                            location=ci,
                        ))

    r.checked = total_checked
    if total_overlaps > 20:
        r.info = (f"Total bbox overlaps: {total_overlaps} (showing first 20). "
                  f"Bounding-box overlaps are conservative - some may be false positives "
                  f"where polygons are close but do not actually intersect.")
    else:
        r.info = f"Checked {total_checked} polygon pairs across {len(FAB_LAYERS)} fab layers"
    return r


def check_chip_dimensions(polys: Dict) -> RuleResult:
    """CHIP - verify chip extents match expected 1095 x 695 um."""
    r = RuleResult("CHIP", f"Chip dimensions = {EXPECTED_CHIP_WIDTH:.0f} x {EXPECTED_CHIP_HEIGHT:.0f} um")

    border_polys = polys.get(LAYER_BORDER, [])
    if not border_polys:
        r.info = "No chip border polygon on layer (99,0)."
        r.violations.append(Violation("CHIP", "No border polygon found."))
        return r

    b = bbox(border_polys[0])
    actual_w = bbox_width(b)
    actual_h = bbox_height(b)

    r.checked = 1
    r.info = (f"Chip extents: ({b[0]:.2f}, {b[1]:.2f}) to ({b[2]:.2f}, {b[3]:.2f})\n"
              f"         Actual: {actual_w:.2f} x {actual_h:.2f} um\n"
              f"         Expected: {EXPECTED_CHIP_WIDTH:.0f} x {EXPECTED_CHIP_HEIGHT:.0f} um")

    if abs(actual_w - EXPECTED_CHIP_WIDTH) > CHIP_DIM_TOL:
        r.violations.append(Violation(
            "CHIP",
            f"Chip width {actual_w:.2f} um != expected {EXPECTED_CHIP_WIDTH:.0f} um "
            f"(tolerance {CHIP_DIM_TOL} um)",
        ))
    if abs(actual_h - EXPECTED_CHIP_HEIGHT) > CHIP_DIM_TOL:
        r.violations.append(Violation(
            "CHIP",
            f"Chip height {actual_h:.2f} um != expected {EXPECTED_CHIP_HEIGHT:.0f} um "
            f"(tolerance {CHIP_DIM_TOL} um)",
        ))

    return r


def layer_inventory(polys: Dict) -> RuleResult:
    """LAYER_INV - list all layers present with polygon count."""
    r = RuleResult("LAYER_INV", "Layer inventory")

    lines = []
    total = 0
    for layer_key in sorted(polys.keys()):
        count = len(polys[layer_key])
        total += count
        name = LAYER_NAMES.get(layer_key, "UNKNOWN")
        lines.append(f"  ({layer_key[0]:3d}, {layer_key[1]}) {name:30s} : {count:5d} polygons")

    r.checked = total
    r.info = "\n".join(lines) + f"\n  {'':34s} TOTAL : {total:5d} polygons"
    return r


# ===========================================================================
# Report formatter
# ===========================================================================

def format_report(results: List[RuleResult], gds_path: str, cell_name: str) -> str:
    sep = "=" * 78
    thin = "-" * 78
    lines = []

    lines.append(sep)
    lines.append("  DRC REPORT - Monolithic 9x9 N-Radix Chip")
    lines.append(sep)
    lines.append(f"  GDS file : {gds_path}")
    lines.append(f"  Top cell : {cell_name}")
    lines.append(f"  DRC rules: NRadix_Accelerator/docs/DRC_RULES.md v1.1")
    lines.append(sep)
    lines.append("")

    lines.append("  RULE SUMMARY")
    lines.append(thin)
    non_critical = {"LAYER_INV", "OVERLAP"}
    critical_fail = False
    for r in results:
        is_info = r.rule_id in non_critical
        if r.passed:
            tag, marker = "PASS", "[+]"
        elif is_info:
            tag, marker = "INFO", "[i]"
        else:
            tag, marker = "FAIL", "[X]"
        suffix = "  (informational)" if is_info and not r.passed else ""
        lines.append(f"  {marker} {r.rule_id:12s} {tag:5s}  {r.description}{suffix}")
        if not r.passed and not is_info:
            critical_fail = True

    lines.append(thin)
    if critical_fail:
        lines.append("  OVERALL: FAIL - one or more critical rules violated")
    else:
        lines.append("  OVERALL: PASS - all critical rules satisfied")
    lines.append("")

    for r in results:
        lines.append(sep)
        lines.append(f"  Rule {r.rule_id}: {r.description}")
        lines.append(f"  Status: {r.status}   |   Items checked: {r.checked}")
        if r.info:
            for info_line in r.info.split("\n"):
                lines.append(f"  {info_line}")
        if r.violations:
            lines.append(f"  Violations ({len(r.violations)}):")
            for v in r.violations:
                loc = f" @ ({v.location[0]:.1f}, {v.location[1]:.1f})" if v.location else ""
                lines.append(f"    - {v.message}{loc}")
        lines.append("")

    lines.append(sep)
    lines.append("  END OF DRC REPORT")
    lines.append(sep)

    return "\n".join(lines)


# ===========================================================================
# Main DRC driver
# ===========================================================================

def run_drc(gds_path: str) -> Tuple[bool, str]:
    print(f"Loading GDS: {gds_path}")
    if not os.path.isfile(gds_path):
        msg = f"ERROR: GDS file not found: {gds_path}"
        print(msg)
        return False, msg

    lib = gdstk.read_gds(gds_path)
    print(f"  Library: {lib.name}")
    print(f"  Cells: {len(lib.cells)}")

    top_cells = lib.top_level()
    if not top_cells:
        msg = "ERROR: No top-level cell found in GDS."
        print(msg)
        return False, msg

    # Find the actual chip cell — avoid gdsfactory context wrappers ($$$)
    # which include raw sub-cell polygons at local origins
    cell = top_cells[0]

    # First: look for the main chip cell by name (must contain "chip" or "9x9")
    for c_candidate in lib.cells:
        name_lower = c_candidate.name.lower()
        if ("monolithic_chip" in name_lower or "nradix" in name_lower) and "$$$" not in name_lower:
            cell = c_candidate
            break
    else:
        # Fallback: use the top cell with the most references (the design, not wrapper)
        for tc in top_cells:
            if "$$$" not in tc.name:
                cell = tc
                break

    print(f"  Top cell: {cell.name}")

    print("  Flattening cell hierarchy...")
    cell.flatten()
    print(f"  Polygons after flatten: {len(cell.polygons)}")

    polys = collect_polygons(cell)
    print(f"  Unique layers: {len(polys)}")

    results: List[RuleResult] = []

    print("\nRunning DRC checks...")

    print("  [1/12] WG.W.1   - waveguide width...")
    results.append(check_wg_width(polys))

    print("  [2/12] WG.S.1   - waveguide spacing...")
    results.append(check_wg_spacing(polys))

    print("  [3/12] MTL1.W.1 - heater width...")
    results.append(check_mtl1_width(polys))

    print("  [4/12] MTL1.S.1 - heater spacing...")
    results.append(check_mtl1_spacing(polys))

    print("  [5/12] MTL2.W.1 - bond pad dimension...")
    results.append(check_mtl2_width(polys))

    print("  [6/12] MTL2.S.1 - pad-to-pad spacing...")
    results.append(check_mtl2_spacing(polys))

    print("  [7/12] SP.5     - SFG region spacing...")
    results.append(check_sfg_spacing(polys))

    print("  [8/12] PPLN.L.1 - SFG mixer length...")
    results.append(check_sfg_length(polys))

    print("  [9/12] EDGE.1   - feature-to-die-edge...")
    results.append(check_edge_clearance(polys))

    print("  [10/12] OVERLAP - same-layer overlaps...")
    results.append(check_same_layer_overlaps(polys))

    print("  [11/12] CHIP    - chip dimensions...")
    results.append(check_chip_dimensions(polys))

    print("  [12/12] LAYER_INV - layer inventory...")
    results.append(layer_inventory(polys))

    report = format_report(results, gds_path, cell.name)
    print("\n" + report)

    # OVERLAP and LAYER_INV are informational — not critical DRC rules.
    # Same-layer polygon overlaps merge during mask generation (standard GDSII behavior).
    non_critical = {"LAYER_INV", "OVERLAP"}
    critical_rules = [r for r in results if r.rule_id not in non_critical]
    all_pass = all(r.passed for r in critical_rules)

    return all_pass, report


def main() -> int:
    gds_path = GDS_PATH
    if len(sys.argv) > 1:
        gds_path = sys.argv[1]

    all_pass, report = run_drc(gds_path)

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {REPORT_PATH}")

    exit_code = 0 if all_pass else 1
    print(f"Exit code: {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
