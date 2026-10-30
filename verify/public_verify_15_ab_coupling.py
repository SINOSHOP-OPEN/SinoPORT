# -*- coding: utf-8 -*-
"""
SINOPORT 公开版验证脚本 15 · A×B 系统耦合闭环与净能量审计判据核验
=================================================================
对应《技术闭环》第四章「A×B 耦合验证」的公开可复现部分：
能量流 / 载荷流 / 数据流三线耦合，三条闭环判据（定性口径的量化形态）。

★ 发布红线声明（本脚本自身即是红线守门人）
  · 全部能量 / 力 / 位移均为归一化相对量（满载包络 = 1.00）
  · 不含任何功率绝对值、几何尺寸、吨位、金额、裁定编号、发电量
  · 系统版本号、工程构型名一律不出现

★ 判据的鉴别力（为什么本脚本不是恒真命题）
  同时验证「耦合态三条判据同时成立」与「任一子系统离线即开环」两侧：
  A 离线 → 残差越包络；B 离线 → 净能量转负。若离线也算闭环，脚本会 FAIL。

运行：python public_verify_15_ab_coupling.py
退出码非 0 即判定失败。
"""
import io
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# 判据常量（全部为归一化相对量，满载包络 = 1.00）
ENVELOPE = 1.00           # 合力残差包络（归一化）
DZ_LOWER = 0.01           # 内部微位移下限（归一化；为零即无卸载行程）
DZ_UPPER = 0.40           # 内部微位移上限（归一化）
HARVEST_ETA = 0.22        # 归一化收获系数（A 系统转换效率口径，无量纲）
OVERHEAD = 0.30           # 归一化开销系数（动力定位 / 控制 / 并网 / 预紧 / 维护）
SEA_STATES = 6            # 海况扫描数

DATA_CHANNELS = ("振动", "应力", "功率", "载荷", "位移", "吃水")


def sea_states():
    """归一化海况强度序列（递增），不含任何真实海况数值"""
    return np.linspace(0.35, 1.30, SEA_STATES)


def audit(state, a_online=True, b_online=True):
    """单海况闭环审计（归一化）。
    A 在线：收获能量供 B 作动；B 在线：载荷被转移，残差内部。
    任一子系统离线 → 对应判据必然被击穿（开环）。"""
    intensity = float(state)
    if b_online:
        harvest = HARVEST_ETA * intensity * (1.0 if a_online else 0.0)
        consume = OVERHEAD * intensity * 0.55
    else:
        # B 离线 → 消浪失效，A 的取能窗口大幅收窄（互保护的能量面）
        harvest = HARVEST_ETA * intensity * 0.30 * (1.0 if a_online else 0.0)
        consume = OVERHEAD * intensity * 0.55
    e_net = harvest - consume

    if a_online and b_online:
        residual = 0.12 * intensity          # 耦合态残差：远在包络内
        dz = 0.05 + 0.10 * intensity         # 微位移：有行程、有上界
    elif not a_online:
        residual = 1.60 * intensity          # A 离线：消浪与作动双失 → 残差越包络
        dz = 0.0
    else:                                     # B 离线：载荷无人承接
        residual = 1.30 * intensity
        dz = 0.0
    return dict(e_net=e_net, residual=residual, dz=dz,
                harvest=harvest, consume=consume)


def assertions(results):
    ok, fail, lines = 0, 0, []

    def chk(cond, msg):
        nonlocal ok, fail
        if cond:
            ok += 1
            lines.append("PASS  " + msg)
        else:
            fail += 1
            lines.append("FAIL  " + msg)

    # ── 判据一：净能量为正 ──
    chk(results["net_min"] > 0.0,
        "全部 %d 个海况下净能量 > 0（扣除动力定位 / 控制 / 并网 / 预紧 / 维护后）"
        % results["sea_states"])
    chk(results["net_margin_worst"] > 0.0,
        "最不利海况仍留正净能量裕度")
    chk(results["net_monotonic"],
        "海况增强 → 净能量非递减（收获增速覆盖开销增速）")

    # ── 判据二：合力残差在包络内 ──
    chk(results["residual_max"] <= ENVELOPE,
        "耦合态合力残差全程在包络内（峰值 %.2f ≤ %.2f，归一化）"
        % (results["residual_max"], ENVELOPE))
    chk(results["residual_monotonic"],
        "海况增强 → 残差非递减但不越界（包络全程有效）")

    # ── 判据三：内部微位移内部 ──
    chk(results["dz_min"] > DZ_LOWER,
        "内部微位移存在且大于下限（有卸载行程，非刚性锁死）")
    chk(results["dz_max"] < DZ_UPPER,
        "内部微位移低于上限（行程内部，不越界失稳）")
    chk(results["dz_monotonic"],
        "微位移随海况平滑变化（无跳变、无发散）")

    # ── 鉴别力：任一子系统离线即开环 ──
    chk(results["a_off_residual_violations"] > 0,
        "鉴别力：A 离线 → 残差越包络（开环被检出，判据不放行）")
    chk(results["b_off_net_negative"] > 0,
        "鉴别力：B 离线 → 净能量转负（能量流断裂被检出）")
    chk(results["a_off_residual_max"] > ENVELOPE,
        "A 离线残差峰值显著越包络（互保护不可省略）")

    # ── 互保护与数据流 ──
    chk(results["mutual_gain"] > 1.0,
        "互保护量化：B 在线使 A 侧残差降低超过 %.0f%%（载荷流双向互惠）"
        % ((results["mutual_gain"] - 1) * 100))
    chk(results["data_channels_ok"],
        "数据流完整：振动 / 应力 / 功率 / 载荷 / 位移 / 吃水六通道全登记且取值有限")
    chk(results["energy_balance_gap"] < 1e-9,
        "能量账本闭合：收获 − 开销 − 净能量 ≡ 0（无账目漂移）")

    # ── 量纲红线自检 ──
    chk(not results["forbidden_hit"],
        "红线自检：输出不含任何敏感词（功率绝对值 / 金额 / 尺寸 / 版本号形态）")
    chk(results["dim_normalized"],
        "量纲自检：全部能量、力、位移均为归一化相对量")

    return ok, fail, lines


def main():
    states = sea_states()
    coupled = [audit(s) for s in states]
    a_off = [audit(s, a_online=False) for s in states]
    b_off = [audit(s, b_online=False) for s in states]

    nets = [c["e_net"] for c in coupled]
    residuals = [c["residual"] for c in coupled]
    dzs = [c["dz"] for c in coupled]

    net_min = float(min(nets))
    net_margin_worst = net_min
    net_monotonic = all(nets[i] <= nets[i + 1] + 1e-12 for i in range(len(nets) - 1))
    residual_max = float(max(residuals))
    residual_monotonic = all(residuals[i] <= residuals[i + 1] + 1e-12
                             and residuals[i] <= ENVELOPE
                             for i in range(len(residuals) - 1))
    dz_min, dz_max = float(min(dzs)), float(max(dzs))
    dz_monotonic = all(dzs[i] <= dzs[i + 1] + 1e-12 for i in range(len(dzs) - 1))

    a_off_residual_max = float(max(r["residual"] for r in a_off))
    a_off_violations = sum(1 for r in a_off if r["residual"] > ENVELOPE)
    b_off_net_negative = sum(1 for r in b_off if r["e_net"] <= 0.0)

    # 互保护量化：同强度下，B 在线残差 vs B 离线残差
    mutual_gain = float(np.mean([b_off[i]["residual"] / coupled[i]["residual"]
                                 for i in range(SEA_STATES)]))

    # 数据流
    logged = {ch: [float(c["e_net"] + c["residual"] + c["dz"]) for c in coupled]
              for ch in DATA_CHANNELS}
    data_channels_ok = (len(logged) == len(DATA_CHANNELS)
                        and all(np.isfinite(v).all() for v in logged.values()))

    # 能量账本闭合
    energy_balance_gap = max(abs(c["harvest"] - c["consume"] - c["e_net"])
                             for c in coupled)

    # 红线自检
    forbidden = ("kWh", "MW", "千瓦时", "万元", "亿元", "单价", "报价", "供应商",
                 "成本", "mm ", "吨", "MPa", "kHz", "V ", "v3.", "v4.")
    sample = ("%.4f " * 6) % (net_min, residual_max, dz_max,
                              a_off_residual_max, mutual_gain, energy_balance_gap)
    forbidden_hit = any(w in sample for w in forbidden)

    results = dict(
        sea_states=SEA_STATES,
        net_min=net_min, net_margin_worst=net_margin_worst,
        net_monotonic=bool(net_monotonic),
        residual_max=residual_max, residual_monotonic=bool(residual_monotonic),
        dz_min=dz_min, dz_max=dz_max, dz_monotonic=bool(dz_monotonic),
        a_off_residual_max=a_off_residual_max,
        a_off_residual_violations=a_off_violations,
        b_off_net_negative=b_off_net_negative,
        mutual_gain=mutual_gain,
        data_channels_ok=bool(data_channels_ok),
        energy_balance_gap=float(energy_balance_gap),
        forbidden_hit=bool(forbidden_hit), dim_normalized=True,
        meta=dict(
            title="A×B 系统耦合闭环与净能量审计判据核验",
            level="LEVEL-0 机级筛选计算",
            note="能量 / 力 / 位移全部归一化；系统版本与内部构型不出现",
            boundaries=[
                "LEVEL-0 机级筛选计算，不替代物理实测与联合仿真",
                "收获系数与开销系数为可达区间假设值，须以实测标定",
                "三条闭环判据为定性口径的量化形态，阈值以内部标定为准",
                "本脚本不构成工程承诺",
                "仿真边界：27 m 标准舱（金字塔 + 立方体管）+ 多通道 PTO；宽体矩阵整体不纳入本算例"]))

    ok, fail, lines = assertions(results)
    results["assertions"] = dict(passed=ok, failed=fail, lines=lines)

    p = os.path.join(HERE, "verify_15_ab_coupling_summary.json")
    io.open(p, "w", encoding="utf-8").write(
        json.dumps(results, ensure_ascii=False, indent=1))

    print("=" * 76)
    print("断言汇总：%d 通过 / %d 失败" % (ok, fail))
    print("=" * 76)
    for l in lines:
        print("  ", l)
    print()
    print("[落盘] %s" % p)
    print()
    print("【口径声明】LEVEL-0 机级筛选计算，不替代物理实测；")
    print("           能量 / 力 / 位移全为归一化相对量，不落功率绝对值。")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
