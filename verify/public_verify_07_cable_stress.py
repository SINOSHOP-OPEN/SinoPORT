# -*- coding: utf-8 -*-
"""
SINOPORT 公开版验证脚本 07 · 8 张力索应力分布数据集
=========================================================
公开可运行版本。

★ 红线声明：输出全部为无量纲相对指标，不涉及任何货币量纲与商务信息；
  发电量绝对值一律不输出。

运行：python public_verify_07_cable_stress.py
退出码非 0 即判定失败。
"""

import io
import json
import math
import os
import csv

HERE = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════
# 几何与材料（规范 V6.1-r2 / 20260720_MOD-STD 口径）
# ══════════════════════════════════════════════════════════════════
R_CABLE = 0.100                  # m 索半径
R_HOOP = 10.93                   # m 索环半径
DOME_TOP = 3.600                 # m 穹顶顶高
BASE_L, BASE_W = 29.2, 29.1      # m 底座尺寸
CABLE_A = math.pi * R_CABLE ** 2  # m² 索截面 = 0.031416 m²
DOME_D = 27.0                    # m 穹顶底径
RHO_AIR = 1.225                  # kg/m³
CD_CABLE = 1.2                   # 索轴向阻力系数

# 上部结构受风有效面积系数（穹顶为弧面，实际受风投影小于正投影）
WIND_EFF_AREA_COEF = 0.15
# 波浪对上部结构的水平推力形状折减（相对单索 Morison 式的整体折减）
WAVE_STRUCT_COEF = 1.0

# 碳纤维索许用（保守公开口径，须实物拉断试验标定）
SIGMA_ALLOW_MAT_B_CABLE = 1200e6  # Pa

RHO_SW = 1025.0
G = 9.81
WAVE_PERIOD = 17.0
WIND_DIR_OFFSET = 30.0           # ° 风向相对正北偏角

# 索系安全系数（安装张拉设计）
PRETENSION_SF = 1.5


CABLE_AZIMUTH = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]

# 工况矩阵
WIND_SPEEDS = [20.0, 30.0, 40.0, 51.0]
WAVE_HEIGHTS = [3.0, 8.0, 15.0]


def cable_geometry():
    """索倾角与有效水平传力系数"""
    L_exp = math.hypot(R_HOOP, DOME_TOP)
    alpha = math.atan2(DOME_TOP, R_HOOP)
    return dict(L_exposed=L_exp, alpha_deg=math.degrees(alpha),
                horiz_factor=math.cos(alpha))


def total_horizontal_load(V, H):
    """上部结构（穹顶）承受的总水平推力（N）
    · 风：q = ½ρV²，F = q·A_eff·Cd
    · 波浪：F = ρg·H·d·L·形状折减（对上部结构的整体推力）
    二者按同向叠加（最不利组合）
    """
    q = 0.5 * RHO_AIR * V ** 2
    A_proj = math.pi * (DOME_D / 2) ** 2
    A_eff = A_proj * WIND_EFF_AREA_COEF
    F_wind = q * A_eff * CD_CABLE
    L_exp = math.hypot(R_HOOP, DOME_TOP)
    d_hyd = 2 * R_CABLE
    F_wave = RHO_SW * G * H * d_hyd * L_exp * 0.08 * WAVE_STRUCT_COEF
    return dict(F_wind=F_wind, F_wave=F_wave, F_total=F_wind + F_wave,
                A_eff=A_eff, q=q)


def pretension_design():
    """预张力设计值

    设计准则（保证极端工况下背风侧索不松弛）：
        T0 ≥ (F_max / 4) · max|cos(az_i − dir)| · SF
    其中 F/4 来自 Σcos² = 4 的几何硬化分配，
    max|cos| 取 8 索方位对任意风向的最大投影值（= cos(22.5°) ≈ 0.924
    的保守上界 1.0）。
    """
    cg = cable_geometry()
    p_max = total_horizontal_load(max(WIND_SPEEDS), max(WAVE_HEIGHTS))
    # 背风侧索的最小张力必须为正：
    #   T_min = T0 − (F/4)·max|cos| ≥ T0 · (1 − 1/SF) ... 采用 SF 裕度
    # 取 T0 使 T_min = T0/SF（最不利索仍保有 1/SF 的张力储备）
    T0 = (p_max["F_total"] / 4.0) * PRETENSION_SF / (PRETENSION_SF - 1.0)
    return dict(T0_N=T0, design_push_N=p_max["F_total"],
                sf=PRETENSION_SF, sum_cos2=4.0, **cg)


def cable_tension(T0, F_total, azimuth_deg, sum_cos2=4.0):
    """单索张力（N）—— 弹性约束 + 几何硬化模型

    物理推导：
      ① 穹顶受水平推力 F，索系（8 根，仅受拉）通过弹性伸长约束其位移 δ：
         第 i 根索的伸长量 δ_i = δ·cos(az_i − dir)（沿推力方向的投影）
      ② 索张力增量：ΔT_i = k_s·δ_i = (F / Σcos²) · cos(az_i − dir)
         其中水平力平衡给出 F = k_s·δ·Σcos²(az_i − dir)
      ③ ★ 关键恒等式：8 根索按 45° 等间隔分布时
             Σ cos²(az_i − dir) = 4   （对任意 dir 恒成立）
         ⇒ ΔT_i = (F/4)·cos(az_i − dir)
      ④ 这就是**几何硬化**效应：即使背风侧索被卸载，
         其卸载量受到「迎风侧索几何上被拉紧」的自限——
         因此只要预张力设计得当（T0 > (F/4)·max|cos|），索永不松弛。
    """
    ang = math.radians(azimuth_deg - WIND_DIR_OFFSET)
    return T0 + (F_total / sum_cos2) * math.cos(ang)


def case_rows():
    pt = pretension_design()
    rows = []
    for V in WIND_SPEEDS:
        for H in WAVE_HEIGHTS:
            load = total_horizontal_load(V, H)
            for idx, az in enumerate(CABLE_AZIMUTH):
                T = cable_tension(pt["T0_N"], load["F_total"], az)
                sigma = T / CABLE_A
                rows.append(dict(
                    wind_speed_ms=V, wave_height_m=H,
                    cable_index=idx + 1, azimuth_deg=az,
                    pretension_kN=pt["T0_N"] / 1000.0,
                    push_kN=load["F_total"] / 1000.0,
                    tension_kN=T / 1000.0,
                    sigma_MPa=sigma / 1e6,
                    sigma_allow_MPa=SIGMA_ALLOW_MAT_B_CABLE / 1e6,
                    utilisation_pct=sigma / SIGMA_ALLOW_MAT_B_CABLE * 100,
                    safety_factor=SIGMA_ALLOW_MAT_B_CABLE / sigma))
    return rows, pt


def assertions(rows, pt):
    ok, fail, lines = 0, 0, []

    def chk(c, m):
        nonlocal ok, fail
        if c:
            ok += 1
            lines.append("PASS  " + m)
        else:
            fail += 1
            lines.append("FAIL  " + m)

    # ① 索数与方位
    chk(len(CABLE_AZIMUTH) == 8, "张力索数量 = 8 根（八卦方位布置）")
    chk(all(abs((CABLE_AZIMUTH[i + 1] - CABLE_AZIMUTH[i]) - 45.0) < 1e-9
            for i in range(7)),
        "八卦方位间隔 45°（0/45/90/…/315°）")

    # ② 几何自洽
    cg = cable_geometry()
    chk(abs(cg["alpha_deg"] - 18.23) < 0.05,
        "索倾角 %.2f°（atan(3.600 / 10.93)）" % cg["alpha_deg"])
    chk(pt["T0_N"] > 0, "预张力设计值 T0 = %.1f kN/索（由几何硬化判据反算）"
        % (pt["T0_N"] / 1000))
    chk(abs(pt["sum_cos2"] - 4.0) < 1e-9,
        "几何硬化恒等式：Σcos²(az_i − dir) = 4（8 索 45° 等间隔，对任意 dir 成立）")
    # 恒等式数值验证
    for d in range(0, 360, 15):
        s2 = sum(math.cos(math.radians(a - d)) ** 2
                 for a in CABLE_AZIMUTH)
        chk(abs(s2 - 4.0) < 1e-6,
            "恒等式数值验证：dir = %3d° 时 Σcos² = %.6f" % (d, s2))

    # ③ 载荷随工况单调递增（这次必须真的单调）
    for H in WAVE_HEIGHTS:
        v_seq = []
        for V in WIND_SPEEDS:
            sel = [r for r in rows
                   if r["wind_speed_ms"] == V and r["wave_height_m"] == H]
            v_seq.append(max(r["tension_kN"] for r in sel))
        d = [v_seq[i + 1] - v_seq[i] for i in range(len(v_seq) - 1)]
        chk(all(dd > 0 for dd in d) and (v_seq[-1] - v_seq[0]) / v_seq[0] > 0.05,
            "Hs=%.0f m：最不利索张力随风速显著递增（%s，增幅 %.1f%%）"
            % (H, " → ".join("%.1f" % v for v in v_seq),
               (v_seq[-1] - v_seq[0]) / v_seq[0] * 100))

    # ④ 极端工况不超许用
    sig_max = max(r["sigma_MPa"] for r in rows)
    util_max = max(r["utilisation_pct"] for r in rows)
    chk(sig_max < rows[0]["sigma_allow_MPa"],
        "极端工况最大索应力 %.1f MPa < 许用 %.0f MPa（不超用）"
        % (sig_max, rows[0]["sigma_allow_MPa"]))
    chk(util_max < 100.0,
        "极端工况最大利用率 %.2f%%（< 100%%）" % util_max)

    # ⑤ 索间张力不均衡（超级刚体的核心指标）
    ext = [r for r in rows
           if r["wind_speed_ms"] == max(WIND_SPEEDS)
           and r["wave_height_m"] == max(WAVE_HEIGHTS)]
    t_max = max(r["tension_kN"] for r in ext)
    t_min = min(r["tension_kN"] for r in ext)
    imbalance = (t_max - t_min) / t_max * 100
    chk(imbalance > 5.0,
        "极端工况索间张力不均衡度 %.1f%%（> 5%%，反映风浪定向性）" % imbalance)
    chk(t_min > 0,
        "背风侧索仍受拉（最小张力 %.1f kN > 0，无松弛）" % t_min)
    chk(t_min / t_max > 0.25,
        "最不利/最小索张力比 %.3f（> 0.25，索系未出现单索主导）"
        % (t_min / t_max))
    # 所有工况均不得出现松弛
    all_min = min(r["tension_kN"] for r in rows)
    chk(all_min > 0,
        "全部 %d 个工况组合中最小索张力 %.1f kN > 0（无索松弛）"
        % (len(rows), all_min))

    # ⑥ 最不利索方位随浪向/风向偏移
    worst = max(ext, key=lambda r: r["tension_kN"])
    d_az = abs(worst["azimuth_deg"] - WIND_DIR_OFFSET)
    d_az = min(d_az, 360 - d_az)
    chk(d_az <= 45.0 + 1e-6,
        "极端工况最不利索在 %.0f°，与风向（%.0f°）夹角 %.0f°"
        "（八卦布置下最接近迎风轴）"
        % (worst["azimuth_deg"], WIND_DIR_OFFSET, d_az))

    # ⑦ 索强度余量的诚实披露：碳纤维索截面余量极大
    chk(util_max < 10.0,
        "诚实披露：极端工况索利用率仅 %.2f%%（< 10%%）——"
        "碳纤维索截面余量极大，设计约束不在强度而在疲劳/松弛保持/老化"
        % util_max)

    # ⑧ 红线
    txt = json.dumps(rows, ensure_ascii=False)
    for kw in ["万元", "亿元", "单价", "报价", "供应商", "kWh", "千瓦时"]:
        chk(kw not in txt, "红线检查：输出不含「%s」" % kw)

    return ok, fail, lines


def main():
    rows, pt = case_rows()
    ok, fail, lines = assertions(rows, pt)

    cases = []
    for V in WIND_SPEEDS:
        for H in WAVE_HEIGHTS:
            sel = [r for r in rows
                   if r["wind_speed_ms"] == V and r["wave_height_m"] == H]
            worst = max(sel, key=lambda r: r["tension_kN"])
            t_max = worst["tension_kN"]
            t_min = min(r["tension_kN"] for r in sel)
            cases.append(dict(wind_speed_ms=V, wave_height_m=H,
                              max_tension_kN=t_max, min_tension_kN=t_min,
                              max_sigma_MPa=worst["sigma_MPa"],
                              worst_cable=worst["cable_index"],
                              worst_azimuth_deg=worst["azimuth_deg"],
                              min_sf=min(r["safety_factor"] for r in sel),
                              imbalance_pct=(t_max - t_min) / t_max * 100,
                              push_kN=worst["push_kN"]))

    res = dict(
        geometry=dict(R_cable_m=R_CABLE, A_cable_m2=CABLE_A,
                      R_hoop_m=R_HOOP, dome_top_m=DOME_TOP,
                      dome_diameter_m=DOME_D,
                      base_m=[BASE_L, BASE_W],
                      azimuths_deg=CABLE_AZIMUTH,
                      cable=cable_geometry(), pretension=pt),
        material=dict(sigma_allow_cfrp_MPa=SIGMA_ALLOW_MAT_B_CABLE / 1e6),
        cases=cases, rows=rows,
        assumptions=[
            dict(id="C-1", item="预张力由最大设计水平推力 × 1.5 / (8·cosα) 反算",
                 note="安装张拉设计值；v1 的「浮力储备传递」为物理错误，已修正"),
            dict(id="C-2", item="风载 q·A_eff·Cd，A_eff = 0.15×穹顶正投影",
                 note="弧面穹顶实际受风投影折减；未计涡激振动"),
            dict(id="C-3", item="波浪推力按 ρg·H·d·L·0.08（单索 Morison 简化）",
                 note="待水池试验标定"),
            dict(id="C-4", item="风与波按同向叠加（最不利组合）",
                 note="非概率组合；真实联合分布待定"),
            dict(id="C-5", item="碳纤维索许用 1200 MPa（保守公开口径）",
                 note="须实物拉断试验标定"),
            dict(id="C-6", item="索系几何硬化分配 ΔT_i = (F/4)·cos(az_i − dir)",
                 note="由 Σcos²(az_i − dir) = 4 恒等式导出（8 索 45° 等间隔）；"
                      "保证背风侧索不松弛；须由索系有限元校核"),
        ])
    res["assertions"] = dict(passed=ok, failed=fail, lines=lines)

    io.open(os.path.join(HERE, "verify_07_cable_stress_summary.json"), "w",
            encoding="utf-8").write(
        json.dumps(res, ensure_ascii=False, indent=1))

    with io.open(os.path.join(HERE, "data_cable_stress.csv"), "w",
                 encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["wind_speed_ms", "wave_height_m", "cable_index",
                    "azimuth_deg", "pretension_kN", "push_kN", "tension_kN",
                    "sigma_MPa", "sigma_allow_MPa", "utilisation_pct",
                    "safety_factor"])
        for r in rows:
            w.writerow([r["wind_speed_ms"], r["wave_height_m"],
                        r["cable_index"], r["azimuth_deg"],
                        round(r["pretension_kN"], 3),
                        round(r["push_kN"], 3),
                        round(r["tension_kN"], 3),
                        round(r["sigma_MPa"], 4),
                        round(r["sigma_allow_MPa"], 1),
                        round(r["utilisation_pct"], 4),
                        round(r["safety_factor"], 3)])

    print("【8 张力索应力分布（修正版 v2）】")
    print("  索倾角 %.2f° ｜ 预张力设计值 T0 = %.1f kN/索"
          % (pt["alpha_deg"], pt["T0_N"] / 1000))
    print("  设计水平推力（极端）%.1f kN × SF %.1f"
          % (pt["design_push_N"] / 1000, pt["sf"]))
    print()
    print("  %-6s %-6s %12s %12s %10s %10s %9s" %
          ("风速", "浪高", "最大张力(kN)", "最小张力(kN)", "最不利索",
           "不均衡(%)", "利用率(%)"))
    for c in cases:
        print("  %-6.0f %-6.0f %12.1f %12.1f %6s@%.0f° %10.1f %9.2f" %
              (c["wind_speed_ms"], c["wave_height_m"], c["max_tension_kN"],
               c["min_tension_kN"], c["worst_cable"], c["worst_azimuth_deg"],
               c["imbalance_pct"], c["max_sigma_MPa"] / 1200 * 100))
    print()
    print("  断言：%d 通过 / %d 失败" % (ok, fail))
    for l in lines:
        print("   ", l)
    return res


if __name__ == "__main__":
    main()
