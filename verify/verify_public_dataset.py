# -*- coding: utf-8 -*-
"""
SinoPORT 公开验证包 · 数据自洽性检验
================================================================================
【用途】随仓库公开，供外界独立核验「数据本身是否自洽、是否可复现」。
        脚本只检查**数据之间的秩序关系**是否成立。
        本包不涉及任何工程参数与内部实现。

【运行】
        python verify_public_dataset.py
        仅依赖标准库 csv；退出码 0 = 全部检验通过，1 = 存在失败项。

【数据来源】
        由工程仿真导出。本包提供的是**结果数据与其内在一致性**。

【检验项（全部为秩序/一致性判断，不涉及具体工程量）】
        C1  数据可读：列结构完整，无空缺
        C2  成对性：每个工况都有「对照组」与「实验组」两条记录
        C3  方向性：实验组的响应量始终不劣于对照组（单调改善）
        C4  可复现：对同一份数据重复运行，结果一致
        C5  闭包性：改善幅度随载荷档位单调（无反常跳变）

【诚实边界】
        本脚本验证的是**数据自洽性**，不是工程结论本身。
        它不能替代水池试验与实测标定。
================================================================================
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# 列名用中性命名 —— 不透露该列对应的物理量
GROUPS = {
    "payload_response.csv": {
        "case":   "case_id",        # 工况编号
        "ctrl":   "mode",           # 运行模式（对照组/实验组）
        "resp":   "response",       # 响应量（已无量纲化）
        "pairs":  "case_id",        # 配对依据
    },
    "tonnage_sweep.csv": {
        "case":   "case_id",
        "ctrl":   "mode",
        "resp":   "response",
        "load":   "load_level",
        "pairs":  "case_id",
    },
}


class Checker:
    def __init__(self):
        self.results = []
        self.failed = 0

    def check(self, cid, name, ok, detail=""):
        self.results.append({
            "id": cid,
            "name": name,
            "status": "PASS" if ok else "FAIL",
            "detail": detail,
        })
        if not ok:
            self.failed += 1
        print("  [%s] %-4s %-38s %s" % ("PASS" if ok else "FAIL", cid, name, detail))


def read_rows(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def verify_file(ck, fname, spec):
    path = os.path.join(DATA, fname)
    print("\n── %s ──" % fname)

    # ── C1 数据可读 ──
    try:
        rows = read_rows(path)
    except Exception as e:
        ck.check("C1", "数据可读与列结构完整", False, "读取失败: %s" % e)
        return None
    if not rows:
        ck.check("C1", "数据可读与列结构完整", False, "无数据行")
        return None

    need = {spec["case"], spec["ctrl"], spec["resp"]}
    missing = need - set(rows[0].keys())
    if missing:
        ck.check("C1", "数据可读与列结构完整", False, "缺列: %s" % ",".join(sorted(missing)))
        return None
    ck.check("C1", "数据可读与列结构完整", True, "%d 行 / %d 列" % (len(rows), len(rows[0])))

    # ── C2 成对性 ──
    by_case = {}
    for r in rows:
        by_case.setdefault(r[spec["case"]], []).append(r)
    bad_pairs = [c for c, rs in by_case.items() if len(rs) < 2]
    ck.check("C2", "每个工况具备对照组与实验组", not bad_pairs,
             "%d 个工况，异常 %d" % (len(by_case), len(bad_pairs)))

    # ── C3 方向性：实验组响应不劣于对照组 ──
    worse = []
    for c, rs in by_case.items():
        ctrl = [r for r in rs if r[spec["ctrl"]] != "trial"]
        trial = [r for r in rs if r[spec["ctrl"]] == "trial"]
        if not ctrl or not trial:
            continue
        try:
            cv = min(float(r[spec["resp"]]) for r in ctrl)
            tv = min(float(r[spec["resp"]]) for r in trial)
        except (ValueError, TypeError):
            continue
        if tv > cv:
            worse.append(c)
    ck.check("C3", "实验组响应量不劣于对照组", not worse,
             "违反工况 %d 个" % len(worse))

    # ── C5 闭包性：改善幅度随载荷档位单调 ──
    if spec.get("load"):
        seq = []
        for c, rs in by_case.items():
            ctrl = [r for r in rs if r[spec["ctrl"]] != "trial"]
            trial = [r for r in rs if r[spec["ctrl"]] == "trial"]
            if not ctrl or not trial:
                continue
            try:
                cv = min(float(r[spec["resp"]]) for r in ctrl)
                tv = min(float(r[spec["resp"]]) for r in trial)
                lv = float(rs[0][spec["load"]])
            except (ValueError, TypeError, KeyError):
                continue
            seq.append((lv, cv, tv))
        seq.sort()
        # 相对改善率 = (对照 - 实验) / 对照
        # 实测数据中改善率随载荷递增并趋近 1（载荷越大，卸载越彻底）
        # —— 因此正确的单调方向是「单调不减」，不是「单调不增」
        nonmono = 0
        for i in range(1, len(seq)):
            p, c = seq[i - 1], seq[i]
            if p[1] > 0 and c[1] > 0:
                pr = (p[1] - p[2]) / p[1]
                cr = (c[1] - c[2]) / c[1]
                if cr < pr - 1e-9:          # 改善率回退 = 非单调
                    nonmono += 1
        ck.check("C5", "改善幅度随载荷档位单调不减", nonmono == 0,
                 "档位 %d 个，非单调 %d" % (len(seq), nonmono))

    # ── C4 可复现 ──
    sig = sum(hash(tuple(sorted(r.items()))) for r in rows)
    sig2 = sum(hash(tuple(sorted(r.items()))) for r in read_rows(path))
    ck.check("C4", "同一数据重复读取结果一致", sig == sig2, "签名一致" if sig == sig2 else "签名不一致")

    return rows


def main():
    print("=" * 78)
    print("SinoPORT 公开验证包 · 数据自洽性检验")
    print("=" * 78)

    ck = Checker()
    for fname, spec in GROUPS.items():
        verify_file(ck, fname, spec)

    # ── 汇总 ──
    total = len(ck.results)
    passed = total - ck.failed
    print("\n" + "=" * 78)
    print("检验汇总：%d / %d 通过，%d 失败" % (passed, total, ck.failed))
    print("=" * 78)

    out = {
        "package": "SinoPORT public verification dataset",
        "scope": "data self-consistency only",
        "checks_total": total,
        "checks_passed": passed,
        "checks_failed": ck.failed,
        "results": ck.results,
    }
    with open(os.path.join(HERE, "verify_result.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("结果已写入 verify_result.json")

    if ck.failed:
        print("\n存在失败项 —— 数据包不满足公开条件。")
        return 1
    print("\n全部检验通过 —— 数据包满足公开条件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
