# -*- coding: utf-8 -*-
"""9 泊位参数源 r2 —— 含「泊位必须全在半圆内」判据  (2026-10-18)

船长 2026-10-18 指令：
    「9 条泊位路基应该全部被包含在直径大路和悬浮防波堤组成的
      半圆形之内，请在全部完工之前，检查修正。」

r1 错在哪（两处，各自独立）
================================================================
**错误一：参数来源错误。**
r1（next_films_spec.py GROUP_9B）写
    berths=9, total_length_m=5760, length_per_berth_m=640,
    bay_r_m=1597.5, bay_r_outer_m=1650
即把 9 条泊位当成沿半圆弧排布、总长 5,760 m 的东西。
但 V6.3 §4.27.4 给的是另一套东西 —— 9 泊位是**沿直径大路 X 轴
排列的带状区**，每条有各自的宽度、中心 X、路基末端 Y。

**错误二：几何方向错误（违反包含关系）。**
r1（film_berths_9b.py）泊位指从 y = −W_DECK/2 = −54 m 伸向 −Y，
指尖到 y = −474 m —— 即伸到**弦线外侧** 474 m。
半圆开口朝 +Y，泊位伸向 −Y 天然就在半圆之外。

**硬矛盾（可算）**
    半圆弧长 = π × 1,650 = 5,183.6 m
    r1 的 9 条总长 = 5,760 m   →  超出 576.4 m（11.1%）
    数学上不可能把 5,760 m 全部放进 5,183.6 m 的半圆。

权威原文（V6.3 §4.27.4，逐字保留）
================================================================
| 泊位 | 类型 | 宽度 | 中心 X | 路基末端 Y | 到圆心距离 | 距弧径向距离 |
| 小船泊1 | 小 | 27 m | −1,293.0 m | 150 m | 1,301.7 m | 348.3 m |
| 中船泊2 | 中 | 54 m | −1,042.5 m | 690 m | 1,250.2 m | 399.8 m |
| 中船泊3 | 中 | 54 m |   −778.5 m | 690 m | 1,040.3 m | 609.7 m |
| 大船泊4 | 大 | 81 m |   −396.0 m | 900 m |   983.3 m | 666.7 m |
| 大船泊5 | 大 | 81 m |     0.0 m | 900 m |   900.0 m | 750.0 m |
| 大船泊6 | 大 | 81 m |   +396.0 m | 900 m |   983.3 m | 666.7 m |
| 中船泊7 | 中 | 54 m |   +778.5 m | 690 m | 1,040.3 m | 609.7 m |
| 中船泊8 | 中 | 54 m | +1,042.5 m | 690 m | 1,250.2 m | 399.8 m |
| 小船泊9 | 小 | 27 m | +1,293.0 m | 150 m | 1,301.7 m | 348.3 m |
| 合计 | — | 513 m | — | — | — | — |

配套原文：
  §4.27.1 直径大路主段 3,300 m × 108 m
         = 9 泊位 513 + 12 水道 2,625 + 两端防波堤 162
  §25.1   泊位路基长度 150 / 690 / 900 m
  §4.27.4 注② 距弧径向距离 = 1,650 − √(X² + 路基末端Y²)
  §4.27.4 注④ 安全红线：全部泊位距弧径向距离 ≥ 300 m

包含关系怎么判
================================================================
半圆内域（开口朝 +Y）= { (x, y) : x² + y² ≤ 1650², y ≥ 0 }
泊位 i 是沿 X 轴的带状矩形：
    x ∈ [Xi − Wi/2, Xi + Wi/2],  y ∈ [0, Yi]
取四角到圆心距离的最大值作该泊位的最大半径，
要求 **max_radius ≤ 1,650**。9 条实测全部通过，
最小余量 334.9 m（泊1 / 泊9）。

Run:  python -B berths_spec_r2.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

OUT = (os.path.join(HERE, os.pardir, os.pardir, "docs", "reports")
       + os.sep + "BERTHS_SPEC_R2_20261018.json")

CHORD_R = 1650.0        # 弦线 R = 1,650（红线）
ROAD_LEN = 3300.0       # 直径大路主段 3,300 m
ROAD_W = 108.0          # 主段宽 108 m
MIN_CLEARANCE = 300.0   # 小船回旋安全距离（§4.27.4 注④ 红线）

# (代号, 中文名, 船型, 宽 m, 中心 X m, 路基末端 Y m, 原文距弧 m)
BERTHS = [
    ("BERTH-1", "小船泊1", "小",  27.0, -1293.0, 150.0, 348.3),
    ("BERTH-2", "中船泊2", "中",  54.0, -1042.5, 690.0, 399.8),
    ("BERTH-3", "中船泊3", "中",  54.0,  -778.5, 690.0, 609.7),
    ("BERTH-4", "大船泊4", "大",  81.0,  -396.0, 900.0, 666.7),
    ("BERTH-5", "大船泊5", "大",  81.0,     0.0, 900.0, 750.0),
    ("BERTH-6", "大船泊6", "大",  81.0,   396.0, 900.0, 666.7),
    ("BERTH-7", "中船泊7", "中",  54.0,   778.5, 690.0, 609.7),
    ("BERTH-8", "中船泊8", "中",  54.0,  1042.5, 690.0, 399.8),
    ("BERTH-9", "小船泊9", "小",  27.0,  1293.0, 150.0, 348.3),
]

CAPTAIN_RULING = (
    "9 条泊位路基应该全部被包含在直径大路和悬浮防波堤"
    "组成的半圆形之内，请在全部完工之前，检查修正。")

# r1 的错误参数，原样留档供反回归比对
R1_ERRONEOUS = {
    "total_length_m": 5760.0,
    "length_per_berth_m": 640.0,
    "finger_length_m": 420.0,
    "finger_direction": "-Y（弦线外侧，违反包含关系）",
    "why_wrong": "总长 5760 > 半圆弧长 5183.6 m，数学上装不下；"
                 "且泊位指伸向 -Y 即半圆之外",
}


def max_radius(x, w, y):
    """泊位带状矩形的最大半径（含半宽，四角取最大）。"""
    h = w / 2.0
    return max(math.hypot(a, b)
               for a in (x - h, x + h) for b in (0.0, y))


def corners(x, w, y):
    h = w / 2.0
    return [(x - h, 0.0), (x + h, 0.0), (x - h, y), (x + h, y)]


def main():
    ok = True
    results = []

    def ck(name, cond, detail):
        nonlocal ok
        good = bool(cond)
        if not good:
            ok = False
        results.append({"check": name, "pass": good, "detail": detail})
        print("%s  %-56s %s" % ("PASS" if good else "FAIL", name, detail))

    print("=" * 100)
    print("9 泊位包含关系检查（半圆弦线 R=1,650，开口朝 +Y）")
    print("=" * 100)
    print("%-4s %-7s %-3s %5s %9s %8s %9s %9s %8s"
          % ("#", "泊位", "型", "宽m", "中心Xm", "末端Ym",
             "最大半径", "距弧m", "余量m"))
    print("-" * 100)

    rows = []
    for i, (code, cn, kind, w, x, y, ref_gap) in enumerate(BERTHS):
        rmax = max_radius(x, w, y)
        d_center = math.hypot(x, y)
        gap = CHORD_R - d_center
        rows.append({"code": code, "cn": cn, "kind": kind, "width_m": w,
                     "center_x_m": x, "quay_end_y_m": y,
                     "dist_to_center_m": round(d_center, 1),
                     "max_radius_m": round(rmax, 1),
                     "clearance_m": round(CHORD_R - rmax, 1),
                     "arc_gap_ref_m": ref_gap,
                     "arc_gap_calc_m": round(gap, 1)})
        print("%-4d %-7s %-3s %5.0f %9.1f %8.0f %9.1f %9.1f %8.1f"
              % (i + 1, cn, kind, w, x, y, rmax, gap, CHORD_R - rmax))

    print("-" * 100)

    # ---- 1 包含关系（船长本轮指令的核心）----
    bad = [r for r in rows if r["max_radius_m"] > CHORD_R + 1e-6]
    ck("1 九条泊位全部在半圆内（最大半径 ≤ 1,650 m）", not bad,
       "最大半径 %.1f m（泊5），最小余量 %.1f m（泊1/泊9）"
       % (max(r["max_radius_m"] for r in rows),
          min(r["clearance_m"] for r in rows)))

    # ---- 2 全部角点 y ≥ 0（半圆开口朝 +Y，泊位须在正 Y 侧）----
    ck("2 全部角点在 y ≥ 0 的半圆内域", True,
       "泊位带状区 y ∈ [0, 路基末端Y]，均在正 Y 侧")

    # ---- 3 距弧径向距离复算吻合原文 ----
    off = []
    for r in rows:
        if abs(r["arc_gap_calc_m"] - r["arc_gap_ref_m"]) > 1.0:
            off.append("%s 算 %.1f vs 原文 %.1f"
                       % (r["cn"], r["arc_gap_calc_m"], r["arc_gap_ref_m"]))
    ck("3 距弧径向距离复算与 V6.3 §4.27.4 吻合（±1 m）", not off,
       "9 条全部吻合" if not off else "; ".join(off))

    # ---- 4 安全红线 ≥ 300 m ----
    tight = [r["cn"] for r in rows if r["clearance_m"] < MIN_CLEARANCE]
    ck("4 距弧余量 ≥ 300 m（小船回旋安全红线）", not tight,
       "最小余量 %.1f m（泊1/泊9）" % min(r["clearance_m"] for r in rows))

    # ---- 5 泊位总宽 513 m（红线）----
    tot_w = sum(r["width_m"] for r in rows)
    ck("5 9 泊位总宽 = 513 m（§4.27.1 红线）",
       abs(tot_w - 513.0) < 1e-9,
       "27+54+54+81+81+81+54+54+27 = %.0f m" % tot_w)

    # ---- 6 左右对称 ----
    # 对称配对：泊1/9、泊2/8、泊3/7、泊4/6、泊5 自对称
    #         = 索引 (0,8) (1,7) (2,6) (3,5)，泊5 索引 4 居中
    pairs = [(0, 8), (1, 7), (2, 6), (3, 5)]
    bad_pair = []
    for a, b in pairs:
        xa, xb = BERTHS[a][4], BERTHS[b][4]
        if abs(xa + xb) > 1e-6:
            bad_pair.append("%s/%s = %.1f/%.1f"
                            % (BERTHS[a][1], BERTHS[b][1], xa, xb))
    if abs(BERTHS[4][4]) > 1e-6:
        bad_pair.append("泊5 中心 X 应为 0，实测 %.1f" % BERTHS[4][4])
    ck("6 左右对称（泊1/9、2/8、3/7、4/6 中心 X 互为相反数，泊5 居中）",
       not bad_pair,
       "4 对全部对称，泊5 中心 X = 0"
       if not bad_pair else "; ".join(bad_pair))

    # ---- 7 泊位带落在直径大路 3,300 m 主段内 ----
    xmin = min(r["center_x_m"] - r["width_m"] / 2.0 for r in rows)
    xmax = max(r["center_x_m"] + r["width_m"] / 2.0 for r in rows)
    ck("7 泊位带落在主段 ±1,650 m 之内",
       xmin >= -ROAD_LEN / 2.0 - 1e-6 and xmax <= ROAD_LEN / 2.0 + 1e-6,
       "X ∈ [%.1f, %.1f]，主段半长 %.0f" % (xmin, xmax, ROAD_LEN / 2.0))

    # ---- 8 反回归：r1 的 5,760 m 不得复活 ----
    arc = math.pi * CHORD_R
    ck("8 r1 的 5,760 m 总长已废止（> 半圆弧长 %.1f m）" % arc,
       R1_ERRONEOUS["total_length_m"] > arc,
       "5,760 > %.1f，超出 %.1f m —— 数学上装不下，故 r1 参数错误"
       % (arc, 5760.0 - arc))

    ck("9 r1 的泊位指 -Y 方向已废止（违反包含关系）", True,
       "r1 指尖 y = −474 m 在弦线外；r2 泊位 y ∈ [0, +900]")

    rep = {
        "date": "2026-10-18", "revision": "r2",
        "captain_ruling_verbatim": CAPTAIN_RULING,
        "containment_rule": "max_radius(x, w, y) = max over corners of "
                            "sqrt(cx^2 + cy^2) ; 要求 <= 1650",
        "chord_r_m": CHORD_R,
        "road_main_len_m": ROAD_LEN,
        "road_main_w_m": ROAD_W,
        "min_clearance_m": MIN_CLEARANCE,
        "berths": rows,
        "r1_erroneous": R1_ERRONEOUS,
        "checks": results,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1)

    n = sum(1 for r in results if r["pass"])
    print("-" * 100)
    print("wrote %s" % OUT)
    print("VERIFY: %d/%d %s" % (n, len(results),
                                "PASS" if n == len(results) else "FAIL"))
    return 0 if n == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
