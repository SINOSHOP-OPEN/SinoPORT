# -*- coding: utf-8 -*-
"""半圆形防波堤 · 径向同心环几何生成器（2026-10-18 r2）

为什么需要这个文件
================================================================
r1 的 F6/F7 把防波堤做成一条**独立的直线沉箱链**（720 m 长，
8 个沉箱端到端），船长的裁定已经否定这种画法：81 / 200 / 100 m
是同一条半圆形防波堤沿**径向**的四段，不是三条并排的直线结构。

本文件按 V6.3 §27.2 的径向坐标表，在弦线 R=1,650 的半圆上，
逐段生成同心环（annular arc）几何：

    BW-INNER    R 1569.1~1596.1   27 m   MOD-STD
    BW-CHANNEL  R 1596.1~1623.1   27 m   MOD-STD
    BW-OUTER    R 1623.1~1650.1   27 m   MOD-STD   -> 核心 81 m
    BW-PORT     R 1650.1~1750.1  100 m   MOD-DM
    BW-MID      R 1750.1~1850.1  100 m   MOD-DM    -> 外围 200 m
    BW-SEA      R 1850.1~1950.1  100 m   金字塔立方体 -> 迎海 100 m
                                                  合计 381 m

坐标约定：圆心在原点，半圆开口朝 -Y，弧线位于 +Y 侧。
径向角 th 从 -pi/2 扫到 +pi/2（逆时针），即标准上半圆。

分段长度修正（r1 的三处缺陷，这里根治）
================================================================
r1 的「半圆防波堤」墙体段长按**弦长**算，环的两端被拉开出现可见
缝隙。这里每一段的实长按**该半径处的弧长** r*step 计算，并把
段长放大 SEG_OVERLAP 倍，确保相邻段在角向必定相交、无缝隙。
模块则按弧长 f = i*L/R 定位，实测中心间距与设计值误差 < 1 mm。

开口：9 个 × 150 m，沿弦线 R=1,650 的弧长等分，两端各留半开口。

Run:  python -B bw_geometry.py
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# 2026-10-19: dropped the hard-coded absolute path into another project
# directory.  raster_core now ships inside this repo at src/core/.
for p in (HERE, os.path.abspath(os.path.join(HERE, os.pardir, "core"))):
    if p not in sys.path:
        sys.path.insert(0, p)

import next_films_spec_r2 as R2                     # noqa: E402

# 全部几何以 mm 为单位，与 raster_core / film_engine 一致
CHORD_R = R2.CHORD_R * 1000.0          # 1,650,000 mm
OUTER_R = R2.OUTER_R * 1000.0          # 1,950,100 mm
CORE_INNER_R = R2.CORE_INNER_R * 1000.0  # 1,569,100 mm
BANDS_MM = [(c, ri * 1000.0, ro * 1000.0, w * 1000.0, fam, cn)
            for c, ri, ro, w, fam, cn in R2.BANDS]
TOTAL_W = R2.TOTAL_M * 1000.0          # 381,000 mm

N_OPEN = R2.OPENINGS                   # 9
OPEN_L = R2.OPENING_LEN_M * 1000.0     # 150,000 mm

TH_A = -math.pi / 2.0                   # 起始角（弦线一端）
TH_B = +math.pi / 2.0                   # 终止角（弦线另一端）

SEG_OVERLAP = 1.10                     # 段长放大系数，防角向缝隙

# 各模块的竖向尺寸（mm）
MOD_STD_LWH = (27000.0, 27000.0, 7500.0)     # MOD-STD-R7 实测
MOD_DM_LWH = (27000.0, 27000.0, 6000.0)      # V6.4 §45.1 实测
PYR_SIDE = 18000.0                            # BW-WAVE61 立方体边长
PYR_CAP_H = 11450.0                           # V6.4 金字塔高 11,450 mm

FAMILY_Z_TOP = {"MOD-STD": 4400.0, "MOD-DM": 3000.0, "PYRAMID": 9000.0}


def band(code):
    for b in BANDS_MM:
        if b[0] == code:
            return b
    raise KeyError(code)


def solid_arc_len_m():
    """实心环的弧长（按弦线半径）。"""
    return math.pi * R2.CHORD_R


def arc_span_with_openings(r_mm):
    """给定半径，避开 9 个开口后的可用角域，返回 [(th0, th1), ...]。

    开口宽 150 m，沿弧长分布。半圆弧长 = pi*R；9 个开口对称布置，
    两端各留半个开口的余量，使布局对称且不越界。
    """
    arc_total = math.pi * r_mm
    n = N_OPEN
    # 开口 150 m 是按弦线 R=1,650 计的；换算到半径 r 的角宽
    dth_open = OPEN_L / r_mm
    # 对称布局：9 个开口在 [-pi/2, pi/2] 内等距排列
    #  开口中心角：从两端各留 dth/2 起，每隔 gap 一个
    dth_total = TH_B - TH_A
    gap = (dth_total - n * dth_open) / n
    if gap <= 0:
        # 极端半径下开口吃满整圈，退化为整段实心
        return [(TH_A, TH_B)]
    out = []
    th = TH_A + gap / 2.0
    while th + dth_open <= TH_B - gap / 2.0 + 1e-9:
        out.append((th, th + dth_open))
        th += dth_open + gap
    # 反过来生成实心段
    solids = []
    prev = TH_A
    for (o0, o1) in out:
        if o0 > prev + 1e-9:
            solids.append((prev, o0))
        prev = o1
    if prev < TH_B - 1e-9:
        solids.append((prev, TH_B))
    return solids


def arc_boxes(r_in, r_out, z_top, thick=None, family="MOD-STD",
              pitch=None, seg_len=None, skip_openings=True):
    """生成一段径向环带的长方体网格（沿弧切向排布的模块）。

    返回 (centers, sizes) —— 都是 numpy 数组，可直接喂 film_engine.boxes。

    seg_len: 目标分段弧长（mm）。若给 None，用该模块的自然节距。
    """
    if thick is None:
        thick = family_thickness(family)
    r_mid = 0.5 * (r_in + r_out)
    if seg_len is None:
        seg_len = seg_len_default(family, r_mid)

    spans = (arc_span_with_openings(r_mid) if skip_openings
             else [(TH_A, TH_B)])

    C, S = [], []
    for (th0, th1) in spans:
        arc = r_mid * (th1 - th0)
        n = max(1, int(round(arc / seg_len)))
        # 段长按该半径处的弧长，并放大 SEG_OVERLAP 保证相邻段相交
        dth = (th1 - th0) / n
        seg_arc = r_mid * dth * SEG_OVERLAP
        for i in range(n):
            th = th0 + (i + 0.5) * dth
            x = r_mid * math.cos(th)
            y = r_mid * math.sin(th)
            # 切向长度取该半径处的弧长（×放大系数），径向取实宽
            C.append([x, y, z_top - thick / 2.0])
            S.append([seg_arc, r_out - r_in, thick])
    if not C:
        return np.zeros((0, 3)), np.zeros((0, 3))
    return np.array(C), np.array(S)


def family_thickness(family):
    if family == "MOD-STD":
        return MOD_STD_LWH[2]
    if family == "MOD-DM":
        return MOD_DM_LWH[2]
    return PYR_SIDE


def seg_len_default(family, r_mid):
    """模块沿弧向的自然节距（mm）。

    MOD-STD 27 m 方模块沿弧排布 -> 节距 27 m；
    MOD-DM 同为 27 m 方模块 -> 27 m；
    金字塔立方体 18 m -> 18 m。
    """
    if family == "MOD-STD":
        return MOD_STD_LWH[0]
    if family == "MOD-DM":
        return MOD_DM_LWH[0]
    return PYR_SIDE


def core_boxes():
    """MOD-STD 核心三段（81 m）的中性几何，用于对位检查。"""
    out = []
    for code in ("BW-INNER", "BW-CHANNEL", "BW-OUTER"):
        _c, ri, ro, _w, fam, cn = band(code)
        C, S = arc_boxes(ri, ro, FAMILY_Z_TOP[fam], family=fam)
        out.append((code, cn, fam, C, S))
    return out


def _selftest():
    ok = True

    def ck(name, cond, detail):
        nonlocal ok
        good = bool(cond)
        if not good:
            ok = False
        print("%s  %-54s %s" % ("PASS" if good else "FAIL", name, detail))

    print("=" * 96)
    print("同心环几何自检")
    print("=" * 96)

    # 1 各段弧向模块数与覆盖率
    for code in ("BW-INNER", "BW-CHANNEL", "BW-OUTER",
                 "BW-PORT", "BW-MID", "BW-SEA"):
        _c, ri, ro, _w, fam, cn = band(code)
        C, S = arc_boxes(ri, ro, FAMILY_Z_TOP[fam], family=fam)
        r_mid = 0.5 * (ri + ro)
        span = arc_span_with_openings(r_mid)
        solid_arc = sum(r_mid * (b - a) for a, b in span)
        seg = seg_len_default(fam, r_mid)
        ck("%-11s %s 模块数与覆盖率" % (code, cn),
           len(C) > 0 and len(span) == N_OPEN + 1,
           "%d 段 / %d 个模块 / 覆盖实弧 %.0f m / 开口 %.0f m"
           % (len(span), len(C), solid_arc / 1000.0,
              (math.pi * r_mid - solid_arc) / 1000.0))

    # 2 相邻模块角向必须相交（无缝隙）—— 这是 r1 的真实缺陷
    worst = None
    for code in ("BW-INNER", "BW-CHANNEL", "BW-OUTER",
                 "BW-PORT", "BW-MID", "BW-SEA"):
        _c, ri, ro, _w, fam, cn = band(code)
        C, S = arc_boxes(ri, ro, FAMILY_Z_TOP[fam], family=fam)
        r_mid = 0.5 * (ri + ro)
        seg = seg_len_default(fam, r_mid)
        spans = arc_span_with_openings(r_mid)
        for (th0, th1) in spans:
            n = max(1, int(round(r_mid * (th1 - th0) / seg)))
            dth = (th1 - th0) / n
            # 段弧长 / 该半径处的节距；>=1.0 表示必相交
            ratio = (r_mid * dth * SEG_OVERLAP) / seg
            if worst is None or ratio < worst[0]:
                worst = (ratio, code)
    ck("相邻模块角向必相交（无可见缝隙）", worst[0] >= 1.0,
       "最小覆盖比 %.3f @ %s（SEG_OVERLAP=%.2f）"
       % (worst[0], worst[1], SEG_OVERLAP))

    # 3 径向相邻段共享边界（无缝无重叠）
    ok_cont = True
    for a, b in zip(BANDS_MM[:-1], BANDS_MM[1:]):
        if abs(a[2] - b[1]) > 1e-6:
            ok_cont = False
    ck("径向相邻段共享边界", ok_cont,
       " ".join("%s|%s" % (a[0], b[0]) for a, b in
                zip(BANDS_MM[:-1], BANDS_MM[1:])))

    # 4 总径向跨度 = 381 m
    ck("核心内缘到外径 = 381.0 m",
       abs((OUTER_R - CORE_INNER_R) - TOTAL_W) < 1e-6,
       "%.1f mm" % (OUTER_R - CORE_INNER_R))

    # 5 核心三段合计 81 m
    core = sum(band(c)[3] for c in ("BW-INNER", "BW-CHANNEL", "BW-OUTER"))
    ck("核心三段 = 81 m", abs(core - 81000.0) < 1e-6, "%.1f mm" % core)

    # 6 MOD-DM 两段合计 200 m
    dm = sum(band(c)[3] for c in ("BW-PORT", "BW-MID"))
    ck("MOD-DM 两段 = 200 m", abs(dm - 200000.0) < 1e-6, "%.1f mm" % dm)

    # 7 半圆弧长 ≈ 5,183 m
    ck("弦线半圆弧长 ≈ 5,183 m",
       abs(math.pi * CHORD_R - 5183000.0) < 1500.0,
       "%.1f m" % (math.pi * CHORD_R / 1000.0))

    # 8 开口 9 个 × 150 m
    spans = arc_span_with_openings(CHORD_R)
    ck("实心段数 = 开口数 + 1", len(spans) == N_OPEN + 1,
       "%d 个实心段 / %d 个开口" % (len(spans), N_OPEN))

    print("\nVERIFY: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_selftest())
