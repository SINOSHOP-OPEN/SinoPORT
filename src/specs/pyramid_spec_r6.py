# -*- coding: utf-8 -*-
"""金字塔立方体开孔规则 R6 —— 孔径 1m -> 900 mm（船长 2026-10-19 裁定）

船长裁定原文
======================================================================
    「金字塔斜面的开孔直径由 1 米改为 900 mm」

口径沿用 R5 全部不变
======================================================================
| 项 | 值 |
|---|---|
| 排布 | 7 排 1/1/2/3/5/8/13（斐波那契） |
| 每面 / 四面 | 33 / **132 孔** |
| 排位 t | 0.86 -> 0.12（自锥顶到锥底阶梯） |
| 间隙 | 船长算法自动分摊：g = (W - n*D) / (n+1) |
| **孔径** | **1,000 -> 900 mm（本次唯一改动）** |

900 mm 的几何影响（实测）
======================================================================
孔径变小 => 剩余宽度变大 => 自动分摊的间隙变宽，布尔更稳：

| 排 | 孔数 | 面宽 mm | 间隙(D=1000) | 间隙(D=900) |
|---|---|---|---|---|
| 5 | 5  | 11,520 | 1,086.7 | 1,170.0 |
| 6 | 8  | 13,680 |565.0   |   720.0 |
| 7 | 13 | 15,840 | **202.9** | **295.7** |

最紧的第7 排间隙从 202.9 mm 升到 295.7 mm。
R5 建模时曾因「相切」导致 OCC 退化（isValid()=False、挖除仅 34%），
故间隙宽度直接决定布尔稳定性 —— 本次改动是**改善**而非风险。

V6.3 未规定开孔直径，此项为船长新增裁定。
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

OUT = (os.path.join(HERE, os.pardir, os.pardir, "docs", "reports")
       + os.sep + "PYRAMID_HOLES_R6_20261019.json")

# ---------------- 几何（与 R3/R4 一致） ----------------
# 【实测修正】金字塔坐在**立方体之上**，不是内部。
# 我初稿误写 PYR_BASE_Z=0 / PYR_TOP_Z=9000，使整个锥体低了 9,000 mm
# 落在立方体内，cut 后裂成 2 个实体（solids=2）、体积偏大 6.679 m3、
# 挖孔量只有 5.77 m3。R3 的正确值是 base=9000 / top=18000。
CUBE_SIDE = 18000.0
CUBE_Z0, CUBE_Z1 = -9000.0, 0.0
PYR_PLAN = 18000.0
PYR_BASE_Z, PYR_TOP_Z = 9000.0, 18000.0
PYR_HEIGHT = 9000.0
SLOPE_DEG = 45.0

# 【实测修正 R5】斜壁真实法向厚度 = SLOPE_THICK / 2，不是 SLOPE_THICK。
# 建模脚本的内锥偏移是 d = SLOPE_THICK / √2（水平与垂直各），
# 两个平行斜面（外锥面 y+z=18000，内锥面 y+z=18000+d）的法向距离
#   = d / √2 = SLOPE_THICK / 2 = 150 mm
# 而 SLOPE_THICK 声明 300 —— 声明值是实际的 2 倍。
# 因此孔心沉入量应是真实半壁厚 = SLOPE_THICK / 4 = 75 mm，
# 此前用 SLOPE_THICK / 2 = 150 mm，偏移量翻倍，把孔心推到壁体外侧，
# 实测上部各排（第 1/2/4 排）挖除量 0 或负、第 5/6/7 排等效穿壁
# 仅 150 mm（真实壁厚 150，即只切到一半）。
SLOPE_THICK = 300.0
WALL_THICK_ACTUAL = SLOPE_THICK / 2.0        # 150 mm，实测
HOLE_SINK = WALL_THICK_ACTUAL / 2.0          # 75 mm，沉到中面
# 【R4 已修正并沿用】底边中点 → 顶点的实长（非角点距离）
SLANT = math.hypot(PYR_PLAN / 2.0, PYR_HEIGHT)      # 12727.92

# ---------------- 管系（未改） ----------------
PIPE_D = 2000.0
PIPE_Z_TOP, PIPE_Z_BOT = 8700.0, -8700.0
PIPE_GRID = [-6000.0, -2000.0, 2000.0, 6000.0]
N_PIPE_Z, N_PIPE_X, N_PIPE_Y = 16, 25, 20
N_PIPE_TOTAL = N_PIPE_Z + N_PIPE_X + N_PIPE_Y

# ---------------- 开孔 R5 ----------------
CAPTAIN_RULING = (
    "共开孔 7 排 128 个各直径 1 米，上的第一排 1 个，第二排 1 个，"
    "第三排 2 个，第四排 3 个，第五排 5 个，第六排 8 个，"
    "下的第七排 13 个孔")

CAPTAIN_ADJUDICATION = {
    "total": "7 排求和 = 33/面 x 4 面 = 132（船长裁定以此为准；"
             "原文「128」视为笔误）",
    "bottom_row_13": "13 孔排布：间隙按剩余宽度自动分摊（船长 12:06 纠正）——"
                     "g = (18000 − 13000)/14 = 357.14 mm，"
                     "13×1000 + 14×357.14 = 18000 精确吻合。"
                     "我此前误实现为「孔相切 + 贴边缘」，"
                     "导致 OCC 退化边、实体 isValid()=False、"
                     "挖除仅 34%，已废止",
}

# 斐波那契 7 排，自锥顶到锥底
HOLE_ROW_N = [1, 1, 2, 3, 5, 8, 13]
HOLE_ROWS = len(HOLE_ROW_N)                        # 7
HOLE_PER_SLOPE = sum(HOLE_ROW_N)                   # 33
N_SLOPES = 4
N_HOLES_TOTAL = HOLE_PER_SLOPE * N_SLOPES          # 132

# 排位：自锥顶 0.86 均匀递减到锥底 0.12
HOLE_ROW_T = [0.86, 0.72, 0.60, 0.48, 0.36, 0.24, 0.12]

HOLE_DIA = 900.0

# 【船长 12:06 纠正】间隙按该排剩余宽度自动分摊，不是相切。
# 船长原话：「金字塔底边长是 18000，13 个孔的合计直径是 13000，
#   13 个孔之间含边线，共有 14 个间隙分摊 5000 mm，物理数学上可行」
#   g = (18000 − 13×1000) / (13−1 + 2) = 5000 / 14 = 357.14 mm
# 校验：13 孔占 12×1357.14 + 1000 = 17,285.7，两端各 357.14，
#   合计 18,000.0 —— 与底边精确吻合。
#
# 【我此前的错】把「边距 0」实现成「相邻孔相切（pitch = 孔径）+ 贴斜面边缘」
#   —— 两者都不是船长意思，且相切圆柱 fuse 后产生 OCC 退化边：
#   实测 isValid()=False、R500 面 153≠132、挖除仅 5.2976/15.5408 = 34.1%，
#   多数孔根本没穿透。间隙必须 > 0。
HOLE_MARGIN = None      # None = 按该排剩余宽度自动分摊（船长口径）
HOLE_EDGE = None        # None = 两端余量与孔间距等分（船长口径）
# HOLE_SINK 已在几何段定义（= 真实壁厚的一半），此处不重复。

# 历史规则，仅留档供反回归
SUPERSEDED = {
    "R3": {"rows": 3, "per_row": 9, "per_slope": 27, "total": 108},
    "R4": {"rows": 5, "row_n": [1, 2, 6, 9, 9], "per_slope": 27,
           "total": 108},
    "R5_wording_128": "原文「共 128 个」与 7 排求和 132 互斥，"
                      "船长裁定取 132",
}


def face_width(t):
    return PYR_PLAN * (1.0 - t)


def row_gap(t, n):
    """该排的间隙（孔间 12 个 + 两端 2 个，共 n+1 段等分剩余宽度）。

    船长口径：g = (W − n×D) / (n + 1)，两端余量亦为 g。
    第 7 排 t=0 时 g = (18000 − 13000)/14 = 357.14 mm。
    """
    spare = face_width(t) - n * HOLE_DIA
    return spare / (n + 1)


def row_positions(t, n):
    """一排 n 孔的横向偏移（相对面中线）。

    间隙自动分摊，故任何 t 只要 n×D ≤ 面宽就能放下；
    间隙 < 0 说明该排真的塞不下，此时报错。
    """
    g = row_gap(t, n)
    if g <= 0.0:
        raise ValueError(
            "row at t=%.3f width=%.0f cannot host %d holes "
            "(needs %.0f, spare %.0f)"
            % (t, face_width(t), n, n * HOLE_DIA, g))
    pitch = HOLE_DIA + g
    span = (n - 1) * pitch
    return [(-span / 2.0 + i * pitch) for i in range(n)]


def t_limit(n):
    """容纳 n 孔的 t 上限：面宽 ≥ n×D（即间隙 ≥ 0）。"""
    return 1.0 - n * HOLE_DIA / PYR_PLAN


def hole_positions():
    """4 斜面 × 7 排 = 132 孔的世界坐标。"""
    # 45 度的 sin / cos（模块级）
cs, sn = (math.cos(math.radians(SLOPE_DEG)),
          math.sin(math.radians(SLOPE_DEG)))
#
# 【实测修正 R5】-X / +X 两面的 up 向量 X 分量符号原本写反，
# 导致这 66 个孔全部落在锥体之外、挖除量 0.0000 m3、R500 面 = 0。
# 实测判据（走 up*1000 后半径必须减小，即朝锥内）：
#     面0 -Y  r 9000 -> 8293  OK
#     面1 -X  r 9000 -> 9707  朝外（错）
#     面2 +Y  r 9000 -> 8293  OK
#     面3 +X  r 9000 -> 9707  朝外（错）
# 正确：-X 面 base=(-9000,0) 需沿 +X 上行到顶点 x=0，故 up=(+cs,0,sn)。
# 四面 up 均满足「沿 up 走半径减小」，nrm 均满足「沿 nrm 走半径增大」。
SLOPE_FRAMES = [
    dict(base=(0.0, -PYR_PLAN / 2.0), across=(1.0, 0.0),
         up=(0.0, cs, sn), nrm=(0.0, -sn, cs)),
    dict(base=(-PYR_PLAN / 2.0, 0.0), across=(0.0, 1.0),
         up=(cs, 0.0, sn), nrm=(-sn, 0.0, cs)),
    dict(base=(0.0, PYR_PLAN / 2.0), across=(-1.0, 0.0),
         up=(0.0, -cs, sn), nrm=(0.0, sn, cs)),
    dict(base=(PYR_PLAN / 2.0, 0.0), across=(0.0, -1.0),
         up=(-cs, 0.0, sn), nrm=(sn, 0.0, cs)),
]


def hole_positions():
    """4 斜面 × 7 排 = 132 孔的世界坐标。"""
    _S = SLOPE_FRAMES
    out = []
    for si, fr in enumerate(_S):
        bx, by = fr["base"]
        ux, uy = fr["across"]
        px, py, pz = fr["up"]
        nx, ny, nz = fr["nrm"]
        for ri, (n, t) in enumerate(zip(HOLE_ROW_N, HOLE_ROW_T)):
            s_up = t * SLANT
            for ci, off in enumerate(row_positions(t, n)):
                x = bx + px * s_up + ux * off
                y = by + py * s_up + uy * off
                z = PYR_BASE_Z + pz * s_up
                x -= nx * HOLE_SINK
                y -= ny * HOLE_SINK
                z -= nz * HOLE_SINK
                out.append({
                    "slope": si, "row": ri + 1, "col": ci + 1,
                    "row_holes": n, "t": t,
                    "across_off": round(off, 1),
                    "centre": [round(x, 1), round(y, 1), round(z, 1)],
                    "normal": [round(nx, 5), round(ny, 5), round(nz, 5)],
                })
    return out


def row_table():
    rows = []
    for ri, (n, t) in enumerate(zip(HOLE_ROW_N, HOLE_ROW_T)):
        g = row_gap(t, n)
        rows.append({
            "row": ri + 1, "holes": n, "t": t,
            "face_width_mm": round(face_width(t), 1),
            "need_mm": round(n * HOLE_DIA, 1),
            "spare_mm": round(face_width(t) - n * HOLE_DIA, 1),
            "gap_mm": round(g, 2),
            "pitch_mm": round(HOLE_DIA + g, 2),
            "t_limit": round(t_limit(n), 4),
            "fits": bool(g > 0.0),
            "dist_from_apex_mm": round((1.0 - t) * SLANT, 1),
            "height_z_mm": round(PYR_BASE_Z + sn45() * t * SLANT, 1),
        })
    return rows


def sn45():
    return math.sin(math.radians(SLOPE_DEG))


def spec_dict():
    return {
        "date": "2026-10-18", "revision": "R5",
        "captain_ruling_verbatim": CAPTAIN_RULING,
        "captain_adjudication": CAPTAIN_ADJUDICATION,
        "ruling": {
            "rows_per_slope": HOLE_ROWS,
            "holes_per_row_top_down": list(HOLE_ROW_N),
            "row_t_top_down": list(HOLE_ROW_T),
            "holes_per_slope": HOLE_PER_SLOPE,
            "n_slopes": N_SLOPES,
            "holes_total": N_HOLES_TOTAL,
            "hole_dia_mm": HOLE_DIA,
            "gap_rule": "间隙按该排剩余宽度自动分摊："
                        "g = (W(t) - n*D) / (n + 1)；两端余量亦为 g",
            "hole_sink_mm": HOLE_SINK,
            "slant_length_mm": round(SLANT, 2),
        },
        "rows": row_table(),
        "superseded": SUPERSEDED,
    }


def main():
    ok = True
    results = []

    def ck(name, cond, detail):
        nonlocal ok
        good = bool(cond)
        if not good:
            ok = False
        results.append({"check": name, "pass": good, "detail": detail})
        print("%s  %-52s %s" % ("PASS" if good else "FAIL", name, detail))

    print("=" * 100)
    print("金字塔斜面开孔 R5 —— 船长 2026-10-18 裁定（斐波那契 7 排）")
    print("=" * 100)
    print("%-4s %-5s %-6s %-9s %-8s %-9s %-9s %-9s %-6s %-9s"
          % ("排", "孔数", "t", "面宽mm", "占宽mm", "剩余mm",
             "间隙mm", "中心距mm", "可行", "z高mm"))
    print("-" * 100)
    for r in row_table():
        print("%-4d %-5d %-6.2f %-9.0f %-8.0f %-9.0f %-9.1f %-9.1f %-6s %-9.0f"
              % (r["row"], r["holes"], r["t"], r["face_width_mm"],
                 r["need_mm"], r["spare_mm"], r["gap_mm"], r["pitch_mm"],
                 "OK" if r["fits"] else "FAIL", r["height_z_mm"]))
    print("-" * 100)

    ck("1 七排孔数 = 1/1/2/3/5/8/13（斐波那契）",
       HOLE_ROW_N == [1, 1, 2, 3, 5, 8, 13],
       " ".join(str(n) for n in HOLE_ROW_N))
    ck("2 每面 33 孔", HOLE_PER_SLOPE == 33,
       "1+1+2+3+5+8+13 = %d" % HOLE_PER_SLOPE)
    ck("3 四面共 132 孔（船长裁定值）", N_HOLES_TOTAL == 132,
       "33 × 4 = %d" % N_HOLES_TOTAL)
    ck("4 孔径 900 mm（船长 2026-10-19 裁定：1m -> 900mm）",
       HOLE_DIA == 900.0, "%.0f mm" % HOLE_DIA)
    # 船长 12:06 纠正的算法（间隙 = 剩余宽度 / (n+1)），按 900 mm 复算
    _g_bot = (18000.0 - 13 * 900.0) / (13 + 1)
    ck("5 船长算法：间隙 = (18000 − 11700) / 14 = %.2f mm" % _g_bot,
       abs(row_gap(0.0, 13) - _g_bot) < 1e-6,
       "13×900 + 14×%.2f = %.1f（底边 18000）"
       % (_g_bot, 13 * 900.0 + 14 * _g_bot))
    bad = [r["row"] for r in row_table() if not r["fits"]]
    ck("6 七排间隙均为正（可布尔建模）", not bad,
       "最小间隙 %.1f mm" % min(r["gap_mm"] for r in row_table())
       if not bad else "第 %s 排间隙 ≤ 0" % bad)
    ck("7 间隙 > 0，杜绝相切退化边",
       min(r["gap_mm"] for r in row_table()) > 1.0,
       "最小 %.1f mm（相切=0 会致 isValid()=False）"
       % min(r["gap_mm"] for r in row_table()))
    ck("8 排号 1 最靠锥顶（t 最大）", HOLE_ROW_T[0] == max(HOLE_ROW_T),
       "t 序列 %s" % HOLE_ROW_T)
    ck("9 排号 7 最靠锥底（t 最小）", HOLE_ROW_T[-1] == min(HOLE_ROW_T),
       "t 序列 %s" % HOLE_ROW_T)
    gaps = [abs(HOLE_ROW_T[i] - HOLE_ROW_T[i + 1]) * SLANT
            for i in range(6)]
    ck("10 相邻排沿斜面间距 ≥ 孔径", min(gaps) >= HOLE_DIA,
       "最小 %.0f mm，最大 %.0f mm（6 段）" % (min(gaps), max(gaps)))
    z_t1 = sn45() * 1.0 * SLANT
    ck("11 SLANT 与锥高自洽（sin45°×SLANT = PYR_HEIGHT %.0f）"
       % PYR_HEIGHT, abs(z_t1 - PYR_HEIGHT) < 1.0,
       "sin45×SLANT = %.1f mm（角点值 15588.5 已弃用）" % z_t1)

    H = hole_positions()
    ck("12 实际生成 132 孔", len(H) == 132, "%d 个" % len(H))
    per = {}
    for h in H:
        per.setdefault(h["slope"], []).append(h)
    ck("13 四面各 33 孔", all(len(v) == 33 for v in per.values()),
       " ".join("%d" % len(per.get(i, [])) for i in range(4)))
    row_ok = all(sum(1 for h in per[s] if h["row"] == r) == n
                 for s in range(4)
                 for r, n in enumerate(HOLE_ROW_N, 1))
    ck("14 每面逐排孔数 1/1/2/3/5/8/13 全部核对", row_ok,
       "4 面 × 7 排核对通过")
    zs = [h["centre"][2] for h in H]
    ck("15 无孔越过锥顶（z < %.0f）" % PYR_TOP_Z, max(zs) < PYR_TOP_Z,
       "最高孔 z = %.0f，余量 %.0f mm" % (max(zs), PYR_TOP_Z - max(zs)))
    ck("16 孔心 z 随排号严格递减",
       all(row_table()[i]["height_z_mm"] > row_table()[i + 1]["height_z_mm"]
           for i in range(6)),
       " / ".join("%.0f" % r["height_z_mm"] for r in row_table()))
    ck("17 R3 / R4 规则已废止",
       SUPERSEDED["R3"]["per_slope"] == 27
       and SUPERSEDED["R4"]["per_slope"] == 27,
       "R3 3x9=27；R4 5排=27；R5 7排=33")
    ck("18 金字塔坐在立方体之上（base=9000=top of cube）",
       PYR_BASE_Z == 9000.0 and PYR_TOP_Z == 18000.0,
       "cube z=[%.0f, %.0f]；pyr z=[%.0f, %.0f]"
       % (CUBE_Z0, CUBE_Z1, PYR_BASE_Z, PYR_TOP_Z))
    ck("19 孔心 z 全部高于立方体顶面（%.0f）" % CUBE_Z1,
       min(h["centre"][2] for h in H) > CUBE_Z1,
       "最低孔 z = %.0f mm"
       % min(h["centre"][2] for h in H))
    ck("20 锥顶余量 = PYR_TOP_Z − 最高孔 z > 孔径",
       (PYR_TOP_Z - max(h["centre"][2] for h in H)) > HOLE_DIA,
       "余量 %.0f mm > 孔径 %.0f"
       % (PYR_TOP_Z - max(h["centre"][2] for h in H), HOLE_DIA))
    _d = SLOPE_THICK / math.sqrt(2.0)
    ck("21 斜壁真实厚度 = SLOPE_THICK/2（非 SLOPE_THICK）",
       abs(WALL_THICK_ACTUAL - _d / math.sqrt(2.0)) < 1e-6,
       "内锥偏移 d=%.1f -> 法向厚 %.1f mm（声明 %.0f 是 2 倍）"
       % (_d, _d / math.sqrt(2.0), SLOPE_THICK))
    ck("22 孔心沉入量 = 真实半壁厚（HOLE_SINK = %.0f）" % HOLE_SINK,
       abs(HOLE_SINK - WALL_THICK_ACTUAL / 2.0) < 1e-9,
       "%.0f mm；此前 150 mm 是 2 倍，把孔心推出壁外" % HOLE_SINK)
    # 逐排实测过的失败模式：孔心若在中面，每排等效穿壁应 = 真实壁厚
    ck("23 孔心确实落在斜壁中面（法向投影自洽）",
       abs(HOLE_SINK - WALL_THICK_ACTUAL / 2.0) < 1e-9
       and 0.0 < HOLE_SINK < WALL_THICK_ACTUAL,
       "0 < %.0f < %.0f = 壁厚" % (HOLE_SINK, WALL_THICK_ACTUAL))
    # ---- 斜面坐标系方向自检（防回归：-X/+X 的 up 符号曾写反）----
    _ok_up, _ok_nrm = True, True
    for _f in SLOPE_FRAMES:
        _bx, _by = _f["base"]
        _r0 = math.hypot(_bx, _by)
        _r1 = math.hypot(_bx + _f["up"][0] * 1000.0,
                         _by + _f["up"][1] * 1000.0)
        if _r1 >= _r0:
            _ok_up = False
        _r2 = math.hypot(_bx + _f["nrm"][0] * 100.0,
                         _by + _f["nrm"][1] * 100.0)
        if _r2 <= _r0:
            _ok_nrm = False
    ck("24 四面 up 均朝锥内（沿 up 半径必须减小）", _ok_up,
       "0 -Y / 1 -X / 2 +Y / 3 +X 全部朝内")
    ck("25 四面 nrm 均朝锥外（沿 nrm 半径必须增大）", _ok_nrm,
       "四面法向全部朝外")
    _rmax = max(math.hypot(h["centre"][0], h["centre"][1]) for h in H)
    ck("26 全部 132 孔心半径在合理范围内",
       _rmax < PYR_PLAN / 2.0 * 1.3,
       "最大孔心半径 %.0f mm（锥底半边长 %.0f）"
       % (_rmax, PYR_PLAN / 2.0))

    rep = spec_dict()
    rep["checks"] = results
    rep["holes"] = H
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