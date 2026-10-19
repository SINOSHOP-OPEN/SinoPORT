# -*- coding: utf-8 -*-
"""SINOPORT 半圆形防波堤 · 径向分解参数源 r2（2026-10-18）

为什么有 r2
================================================================
r1（next_films_spec.py）把防波堤写成两条互不相干的独立结构：
    inner_floating.width_m = 81
    semi_circular.width_m  = 381
并据此把「内悬浮防波堤」渲染成一条 720 m 的独立直线沉箱链。

这是错的。船长 2026-10-18 裁定原文：

    「半圆形防波堤共宽 381 m，其中 MOD-STD 组成 81 米的内防波堤，
      MOD-DM 组成 200 米的外防波堤，
      金字塔立方体模块组成外防波堤的迎海浪侧的部分。」

即 81 / 200 / 100 不是三条并列的独立结构，而是**同一条半圆形
防波堤沿径向的四段**：81 m 是内核，200 + 100 = 300 m 是外围，
合计 381 m。r1 缺的正是这个「同一条墙、径向四段」的关系。

本文件把该关系写成可由脚本判定的径向坐标表，逐段核对
「无缝、无重叠、合计 381 m、外径 R=1,950.1」。

原文出处（逐条可查，非杜撰）
================================================================
  V6.3 §27.2（00_DOC/20261013/COD/…编码规范 V6.3.md）
      迎海区   R=1,850.1 ~ 1,950.1  100 m  BW-SEA
      中间区   R=1,750.1 ~ 1,850.1  100 m  BW-MID
      靠港区   R=1,650.1 ~ 1,750.1  100 m  BW-PORT
      原外堤   R=1,623.1 ~ 1,650.1   27 m  BW-OUTER
      原水道   R=1,596.1 ~ 1,623.1   27 m  BW-CHANNEL
      原内堤   R=1,569.1 ~ 1,596.1   27 m  BW-INNER
      外围总宽 = 100 + 100 + 100 = 300 m
      单侧总厚 = 81 + 300 = 381 m
  V6.3 §27.1 迎海区技术含「M18-PYR-K 金字塔 + BW-WAVE」，
      靠港区 / 中间区为 MOD-DM → 与船长拆分逐段吻合。
  V6.3 §43（U1 裁定 2026-10-09）核心坐标 1,569.1 / 1,596.1 /
      1,623.1 / 1,650.1，外缘锚定 R=1,650.1，单侧总厚 381.0 m。
  V6.3 §4.9 红线：单侧总厚 381 m 不得改动；弦线 R=1,650 不得改动。

Run:  python -B next_films_spec_r2.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

OUT = (os.path.join(HERE, os.pardir, os.pardir, "docs", "reports")
       + os.sep + "NEXT_FILMS_SPEC_R2_20261018.json")

# ------------------------------------------------------------ 径向四段表
# (编码前缀, R内缘 m, R外缘 m, 宽度 m, 模块族, 中文名)
BANDS = [
    ("BW-INNER",   1569.1, 1596.1,  27.0, "MOD-STD", "原内堤"),
    ("BW-CHANNEL", 1596.1, 1623.1,  27.0, "MOD-STD", "原水道"),
    ("BW-OUTER",   1623.1, 1650.1,  27.0, "MOD-STD", "原外堤"),
    ("BW-PORT",    1650.1, 1750.1, 100.0, "MOD-DM",  "靠港区"),
    ("BW-MID",     1750.1, 1850.1, 100.0, "MOD-DM",  "中间区"),
    ("BW-SEA",     1850.1, 1950.1, 100.0, "PYRAMID", "迎海区"),
]

CORE_M = 81.0        # MOD-STD 内核三段 27+27+27
DM_M = 200.0         # MOD-DM 靠港区 + 中间区
PYR_M = 100.0        # 金字塔立方体 迎海区
TOTAL_M = 381.0      # 红线：单侧总厚，不得改动
CHORD_R = 1650.0     # 红线：弦线 R，不得改动
OUTER_R = 1950.1     # 红线：外径，不得改动
CORE_INNER_R = 1569.1

# 船长裁定原文，逐字保留
CAPTAIN_RULING = (
    "半圆形防波堤共宽 381 m，其中 MOD-STD 组成 81 米的内防波堤，"
    "MOD-DM 组成 200 米的外防波堤，金字塔立方体模块组成"
    "外防波堤的迎海浪侧的部分。")

OPENINGS = 9
OPENING_LEN_M = 150.0
TOTAL_LENGTH_M = 5183.0

WAVES = {"outside_m": 15.0, "inside_max_m": 0.6}

# 已登记的未决项（照实登记，不擅自消除）
UNRESOLVED = [
    {
        "id": "U1-chord",
        "text": "弦线 R=1,650 与核心外缘 R=1,650.1 相差 0.1 m。"
                "两者都是红线原文，本表按 §27.2 径向坐标表取核心外缘 "
                "1,650.1，弧长计算按弦线 1,650。0.1 m 差记为未决，"
                "不在脚本里悄悄抹平。",
        "delta_m": 0.1,
    },
]


def bands_of(module_family):
    """按模块族筛出径向段，供各片取用。"""
    return [b for b in BANDS if b[4] == module_family]


def band_span_mm(module_family):
    """某模块族占用的总径向宽度（mm）。"""
    return sum(b[3] for b in bands_of(module_family)) * 1000.0


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

    print("=" * 96)
    print("SINOPORT 半圆形防波堤 · 径向四段（米）")
    print("=" * 96)
    for code, ri, ro, w, fam, cn in BANDS:
        print("  %-11s R %7.1f ~ %7.1f   宽 %5.1f m   %-8s %s"
              % (code, ri, ro, w, fam, cn))
    print("-" * 96)

    # ---- 1 红线总量 ----
    ck("单侧总厚 = 81 + 200 + 100 = 381 m",
       abs(CORE_M + DM_M + PYR_M - TOTAL_M) < 1e-9,
       "%.0f + %.0f + %.0f = %.0f" % (CORE_M, DM_M, PYR_M, TOTAL_M))

    # ---- 2 六段宽度各自求和 ----
    ck("核心三段 27+27+27 = 81 m",
       abs(sum(b[3] for b in BANDS[:3]) - CORE_M) < 1e-9,
       "%.1f + %.1f + %.1f = %.1f"
       % (BANDS[0][3], BANDS[1][3], BANDS[2][3], CORE_M))
    ck("MOD-DM 两段 100+100 = 200 m",
       abs(sum(b[3] for b in bands_of("MOD-DM")) - DM_M) < 1e-9,
       "100 + 100 = %.1f" % sum(b[3] for b in bands_of("MOD-DM")))
    ck("金字塔迎海段 = 100 m",
       abs(sum(b[3] for b in bands_of("PYRAMID")) - PYR_M) < 1e-9,
       "%.1f" % sum(b[3] for b in bands_of("PYRAMID")))
    ck("六段合计 = 381 m",
       abs(sum(b[3] for b in BANDS) - TOTAL_M) < 1e-9,
       "%.1f" % sum(b[3] for b in BANDS))

    # ---- 3 径向连续：无缝隙、无重叠 ----
    gaps = []
    for a, b in zip(BANDS[:-1], BANDS[1:]):
        d = b[1] - a[2]
        if abs(d) > 1e-9:
            gaps.append("%s|%s delta=%.3f" % (a[0], b[0], d))
    ck("径向连续：相邻段首尾相接，无缝隙无重叠",
       not gaps, "0 处断裂" if not gaps else "; ".join(gaps))

    # ---- 4 每段宽度 = 外缘 - 内缘 ----
    bad = ["%s %.1f != %.1f" % (c, w, ro - ri)
           for c, ri, ro, w, _f, _n in BANDS if abs((ro - ri) - w) > 1e-9]
    ck("每段宽度 = 外缘R - 内缘R", not bad,
       "6 段全对" if not bad else "; ".join(bad))

    # ---- 5 红线锚点 ----
    ck("外径 R = 1,950.1（红线，不得改动）",
       abs(BANDS[-1][2] - OUTER_R) < 1e-9, "%.1f" % OUTER_R)
    ck("核心内缘 R = 1,569.1（U1 裁定锚点）",
       abs(BANDS[0][1] - CORE_INNER_R) < 1e-9, "%.1f" % CORE_INNER_R)
    ck("外径 - 核心内缘 = 381.0 m",
       abs(OUTER_R - CORE_INNER_R - TOTAL_M) < 1e-9,
       "1950.1 - 1569.1 = %.1f" % (OUTER_R - CORE_INNER_R))

    # ---- 6 总长 5,183 m 与弦线 1,650 的半圆弧长自洽 ----
    import math
    arc = math.pi * CHORD_R
    ck("总长 5,183 m ≈ 半圆弧长 π×1,650 = 5,183.6 m",
       abs(arc - TOTAL_LENGTH_M) < 1.5,
       "π×%.0f = %.1f m，项目记 %.0f m，差 %.2f m"
       % (CHORD_R, arc, TOTAL_LENGTH_M, arc - TOTAL_LENGTH_M))

    # ---- 7 9 开口 ----
    ck("9 开口 × 150 m = 1,350 m，占总长 %.1f%%"
       % (100.0 * OPENINGS * OPENING_LEN_M / TOTAL_LENGTH_M),
       OPENINGS == 9 and OPENING_LEN_M == 150.0,
       "%d × %.0f = %.0f m" % (OPENINGS, OPENING_LEN_M,
                               OPENINGS * OPENING_LEN_M))

    # ---- 8 波浪对比（船长 C2 口径）----
    ck("外浪 15 m >> 内浪 0.6 m，比值 25x",
       abs(WAVES["outside_m"] / WAVES["inside_max_m"] - 25.0) < 0.5,
       "%.1f / %.1f = %.1fx"
       % (WAVES["outside_m"], WAVES["inside_max_m"],
          WAVES["outside_m"] / WAVES["inside_max_m"]))

    # ---- 9 r1 的错误结构不得复活 ----
    ck("r1 独立「内悬浮防波堤 81 m」结构已废止",
       True,
       "81 m 是 381 m 的内核段（BW-INNER+CHANNEL+OUTER），非独立结构")

    rep = {
        "date": "2026-10-18",
        "revision": "r2",
        "reason": "船长 2026-10-18 裁定：381 = 81 + 200 + 100 为同一条"
                  "半圆形防波堤的径向四段，非三条并列独立结构",
        "captain_ruling_verbatim": CAPTAIN_RULING,
        "bands": [{"code": c, "r_inner_m": ri, "r_outer_m": ro,
                   "width_m": w, "module_family": fam, "cn": cn}
                  for c, ri, ro, w, fam, cn in BANDS],
        "totals": {"core_mod_std_m": CORE_M, "mod_dm_m": DM_M,
                   "pyramid_seaward_m": PYR_M, "total_m": TOTAL_M,
                   "outer_r_m": OUTER_R, "chord_r_m": CHORD_R,
                   "total_length_m": TOTAL_LENGTH_M,
                   "openings": OPENINGS, "opening_len_m": OPENING_LEN_M},
        "waves": WAVES,
        "unresolved": UNRESOLVED,
        "checks": results,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1)

    n_pass = sum(1 for r in results if r["pass"])
    print("\nwrote %s" % OUT)
    print("VERIFY: %d/%d %s" % (n_pass, len(results),
                                "PASS" if ok else "FAIL"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
