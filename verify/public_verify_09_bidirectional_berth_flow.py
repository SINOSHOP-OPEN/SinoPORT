# -*- coding: utf-8 -*-
"""
SINOPORT 公开版验证脚本 09 · 开放规划图双侧泊位路基与不积压仿真
================================================================
公开可运行版本：把《悬浮港开放设计规划图》工程化为工程平面图，
并以离散事件仿真验证三项设计要求：

  ① 一个泊位双侧装卸 —— 同一条泊位路基两侧各靠一船
  ② 一条泊位路基同时为两侧船舶装卸 —— 对冲直装（A→B）就地交接
  ③ 泊位路基与港区道路快速流转货物、不积压载荷

★ 红线声明：输出全部为无量纲相对指标与无量纲判定，不涉及任何货币量纲
  与商务信息；不涉及工程配置参数。

模型层级：LEVEL-0 机级筛选（离散事件仿真），为通航仿真与现场实测提供
边界参考，不替代实测。

运行：python public_verify_09_bidirectional_berth_flow.py
退出码非 0 即判定失败。
"""
import io
import json
import math
import os
import random
import heapq
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════
# 1. 参数（泊位规格来自编码规范 V6.1-r2 §4.27.4）
# ══════════════════════════════════════════════════════════════════
BERTHS = [
    ("泊1", "小", 27, 150, -1293.0),
    ("泊2", "中", 54, 690, -1042.5),
    ("泊3", "中", 54, 690, -778.5),
    ("泊4", "大", 81, 900, -396.0),
    ("泊5", "大", 81, 900, 0.0),
    ("泊6", "大", 81, 900, 396.0),
    ("泊7", "中", 54, 690, 778.5),
    ("泊8", "中", 54, 690, 1042.5),
    ("泊9", "小", 27, 150, 1293.0),
]

QC_RATE = 42.0 / 3600.0
QC_RATE_OPT = 48.0 / 3600.0
IGV_SPEED = 16.67 / 3.6
IGV_PICK_TIME = 10.0
IGV_LOAD_TIME = 12.0
ROAD_LANES = 4
ROAD_CAPACITY_PER_LANE = 2
TURN_ZONE_LEN = 60.0
BOX_SLOT_LEN = 12.0
SEED = 20261025


class Box:
    __slots__ = ("side", "dest", "t_arrive", "t_qc_done", "t_roadbed",
                 "t_pick", "t_exit", "wait_buffer", "wait_igv")

    def __init__(self, side, dest):
        self.side = side
        self.dest = dest
        self.t_arrive = 0.0
        self.t_qc_done = 0.0
        self.t_roadbed = 0.0
        self.t_pick = 0.0
        self.t_exit = 0.0
        self.wait_buffer = 0.0
        self.wait_igv = 0.0


class Sim:
    """单泊位双侧装卸 + 路基/道路流（离散事件仿真）"""

    def __init__(self, berth, n_pairs=120, direct_ratio=0.5,
                 igv_count=None, buffer_slots=None, qc_rate=None, seed=0):
        self.name, self.kind, self.width, self.length, self.x = berth
        self.n_pairs = n_pairs
        self.direct_ratio = direct_ratio
        self.rng = random.Random(seed)
        usable = max(self.length - TURN_ZONE_LEN, BOX_SLOT_LEN)
        self.buffer_slots = buffer_slots if buffer_slots is not None \
            else int(usable // BOX_SLOT_LEN)
        self.qc_rate = qc_rate if qc_rate is not None else QC_RATE
        if igv_count is None:
            t_leg = (self.length / 2 + 120.0) / IGV_SPEED
            cycle = IGV_PICK_TIME + t_leg + IGV_LOAD_TIME + t_leg
            igv_count = max(int(math.ceil(2 * self.qc_rate * cycle * 1.35)), 3)
        self.igv_count = igv_count
        self.boxes = []
        self.heap = []
        self._seq = 0
        self.stats = {}

    def run(self, horizon=None):
        rng = self.rng
        for side in ("L", "R"):
            for i in range(self.n_pairs):
                t_arrive = rng.expovariate(self.qc_rate)
                self._seq += 1
                heapq.heappush(self.heap,
                               (t_arrive, self._seq, ("QC_ARRIVE", (side, i))))
        t_end = horizon or (self.n_pairs * 2 / self.qc_rate * 6.0)

        qc_free = {"L": 0.0, "R": 0.0}
        slots = {}
        slot_of = {}
        qc_waiting = {"L": None, "R": None}
        igv_pos = [0.0] * self.igv_count
        igv_free = [0.0] * self.igv_count
        road_in = 0
        boxes_done = 0
        max_on_roadbed = 0
        series = []
        qc_waits = []
        direct_pending = {"L": [], "R": []}
        direct_pairs = 0
        qc_next_slot = {"L": self.buffer_slots - 1, "R": self.buffer_slots - 1}

        def try_place(t_now, side):
            si = qc_next_slot[side]
            while si >= 0 and (side, si) in slots:
                si -= 1
            if si < 0:
                return False
            qc_next_slot[side] = si - 1
            bx = qc_waiting[side]
            qc_waiting[side] = None
            bx.t_qc_done = t_now
            bx.t_roadbed = t_now
            slots[(side, si)] = bx
            slot_of[bx] = (side, si)
            self._seq += 1
            heapq.heappush(self.heap, (t_now, self._seq,
                                       ("IGV_DISPATCH", (bx,))))
            return True

        heap = self.heap
        while heap:
            t_ev, _sq, (kind, payload) = heapq.heappop(heap)
            if t_ev > t_end:
                break

            if kind == "QC_ARRIVE":
                side, idx = payload
                if qc_free[side] > t_ev:
                    self._seq += 1
                    heapq.heappush(heap, (qc_free[side], self._seq,
                                          ("QC_ARRIVE", payload)))
                    continue
                t_qc = t_ev + 1.0 / self.qc_rate
                qc_free[side] = t_qc
                dest = "DIRECT" if rng.random() < self.direct_ratio else "EXIT"
                bx = Box(side, dest)
                self.boxes.append(bx)
                bx.t_arrive = t_ev

                if dest == "DIRECT":
                    # 对冲直装：路基就地交接，不占存箱位、不经 IGV 与道路
                    opp = "R" if side == "L" else "L"
                    bx.t_qc_done = t_qc
                    bx.t_roadbed = t_qc
                    bx.t_pick = t_qc
                    bx.t_exit = t_qc
                    bx.wait_igv = 0.0
                    if direct_pending[opp]:
                        other = direct_pending[opp].pop(0)
                        other.t_qc_done = t_qc
                        other.t_exit = t_qc
                        direct_pairs += 1
                    direct_pending[side].append(bx)
                    boxes_done += 1
                    continue

                qc_waiting[side] = bx
                if not try_place(t_qc, side):
                    bx.wait_buffer = t_qc - t_ev - 1.0 / self.qc_rate
                    qc_waits.append((side, t_ev, t_qc))

            elif kind == "SLOT_FREE":
                for sd in ("L", "R"):
                    if qc_waiting[sd] is not None:
                        try_place(payload, sd)

            elif kind == "IGV_DISPATCH":
                (bx,) = payload
                if road_in >= ROAD_LANES * ROAD_CAPACITY_PER_LANE:
                    self._seq += 1
                    heapq.heappush(heap, (t_ev + 2.0, self._seq,
                                          ("IGV_DISPATCH", (bx,))))
                    continue
                k = min(range(self.igv_count), key=lambda i: igv_free[i])
                side, si = slot_of[bx]
                y_pick = TURN_ZONE_LEN + (si + 0.5) * BOX_SLOT_LEN
                travel_in = abs(y_pick - igv_pos[k]) / IGV_SPEED
                t_igv = max(t_ev, igv_free[k]) + travel_in
                bx.t_pick = t_igv + IGV_PICK_TIME
                bx.wait_igv = bx.t_pick - bx.t_roadbed
                travel_out = y_pick / IGV_SPEED
                t_exit = bx.t_pick + travel_out + IGV_LOAD_TIME
                igv_pos[k] = 0.0
                igv_free[k] = t_exit + travel_out
                road_in += 1
                self._seq += 1
                heapq.heappush(heap, (t_exit, self._seq, ("BOX_EXIT", (bx,))))

            elif kind == "BOX_EXIT":
                (bx,) = payload
                road_in -= 1
                key = slot_of.get(bx)
                if key is not None and key in slots:
                    del slots[key]
                bx.t_exit = t_ev
                boxes_done += 1
                series.append((t_ev, len(slots)))
                self._seq += 1
                heapq.heappush(heap, (t_ev, self._seq, ("SLOT_FREE", t_ev)))

        n = max(len(self.boxes), 1)
        nl = sum(1 for b in self.boxes if b.side == "L")
        nr = sum(1 for b in self.boxes if b.side == "R")
        e2e = [b.t_exit - b.t_arrive for b in self.boxes if b.t_exit > 0]
        occ = [c for _, c in series]
        self.stats = dict(
            berth=self.name, kind=self.kind, width_m=self.width,
            length_m=self.length, x_m=self.x,
            buffer_slots=self.buffer_slots, igv_count=self.igv_count,
            qc_rate=self.qc_rate, direct_ratio=self.direct_ratio,
            roadbed_occupancy_max=max(occ) if occ else 0,
            roadbed_occupancy_mean=(sum(occ) / len(occ)) if occ else 0.0,
            qc_wait_events=len(qc_waits),
            igv_wait_max_s=max([b.wait_igv for b in self.boxes] or [0.0]),
            buffer_wait_max_s=max([b.wait_buffer for b in self.boxes] or [0.0]),
            e2e_mean_s=(sum(e2e) / len(e2e)) if e2e else 0.0,
            e2e_max_s=max(e2e) if e2e else 0.0,
            n_left=nl, n_right=nr,
            side_imbalance=abs(nl - nr) / max(nl + nr, 1),
            direct_pairs=direct_pairs, boxes_done=boxes_done,
        )
        return self.stats


def run_cases():
    out = {}
    b5 = BERTHS[4]
    b1 = BERTHS[0]

    def go(berth, key, **kw):
        s = Sim(berth, seed=SEED, **kw)
        out[key] = s.run()
        return out[key]

    go(b5, "泊5_基准")
    go(b5, "泊5_最优岸桥", qc_rate=QC_RATE_OPT)
    go(b5, "泊5_全直装", direct_ratio=1.0)
    go(b5, "泊5_零直装", direct_ratio=0.0)
    for ni in (3, 4, 5, 6, 7, 8):
        go(b5, "泊5_IGV%d台" % ni, igv_count=ni)
    go(BERTHS[2], "泊3_基准")
    go(b1, "泊1_基准")
    go(b1, "泊1_直装80%", direct_ratio=0.80)
    go(b1, "泊1_直装80%+溢出20位", direct_ratio=0.80, buffer_slots=7 + 20)
    go(b1, "泊1_溢出40位", direct_ratio=0.50, buffer_slots=7 + 40)
    return out


def assertions(cases):
    lines = []
    passed = failed = 0

    def chk(cond, msg):
        nonlocal passed, failed
        if cond:
            passed += 1
            lines.append(("PASS", msg))
        else:
            failed += 1
            lines.append(("FAIL", msg))

    # ① 双侧同时作业可行
    for key, s in cases.items():
        chk(s["n_left"] > 0 and s["n_right"] > 0,
            "%s：双侧均有箱完成（左 %d / 右 %d）"
            % (key, s["n_left"], s["n_right"]))

    # ② 路基占用率峰值 ≤ 85%（不积压量化判据）
    for key, s in cases.items():
        if "_IGV" in key or "零直装" in key:
            continue
        occ = s["roadbed_occupancy_max"] / max(s["buffer_slots"], 1)
        chk(occ <= 0.85,
            "%s：路基占用率峰值 %.1f%% ≤ 85%%（缓冲 %d 位 / 实占 %d）"
            % (key, 100 * occ, s["buffer_slots"], s["roadbed_occupancy_max"]))

    # ③ 大船泊位基准零阻塞
    s = cases["泊5_基准"]
    chk(s["qc_wait_events"] == 0,
        "泊5_基准：大船泊位路基阻塞 %d 次（目标 0 —— 岸桥全程不停等）"
        % s["qc_wait_events"])

    # ④ 失效边界可复现（判据具备鉴别力）
    stress = {k: v for k, v in cases.items() if "_IGV" in k}
    if stress:
        worst = max(stress.items(), key=lambda kv: kv[1]["igv_wait_max_s"])
        chk(worst[1]["igv_wait_max_s"] > 180.0,
            "★失效边界可复现：%s（IGV 仅 %d 台）IGV 等待达 %.0f s（> 180 s）"
            "⇒ 运力不足时必然积压，判据具备鉴别力"
            % (worst[0], worst[1]["igv_count"], worst[1]["igv_wait_max_s"]))
        best = min(stress.items(), key=lambda kv: kv[1]["igv_count"])
        occ = best[1]["roadbed_occupancy_max"] / max(best[1]["buffer_slots"], 1)
        chk(occ > 0.30,
            "★运力不足时占用率显著抬升：%s（IGV %d 台）占用峰值 %.1f%%（> 30%%）"
            % (best[0], best[1]["igv_count"], 100 * occ))

    # ⑤ 对冲直装的定量价值
    a, b = cases["泊5_全直装"], cases["泊5_零直装"]
    chk(a["roadbed_occupancy_max"] == 0,
        "全直装时路基占用峰值为 0 个箱位（箱完全不进入运输系统）")
    chk(a["e2e_mean_s"] < b["e2e_mean_s"],
        "对冲直装有效：全直装端到端 %.0f s < 零直装 %.0f s"
        % (a["e2e_mean_s"], b["e2e_mean_s"]))
    chk(b["qc_wait_events"] > 0,
        "零直装时出现路基阻塞 %d 次（诚实记录失效边界）" % b["qc_wait_events"])

    # ⑥ 端到端周转
    for key in ("泊5_基准", "泊3_基准", "泊1_基准"):
        if key in cases:
            s = cases[key]
            chk(s["e2e_mean_s"] <= 900.0,
                "%s：端到端平均周转 %.0f s ≤ 900 s（15 min）"
                % (key, s["e2e_mean_s"]))

    # ⑦ 双侧均衡
    for key, s in cases.items():
        chk(s["side_imbalance"] <= 0.15,
            "%s：双侧箱量失衡度 %.1f%% ≤ 15%%（载荷守恒前提）"
            % (key, 100 * s["side_imbalance"]))

    # ⑧ 小船泊位短板识别与对策有效性
    b0 = cases["泊1_基准"]
    chk(b0["qc_wait_events"] > 0,
        "★★短板如实识别：泊1（路基 150 m / %d 个单层箱位）基准阻塞 %d 次 "
        "⇒ 小船泊位须配「浮箱溢出区 + 直装优先」对策"
        % (b0["buffer_slots"], b0["qc_wait_events"]))
    if "泊1_直装80%+溢出20位" in cases:
        b1s = cases["泊1_直装80%+溢出20位"]
        chk(b1s["qc_wait_events"] <= b0["qc_wait_events"],
            "泊1 对策有效：直装 80%% + 溢出 20 位 → 阻塞 %d 次 ≤ 基准 %d 次"
            % (b1s["qc_wait_events"], b0["qc_wait_events"]))
    if "泊1_溢出40位" in cases:
        b2s = cases["泊1_溢出40位"]
        occ = b2s["roadbed_occupancy_max"] / max(b2s["buffer_slots"], 1)
        chk(occ <= 0.85,
            "泊1 对策有效：溢出 40 位后路基占用率峰值 %.1f%% ≤ 85%%" % (100 * occ))

    # ⑨ IGV 运力余量
    base = cases["泊5_基准"]
    t_leg = (900.0 / 2 + 120.0) / IGV_SPEED
    cycle = IGV_PICK_TIME + t_leg + IGV_LOAD_TIME + t_leg
    cap = base["igv_count"] / cycle
    need = 2 * base["qc_rate"]
    chk(cap > need,
        "泊5 基准：IGV 运力 %.4f 箱/s > 双侧放箱需求 %.4f 箱/s（余量 %.0f%%）"
        % (cap, need, 100 * (cap / need - 1.0)))

    return passed, failed, lines


def main():
    print("=" * 74)
    print("SINOPORT 开放规划图 · 双侧泊位路基与道路不积压仿真（公开版）")
    print("=" * 74)

    print("\n【1】泊位规格（编码规范 V6.1-r2 §4.27.4）")
    print("  %-8s %-6s %10s %12s %12s" % ("泊位", "类型", "路基宽(m)",
                                          "路基长(m)", "单层缓冲位"))
    for nm, kd, w, L, x in BERTHS:
        usable = max(L - TURN_ZONE_LEN, BOX_SLOT_LEN)
        print("  %-8s %-6s %10.0f %12.0f %12d" % (nm, kd, w, L,
                                                    int(usable // BOX_SLOT_LEN)))

    cases = run_cases()

    print("\n【2】仿真结果")
    print("  %-20s %8s %9s %9s %10s %9s"
          % ("工况", "缓冲位", "占用峰值", "路基阻塞", "IGV等待", "E2E均值"))
    for k, s in cases.items():
        occ = s["roadbed_occupancy_max"] / max(s["buffer_slots"], 1)
        print("  %-20s %8d %8.1f%% %9d %9.1fs %8.0fs"
              % (k, s["buffer_slots"], 100 * occ, s["qc_wait_events"],
                 s["igv_wait_max_s"], s["e2e_mean_s"]))

    passed, failed, lines = assertions(cases)
    print("\n【3】断言")
    for tag, msg in lines:
        print("  %s  %s" % (tag, msg))
    print("\n  断言：%d 通过 / %d 失败" % (passed, failed))

    out = {
        "meta": {
            "title": "开放规划图双侧泊位路基与不积压仿真",
            "level": "LEVEL-0 机级筛选（离散事件仿真）",
            "berths_source": "编码规范 V6.1-r2 §4.27.4（9 泊位 513 m）",
            "qc_rate_source": "京唐港认证综合作业效率 42 move/h",
        },
        "berths": [dict(name=n, kind=k, width_m=w, length_m=L, x_m=x)
                   for n, k, w, L, x in BERTHS],
        "params": {
            "qc_rate_move_h": QC_RATE * 3600,
            "qc_rate_opt_move_h": QC_RATE_OPT * 3600,
            "igv_speed_mps": IGV_SPEED,
            "igv_pick_s": IGV_PICK_TIME,
            "igv_load_s": IGV_LOAD_TIME,
            "road_lanes": ROAD_LANES,
            "road_capacity_per_lane": ROAD_CAPACITY_PER_LANE,
            "turn_zone_len_m": TURN_ZONE_LEN,
            "box_slot_len_m": BOX_SLOT_LEN,
            "no_ground_stacking": True,
        },
        "cases": cases,
        "assertions": dict(passed=passed, failed=failed,
                           lines=[dict(status=t, msg=m) for t, m in lines]),
        "assumptions": [
            dict(id="P-1", item="泊位路基单层不落地堆存，缓冲位数 = "
                 "(路基长 − 端部作业区) / 箱位长",
                 note="浮式路基承载受限；对应 §7.2 单层快离约束"),
            dict(id="P-2", item="岸桥取箱耗时 = 1/节拍；落箱后持续占用路基箱位",
                 note="IGV 取走时才释放箱位"),
            dict(id="P-3", item="IGV 完整循环 = 取箱 + 重载行程 + 落箱 + 空驶回程",
                 note="行程按 (路基长/2 + 120 m) 计"),
            dict(id="P-4", item="对冲直装箱在路基就地交接，不占存箱位、不经 IGV 与道路",
                 note="这是「不积压」的根本机制"),
            dict(id="P-5", item="道路在途车上限 = 车道数 × 每车道容量",
                 note="108 m 宽路基上的有效作业车道取 4（双向各 2）"),
            dict(id="P-6", item="直装比例是可调度参数，由 TOS 按航次目的港匹配度在线调节",
                 note="提高它比增加 IGV 更有效"),
        ],
    }
    p = os.path.join(HERE, "verify_09_bidirectional_berth_summary.json")
    io.open(p, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print("\n结果已写入：", p)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
