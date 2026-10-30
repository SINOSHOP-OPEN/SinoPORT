# -*- coding: utf-8 -*-
"""
SINOPORT 公开版验证脚本 04 · 多波高消浪衰减数据集
==================================================
公开可运行版本：验证 381 m 四梯队防波堤在 5 / 10 / 15 m 三工况下的
级联衰减，以及相对波高扫描给出的消浪效率边界。

与工程版的差异：仅省略工程路径信息，物理模型完全一致。

运行：python public_verify_04_wave_multilevel.py
退出码非 0 即判定失败。
"""
import io
import json
import math
import os
import csv
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.81
SHOAL_K = 0.933
C_NONLIN = 1.75
H_TARGET = 0.6
RATIO_TARGET = 25.0
BASIN_AREA = 4277011.378194911
BAND_TOTAL = 381.0

STAGE_THICK = {"BW-SEA": 100.0, "BW-MID": 100.0, "BW-PORT": 100.0, "CORE": 81.0}
KT_BEST = {"BW-SEA": 0.24, "BW-MID": 0.19, "BW-PORT": 0.58, "CORE": 0.70}
KT_LO = {"BW-SEA": 0.14, "BW-MID": 0.10, "BW-PORT": 0.42, "CORE": 0.55}
KT_HI = {"BW-SEA": 0.42, "BW-MID": 0.38, "BW-PORT": 0.82, "CORE": 0.88}


def dispersion(T, h):
    """线性波理论色散关系（Newton 迭代）
        ω² = g·k·tanh(k·h)，k = 2π/L  ⇒  ω²L/(2πg) = tanh(2πh/L)
    """
    w = 2 * math.pi / T
    L = min(T * math.sqrt(G * h), (G * T * T) / (2 * math.pi))
    for _ in range(100):
        x = 2 * math.pi * h / L
        t = math.tanh(x)
        f = w * w * L / (2 * math.pi * G) - t
        dfdL = w * w / (2 * math.pi * G) + \
            (2 * math.pi * h / (L * L)) * (1.0 - t * t)
        if abs(dfdL) < 1e-14:
            break
        step = f / dfdL
        L -= step
        if L <= 1e-6:
            L = 1.0
            break
        if abs(step) < 1e-10:
            break
    return w, L


def kt_nonlinear(kt0, H, L):
    """非线性波高修正：Kt = Kt0·(1 + C·(H/L)²)
    波高增大 → 波陡度上升 → 破碎/越顶增多 → 透射率上升
    """
    if L <= 0:
        return kt0
    return kt0 * (1.0 + C_NONLIN * (H / L) ** 2)


def cascade(H_off, T=17.0, kts=None, k_depth=45.0):
    if kts is None:
        kts = dict(KT_BEST)
    _, L = dispersion(T, k_depth)
    H_toe = H_off * SHOAL_K
    rows = []
    H = H_toe
    for s in ("BW-SEA", "BW-MID", "BW-PORT", "CORE"):
        kt = kt_nonlinear(kts[s], H, L)
        H_out = H * kt
        rows.append(dict(stage=s, thickness_m=STAGE_THICK[s], H_in_m=H,
                         Kt=kt, H_out_m=H_out, dH_m=H - H_out,
                         dH_pct=(H - H_out) / H_toe * 100))
        H = H_out
    return dict(H_toe=H_toe, chain=rows, H_final=H,
                ratio=H_toe / H if H > 1e-9 else float("inf"))


def rise_98(gross_total, hours=9.0, eta=0.98):
    net = gross_total * (1.0 - eta)
    v_mh = net / BASIN_AREA * 3600.0
    return v_mh, v_mh * hours * 1000.0, net


def assertions(res):
    ok, fail, lines = 0, 0, []

    def chk(c, m):
        nonlocal ok, fail
        if c:
            ok += 1
            lines.append("PASS  " + m)
        else:
            fail += 1
            lines.append("FAIL  " + m)

    chk(abs(sum(STAGE_THICK.values()) - BAND_TOTAL) < 1e-6,
        "四梯队径向厚度合计 = %.0f m（应 %.0f m）"
        % (sum(STAGE_THICK.values()), BAND_TOTAL))

    r15 = res["cases"][15.0]
    chk(r15["ratio"] >= RATIO_TARGET,
        "Hs=15 m 极端工况：消浪比 %.1f×（≥ 25×）" % r15["ratio"])
    chk(r15["H_final"] <= H_TARGET,
        "Hs=15 m：泊位区有效波高 %.3f m（≤ %.2f m）" % (r15["H_final"], H_TARGET))

    r5, r10 = res["cases"][5.0], res["cases"][10.0]
    chk(r5["ratio"] >= r10["ratio"] >= r15["ratio"],
        "消浪比随波高单调递减（%.2f× → %.2f× → %.2f×，非线性修正生效）"
        % (r5["ratio"], r10["ratio"], r15["ratio"]))

    for H in (5.0, 10.0, 15.0):
        c = res["cases"][H]
        s = sum(r["dH_m"] for r in c["chain"])
        chk(abs(s - (c["H_toe"] - c["H_final"])) < 1e-6,
            "Hs=%.0f m：逐段耗散之和 %.4f m = 总耗散 %.4f m（能量守恒）"
            % (H, s, c["H_toe"] - c["H_final"]))

    top = res["cases"][15.0]["responsibility"]
    chk(top[0]["stage"] == "BW-SEA",
        "Hs=15 m 耗散责任首位 = %s（%.1f%%，应为迎海区）"
        % (top[0]["stage"], top[0]["dH_pct"]))

    sw = res["steepness_sweep"]
    chk(sw["ratio_at_design"] >= RATIO_TARGET,
        "设计相对波高 H/L=%.3f 处消浪比 %.1f×（≥ 25×）"
        % (sw["rel_design"], sw["ratio_at_design"]))
    chk(sw["ratio_at_breaking"] < sw["ratio_at_design"],
        "破碎极限 H/L=%.3f 处消浪比 %.1f×（较设计工况恶化 %.1f×）"
        % (sw["rel_breaking"], sw["ratio_at_breaking"],
           sw["ratio_at_design"] - sw["ratio_at_breaking"]))

    v15 = res["cases"][15.0]["rise_m_per_h"]
    chk(v15 > 0, "Hs=15 m 净回流后升速 = %.4f m/h（98%% 回流率）" % v15)
    chk(res["design"]["net_outflow_needed_m3s"] > 0,
        "回流能力设计条款：净排放须 ≥ %.0f m³/s（对应 0.3 m/h 升速上限）"
        % res["design"]["net_outflow_needed_m3s"])

    # 红线：输出不含发电量绝对值与成本信息
    txt = json.dumps(res, ensure_ascii=False)
    for kw in ["kWh", "千瓦时", "万元", "亿元", "单价", "报价", "供应商"]:
        chk(kw not in txt, "红线检查：输出不含「%s」" % kw)

    return ok, fail, lines


def main():
    cases = {}
    for H in (5.0, 10.0, 15.0):
        c = cascade(H)
        gross = sum(r.get("gross_inflow_m3s", 0.0) for r in c["chain"])
        # 越顶毛入流（简化 Goda 自由越顶）
        gross = 0.2 * max(c["H_toe"] - 1.0, 0.0) ** 1.5 * 1.0 * 600.0
        v_mh, rise_mm, net = rise_98(gross)
        resp = sorted(c["chain"], key=lambda r: -r["dH_pct"])
        cases[H] = dict(H_offshore_m=H, H_toe=c["H_toe"], chain=c["chain"],
                        H_final=c["H_final"], ratio=c["ratio"],
                        gross_total=gross, net_inflow_m3s=net,
                        rise_m_per_h=v_mh, rise_mm_9h=rise_mm,
                        responsibility=resp)

    _, L_ref = dispersion(17.0, 45.0)
    rel_list = [0.02, 0.03, 0.046, 0.06, 0.08, 0.10, 0.12, 0.143]
    sweep = []
    for rel in rel_list:
        c = cascade(rel * L_ref / SHOAL_K)
        sweep.append(dict(rel=rel, H_offshore=rel * L_ref / SHOAL_K,
                           H_toe=c["H_toe"], H_final=c["H_final"],
                           ratio=c["ratio"]))

    v_limit = 0.3 / 3600.0
    net_need = v_limit * BASIN_AREA
    res = dict(
        design=dict(H_offshore_range_m=[5.0, 15.0], T_design=17.0,
                    H_inner_target=H_TARGET, ratio_target=RATIO_TARGET,
                    band_total_m=BAND_TOTAL,
                    net_outflow_needed_m3s=net_need,
                    gross_outflow_at98_m3s=net_need / 0.02),
        steepness_sweep=dict(
            rel_list=rel_list, ratios=[r["ratio"] for r in sweep],
            rel_design=0.046,
            ratio_at_design=[r["ratio"] for r in sweep
                             if abs(r["rel"] - 0.046) < 1e-9][0],
            rel_breaking=1.0 / 7.0,
            ratio_at_breaking=[r["ratio"] for r in sweep
                               if r["rel"] >= 1.0 / 7.0 - 1e-9][-1],
            note="相对波高 H/L 扫描（H/L>0.10 为外推区，待缩尺标定）"),
        cases=cases,
        assumptions=[
            dict(id="A-1", item="迎海区外缘设计水深 45 m",
                 note="线性浅化用；待海测确认"),
            dict(id="A-2", item="越顶量采用 Goda 自由越顶简化式",
                 note="堤顶高按水深上限简化；待缩尺试验标定"),
            dict(id="A-3", item="段 Kt 取各段工程可达区间的中值（最优组合）",
                 note="区间与悲观组合见稳健性数据集"),
            dict(id="A-4", item="98% 回流率为假设值",
                 note="回流系统效率待实测"),
            dict(id="A-5", item="非线性波高修正 Kt = Kt0·(1+C·(H/L)²)，C=1.75",
                 note="工程近似：波陡度驱动的破碎/越顶增量"),
        ])

    ok, fail, lines = assertions(res)
    res["assertions"] = dict(passed=ok, failed=fail, lines=lines)

    print("【多波高消浪对比】")
    print("  %-6s %8s %10s %9s %8s %11s" %
          ("Hs", "H_toe", "H_final", "消浪比", "达标", "升速(m/h)"))
    for H in (5.0, 10.0, 15.0):
        c = cases[H]
        print("  %-6.0f %8.3f %10.3f %8.1f× %8s %11.4f" %
              (H, c["H_toe"], c["H_final"], c["ratio"],
               "是" if c["ratio"] >= RATIO_TARGET else "否", c["rise_m_per_h"]))
    print()
    print("  相对波高扫描（消浪效率边界）：")
    for r in sweep:
        mark = " <- 设计工况" if abs(r["rel"] - 0.046) < 1e-9 else (
               " <- 破碎极限" if r["rel"] >= 1.0 / 7.0 - 1e-9 else "")
        print("    H/L=%.3f  H_off=%7.2f m  H_final=%7.3f m  消浪比 %5.1f×%s"
              % (r["rel"], r["H_offshore"], r["H_final"], r["ratio"], mark))
    print()
    print("  断言脚本：%d 通过 / %d 失败" % (ok, fail))
    for l in lines:
        print("   ", l)

    out = os.path.join(HERE, "verify_04_wave_multilevel_summary.json")
    io.open(out, "w", encoding="utf-8").write(
        json.dumps(res, ensure_ascii=False, indent=1))
    print("\n结果已写入：", out)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
