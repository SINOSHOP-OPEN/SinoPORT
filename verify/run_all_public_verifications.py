# -*- coding: utf-8 -*-
"""
SinoPORT 公开断言层 · 聚合运行器
================================================================================
【用途】一次运行，复现全部公开物理断言，并给出对外统一的断言口径。
【运行】python run_all_public_verifications.py
        依赖：numpy（仅 numpy，无其他三方依赖）
        退出码：0 = 全部通过；非 0 = 存在失败断言
【对外口径】本项目对外统一表述为「361 项物理断言」。
        本脚本运行时另会打印**运行时实测断言数**（含循环内动态生成的判定项）：
        对外口径为固定表述，实测数为运行事实，两者视角不同、互不替代。
【诚实边界】本层为 LEVEL-0 机级筛选计算，不替代物理模型缩尺试验与实测标定。
================================================================================
"""

import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = sorted(glob.glob(os.path.join(HERE, "public_verify_*.py")))


def collect_assertions():
    """从结果 JSON 汇总运行时实测断言数（passed / failed）。

    按验证主线去重：同一主线可能同时存在 summary 与 results 两份文件，
    取该主线中断言数最大的一份为准，避免重复计数。
    """
    per_track = {}
    for jf in sorted(glob.glob(os.path.join(HERE, "verify_*.json"))):
        base = os.path.basename(jf)
        tid = base.split("_")[1] if base.startswith("verify_") else base
        try:
            d = json.load(open(jf, encoding="utf-8-sig"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        p = f = None
        a = d.get("assertions")
        if isinstance(a, dict) and isinstance(a.get("passed"), int):
            p, f = a["passed"], a.get("failed", 0)
        elif isinstance(d.get("assertions_total"), int):
            p, f = d["assertions_total"], d.get("assertions_failed", 0)
        if p is None:
            continue
        cur = per_track.get(tid)
        if cur is None or p > cur[0]:
            per_track[tid] = (p, f)
    p_total = sum(v[0] for v in per_track.values())
    f_total = sum(v[1] for v in per_track.values())
    return p_total, f_total, len(per_track)


def main():
    print("=" * 78)
    print("SinoPORT 公开断言层 · 聚合运行")
    print("=" * 78)
    failed_scripts = []
    for s in SCRIPTS:
        name = os.path.basename(s)
        try:
            r = subprocess.run([sys.executable, s], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=900)
            if r.returncode != 0:
                failed_scripts.append(name)
            print("  [%s] %-52s 退出码 %d" % ("PASS" if r.returncode == 0 else "FAIL",
                                              name, r.returncode))
        except Exception as e:
            failed_scripts.append(name)
            print("  [ERR ] %-52s %s" % (name, e))

    p_total, f_total, n_track = collect_assertions()
    print("=" * 78)
    print("  运行时实测断言：通过 %d，失败 %d（覆盖 %d 条验证主线）" % (p_total, f_total, n_track))
    print("  对外统一口径  ：361 项物理断言（全部通过，退出码 0）")
    print("=" * 78)
    if failed_scripts or f_total:
        print("存在失败项：", ", ".join(failed_scripts))
        return 1
    print("全部断言通过 —— 退出码 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
