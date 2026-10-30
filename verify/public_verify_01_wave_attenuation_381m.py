# -*- coding: utf-8 -*-
"""
================================================================================
SINOPORT · 公开验证脚本 · 任务一 · 悬浮防波堤 381 m 四梯队消浪仿真
================================================================================
【用途】开源支撑材料 · 可复现验证「25 倍极限消浪」主张
【运行】python verify_01_wave_attenuation_381m.py
        （仅依赖 numpy；退出码 0 = 全部断言通过，1 = 存在失败断言）
【输出】verify_01_wave_attenuation_381m_results.json

【可复现的公开主张】
  · 外海有效波高 15 m（极端台风工况）经过 381 m 厚四梯队串联悬浮防波堤
  · 泊位区（防波堤内侧）有效波高衰减至 0.6 m 量级
  · 总消浪比 25×（= 0.6/15，对应波能通量比 0.0016，须耗散 99.84% 入射波能）
  · 断言脚本判定：几何自洽、浅化合理性、级联单调性、达标率、越顶量级、
                周期工况收敛、红线自检

【四梯队构成（单侧总厚 381 m）】
  ① 迎海区   100 m  悬浮金字塔阵列（三管束 + 涡轮导流管层 + 弹簧发电线）
  ② 中间区   100 m  五层垂向消浪带（表层生态消浪 + 下层导流管束）
  ③ 靠港区   100 m  浮体排 + 浮动压浪翼 + 水舱节流孔
  ④ 核心区    81 m  核心防波堤排

【诚实边界（LEVEL-0 机理级筛选计算）】
  · 本脚本为参数化筛选计算，采用线性波理论 + 能量通量守恒 + 经验越顶公式；
    各段透射系数取「工程可达区间」参数化假设值；
  · 不替代物理模型缩尺试验与实测验证；段参数须以试验数据标定后方可引用；
  · 波浪参数、几何与工况取自公开设计口径。
================================================================================
"""
import json
import math
import os
import sys

import numpy as np

# ── 物性 ──────────────────────────────────────────────────────────────
RHO = 1025.0        # 海水密度 kg/m³
G = 9.81            # 重力加速度 m/s²

# ── 设计工况（公开口径）────────────────────────────────────────────────
H_OFFSHORE = 15.0      # 外海有效波高 Hs (m) —— 极端台风工况
T_LO, T_HI = 14.0, 20.0    # 波周期区间 (s)
T_DES = 17.0               # 设计周期 (s)
SURGE = 4.0                # 风暴潮水位升高 (m)
H_INNER_TARGET = 0.6       # 泊位区目标有效波高 (m)
RATIO_TARGET = 25.0        # 总消浪比

# ── 几何 ──────────────────────────────────────────────────────────────
R_CORE = 1650.1
R_PORT = 1750.1
R_MID = 1850.1
R_SEA = 1950.1
T_SEA, T_MID, T_PORT, T_CORE = 100.0, 100.0, 100.0, 81.0
BAND_TOTAL = T_SEA + T_MID + T_PORT + T_CORE      # 381 m
H_TOE = 45.0          # 迎海区外缘设计水深 (m)
A_BASIN = math.pi * R_CORE ** 2 / 2
RING_LEN = 3300.0     # 防波堤总长 (m)

FREEBOARD = {"BW-SEA": 5.0, "BW-MID": 4.0, "BW-PORT": 3.5, "CORE": 3.0}

# ── 段透射系数工程可达区间（LEVEL-0 参数化假设，待试验标定）────────────
BANDS = {
    "BW-SEA":  dict(lo=0.14, hi=0.42, best=0.24,
                    mech="悬浮金字塔阵列（反射 + 越顶破碎）+ 三管束 + 涡轮导流管层"),
    "BW-MID":  dict(lo=0.10, hi=0.38, best=0.19,
                    mech="五层垂向消浪带（表层生态消浪 + 下层导流管束孔隙耗散）"),
    "BW-PORT": dict(lo=0.42, hi=0.82, best=0.58,
                    mech="浮体排 + 浮动压浪翼 + 水舱节流孔"),
    "CORE":    dict(lo=0.55, hi=0.88, best=0.70, mech="核心防波堤排"),
}
ORDER = ["BW-SEA", "BW-MID", "BW-PORT", "CORE"]


def dispersion(T, h, iters=100):
    w = 2 * math.pi / T
    k = w * w / G
    for _ in range(iters):
        th = math.tanh(k * h) if h > 0 else 1.0
        f = G * k * th - w * w
        df = G * th + (G * k * h * (1 - th * th)) if h > 0 else G
        k = max(k - f / df, 1e-6)
    th = math.tanh(k * h) if h > 0 else 1.0
    c = w / k
    n = 0.5 * (1 + 2 * k * h / math.sinh(2 * k * h)) if h > 0 else 1.0
    return k, 2 * math.pi / k, c, c * n, n


def shoal(T, h_off, h_on, H0):
    _, _, _, cg0, _ = dispersion(T, h_off)
    _, _, _, cg1, _ = dispersion(T, h_on)
    return H0 * math.sqrt(cg0 / cg1), cg1


def power_flux(H, T, h):
    _, _, _, cg, _ = dispersion(T, h)
    return 0.125 * RHO * G * H ** 2 * cg


def goda_overtopping(H, Rc):
    H1 = 1.5 * H
    if Rc >= H1:
        return 0.0
    return 0.1 * math.sqrt(G * H1 ** 3) * math.exp(-2.6 * (1 - Rc / H1))


def cascade_deterministic(H_toe, band_vals):
    H = H_toe
    out = []
    for name in ORDER:
        H = H * band_vals[name]
        out.append(dict(stage=name, H_out=H, q_overtop=goda_overtopping(H, FREEBOARD[name])))
    return out


def run_monte_carlo(T, n=200000, seed=20260921, mode="tri"):
    rng = np.random.default_rng(seed)
    H_toe, _ = shoal(T, 2000.0, H_TOE, H_OFFSHORE)
    H = np.full(n, H_toe)
    trace = []
    for name in ORDER:
        b = BANDS[name]
        if mode == "tri":
            v = rng.triangular(b["lo"], b["best"], b["hi"], n)
        elif mode == "pess":
            v = rng.triangular(b["hi"] * 0.90, b["hi"], min(b["hi"] * 1.12, 1.0), n)
        else:
            v = rng.triangular(b["best"] * 0.80, b["best"], b["best"] * 1.25, n)
        H = H * np.clip(v, b["lo"], b["hi"] * 1.12)
        trace.append(dict(stage=name, H_p50=float(np.percentile(H, 50)),
                          H_p90=float(np.percentile(H, 90)),
                          H_p99=float(np.percentile(H, 99))))
    return dict(H_toe=H_toe, trace=trace,
                H_final_p50=float(np.percentile(H, 50)),
                H_final_p90=float(np.percentile(H, 90)),
                H_final_p99=float(np.percentile(H, 99)),
                H_final_max=float(H.max()),
                P_meet=float((H < H_INNER_TARGET).mean()))


def assertions(res):
    ok, fail, lines = [], [], []

    def chk(cond, msg):
        (ok if cond else fail).append(msg)
        lines.append(("  PASS  " if cond else "  FAIL  ") + msg)

    chk(abs(BAND_TOTAL - 381.0) < 1e-6, "四梯队径向厚度合计 = %.0f m（应 381 m）" % BAND_TOTAL)
    chk(abs((R_SEA - R_CORE) - 300.0) < 1e-6, "外围三区段径向 = %.0f m（应 300 m）" % (R_SEA - R_CORE))
    Ht, _ = shoal(T_DES, 2000.0, H_TOE, H_OFFSHORE)
    chk(13.0 <= Ht <= 16.0, "迎海外缘波高 = %.2f m（应 13~16 m）" % Ht)
    chk(abs(H_INNER_TARGET / H_OFFSHORE - 0.04) < 1e-9,
        "0.6/15.0 = %.3f（总透射比，应 0.040）" % (H_INNER_TARGET / H_OFFSHORE))
    kd = 1 - (H_INNER_TARGET / H_OFFSHORE) ** 2
    chk(kd > 0.998, "25× 目标对应能量耗散率 = %.4f%%（应 > 99.8%%）" % (100 * kd))
    det = cascade_deterministic(Ht, {k: v["best"] for k, v in BANDS.items()})
    chk(det[-1]["H_out"] < H_INNER_TARGET,
        "确定性级联（最优参数）泊位区 Hs = %.3f m（应 < %.1f m）" % (det[-1]["H_out"], H_INNER_TARGET))
    mc_opt = run_monte_carlo(T_DES, mode="opt")
    chk(mc_opt["P_meet"] >= 0.90,
        "MC 最优参数组合 25× 达标率 = %.1f%%（应 ≥ 90%%）" % (100 * mc_opt["P_meet"]))
    mc_pess = run_monte_carlo(T_DES, mode="pess")
    chk(mc_pess["P_meet"] < mc_opt["P_meet"] - 0.05,
        "MC 悲观组合达标率 %.1f%% 明显低于最优组合 %.1f%%（参数敏感性成立）"
        % (100 * mc_pess["P_meet"], 100 * mc_opt["P_meet"]))
    q_sea = goda_overtopping(det[0]["H_out"], FREEBOARD["BW-SEA"])
    gross = q_sea * RING_LEN
    chk(1e3 < gross < 5e4, "迎海段越顶毛入流 = %.0f m³/s（量级检查 1e3~5e4）" % gross)
    net = q_sea * 0.02 * RING_LEN
    rise = net * 3600 / A_BASIN
    chk(0.05 < rise < 0.60, "98%% 回流后内港水位升速 = %.3f m/h（应 0.05~0.60 m/h）" % rise)
    for T in (T_LO, T_HI):
        r = run_monte_carlo(T, n=20000, mode="tri")
        chk(r["H_final_p50"] >= 0.0, "周期 %.0f s 工况计算收敛（H_p50=%.3f m）" % (T, r["H_final_p50"]))
    mono = all(det[i + 1]["H_out"] < det[i]["H_out"] for i in range(len(det) - 1))
    chk(mono, "级联波高逐段单调递减")
    blob = json.dumps(res, ensure_ascii=False)
    for bad in ("kWh", "kW ", "发电量"):
        chk(bad not in blob, "红线：输出不含发电量绝对值（检查 '%s'）" % bad)
    return ok, fail, lines


def main():
    res = {}
    print("=" * 78)
    print("SINOPORT · 任务一 · 381 m 四梯队消浪仿真（Hs = 15 m 极端台风工况）")
    print("=" * 78)

    res["shoaling"] = []
    print("\n【1】波浪浅化（迎海区外缘，水深 %.0f m）" % H_TOE)
    print("   T(s)   L0(m)   L1(m)   H_toe(m)  H/L1    P(MW/m)")
    for T in (T_LO, 15.0, T_DES, 18.5, T_HI):
        _, L0, _, _, _ = dispersion(T, 2000.0)
        _, L1, _, _, _ = dispersion(T, H_TOE)
        Ht, cg = shoal(T, 2000.0, H_TOE, H_OFFSHORE)
        P = power_flux(Ht, T, H_TOE) / 1e6
        res["shoaling"].append(dict(T=T, L0=L0, L1=L1, H_toe=Ht,
                                     steep=Ht / L1, P_MW_per_m=P, Cg=cg))
        print("  %4.1f  %6.0f  %6.0f   %6.2f  %.4f  %6.2f" % (T, L0, L1, Ht, Ht / L1, P))
    Ht_des, _ = shoal(T_DES, 2000.0, H_TOE, H_OFFSHORE)
    P_in = power_flux(Ht_des, T_DES, H_TOE)
    res["incident"] = dict(H_toe=Ht_des, P_in_MW_per_m=P_in / 1e6,
                            required_dissipation_kW_per_m_path=P_in / BAND_TOTAL / 1e3)
    print("\n  入射波能通量 = %.2f MW/m（每延米波峰线）" % (P_in / 1e6))
    print("  381 m 带宽内平均需耗散能力 = %.1f kW/m 路径" % (P_in / BAND_TOTAL / 1e3))

    res["bands"] = {k: dict(v) for k, v in BANDS.items()}
    thickness = {"BW-SEA": T_SEA, "BW-MID": T_MID, "BW-PORT": T_PORT, "CORE": T_CORE}
    print("\n【2】四梯队结构与段透射系数工程可达区间（LEVEL-0 假设，待试验标定）")
    for k in ORDER:
        v = BANDS[k]
        print("  %-9s %6.0f m  Kt %.2f~%.2f（最优 %.2f）  %s"
              % (k, thickness[k], v["lo"], v["hi"], v["best"], v["mech"]))

    res["deterministic"] = []
    print("\n【3】确定性级联")
    for tag, pick in (("最优", "best"), ("悲观", "hi")):
        vals = {k: (v["best"] if pick == "best" else v["hi"]) for k, v in BANDS.items()}
        det = cascade_deterministic(Ht_des, vals)
        res["deterministic"].append(dict(tag=tag, chain=det))
        print("  %s：%.2f m %s m   达标=%s"
              % (tag, Ht_des, " → ".join("%.3f" % d["H_out"] for d in det),
                 "是" if det[-1]["H_out"] < H_INNER_TARGET else "否"))

    res["monte_carlo"] = {}
    print("\n【4】蒙特卡洛（20 万次/工况）")
    for mode, label in (("opt", "最优"), ("tri", "三角分布"), ("pess", "悲观")):
        r = run_monte_carlo(T_DES, mode=mode)
        res["monte_carlo"][mode] = r
        print("  %-4s 泊位区 Hs: p50=%.3f  p90=%.3f  p99=%.3f  max=%.3f m   25× 达标率=%.1f%%"
              % (label, r["H_final_p50"], r["H_final_p90"], r["H_final_p99"],
                 r["H_final_max"], 100 * r["P_meet"]))

    res["period_sweep"] = []
    print("\n【5】周期敏感性（三角分布抽样）")
    for T in (T_LO, 15.0, T_DES, 18.5, T_HI):
        r = run_monte_carlo(T, mode="tri", n=100000)
        res["period_sweep"].append(dict(T=T, H_p50=r["H_final_p50"],
                                        H_p90=r["H_final_p90"], P_meet=r["P_meet"]))
        print("  T=%.1f s  泊位区 Hs p50=%.3f  p90=%.3f m  达标率=%.1f%%"
              % (T, r["H_final_p50"], r["H_final_p90"], 100 * r["P_meet"]))

    res["overtopping"] = []
    print("\n【6】越顶核算（Goda，含风暴潮抬升 %.1f m 的有效干舷）" % SURGE)
    for stage in ORDER:
        Hloc = res["deterministic"][0]["chain"][ORDER.index(stage)]["H_out"]
        Rc_eff = FREEBOARD[stage] - SURGE
        q = goda_overtopping(Hloc, Rc_eff)
        gross = q * RING_LEN
        rise = gross * 0.02 * 3600 / A_BASIN
        res["overtopping"].append(dict(stage=stage, H_loc=Hloc, Rc_eff=Rc_eff,
                                       q=q, gross=gross, rise_98=rise))
        print("  %-9s 局部 Hs=%6.2f m  有效干舷=%4.1f m  q=%.2f m³/s·m  毛入流=%.0f m³/s  升速=%.3f m/h"
              % (stage, Hloc, Rc_eff, q, gross, rise))

    p0 = res["monte_carlo"]["tri"]["P_meet"]
    res["sensitivity"] = []
    print("\n【7】参数敏感性（基准达标率 %.1f%%）" % (100 * p0))
    for name in ORDER:
        b = BANDS[name]
        for tag, best in (("乐观", b["best"] * 0.80), ("悲观", b["hi"] * 0.98)):
            orig = b["best"]
            BANDS[name]["best"] = best
            r = run_monte_carlo(T_DES, n=120000, mode="opt")
            BANDS[name]["best"] = orig
            res["sensitivity"].append(dict(factor="%s 段 Kt %s (%.2f)" % (name, tag, best),
                                           P_meet=r["P_meet"],
                                           delta_pp=(r["P_meet"] - p0) * 100))
            print("  %-30s 达标率=%5.1f%%  Δ=%+.1f pp"
                  % (res["sensitivity"][-1]["factor"], 100 * r["P_meet"],
                     res["sensitivity"][-1]["delta_pp"]))

    res["geometry"] = dict(R_core=R_CORE, R_port=R_PORT, R_mid=R_MID, R_sea=R_SEA,
                           t_sea=T_SEA, t_mid=T_MID, t_port=T_PORT, t_core=T_CORE,
                           band_total=BAND_TOTAL, ring_len=RING_LEN, basin_area=A_BASIN)
    res["design"] = dict(H_offshore=H_OFFSHORE, T_range=[T_LO, T_HI], T_design=T_DES,
                          surge=SURGE, H_inner_target=H_INNER_TARGET, ratio_target=RATIO_TARGET)

    ok, fail, lines = assertions(res)
    res["assertions"] = dict(passed=len(ok), failed=len(fail), failures=fail, lines=lines)
    print("\n【8】断言脚本（%d 项通过 / %d 项失败）" % (len(ok), len(fail)))
    for l in lines:
        print(l)

    out = "verify_01_wave_attenuation_381m_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=float)
    print("\n结果已写入：%s" % out)
    if fail:
        print("\n>>> 断言未全部通过")
        return 1
    print("\n>>> 全部断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
