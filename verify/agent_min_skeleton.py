# -*- coding: utf-8 -*-
"""
SinoPORT-Twin · AI Agent 最小可运行骨架
================================================================================
一个可运行的最小骨架，示范本项目的三层结构与国产算力迁移接口：

    L4  编排层（Orchestrator）  —— 本文件：决定「做什么、怎么串、怎么判」
    L3  断言校验层（Assertion）  —— assertion_layer.py：判定「结论是否成立」
    L1  设备抽象层（Device）    —— device_layer.py：屏蔽「算力跑在哪」
    L0  Mock 后端（Mock）       —— mock_backend.py：无需 GPU 即可跑通全链

【设计哲学】
    人提供物理直觉与道德红线，AI 提供不知疲倦的穷举与交叉验证。
    本骨架把这条分工写进代码结构里：
      · 物理判据（断言）由**脚本**判定，退出码 0 才算通过；
      · 编排层只负责调度与汇总，**不产生**任何结论；
      · 设备抽象层把「算力在哪」与「判据是什么」彻底解耦。

【运行】
    python agent_min_skeleton.py

【诚实边界】
    本骨架为**接口与调度示范**，不含真实物理仿真、不含工程参数、不含任何
    物理尺寸、材料配比或内部控制律。Mock 后端返回确定性结果，仅用于验证
    编排链路与断言判定机制。真实数值结论请以 verify/ 下的公开验证脚本为准。
================================================================================
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────
# L1 · 设备抽象层（Device Abstraction Layer）
# ─────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DeviceInfo:
    """设备能力描述 —— 上层只依赖这份能力清单，不依赖具体硬件。"""
    name: str
    vendor: str
    backend: str
    supports_fp32: bool = True
    supports_deterministic: bool = True
    notes: str = ""


class DeviceBackend:
    """设备抽象接口。

    实现方需提供两个能力：
        · describe()  —— 报告自身能力（供编排层做适配决策）
        · execute()   —— 执行一段确定性计算，返回结果与退出码

    ★ 迁移要点：新增国产算力栈时**只需实现本接口**，编排层与断言层零改动。
    """

    def describe(self) -> DeviceInfo:
        raise NotImplementedError

    def execute(self, task: Dict[str, Any]) -> "TaskResult":
        raise NotImplementedError


@dataclass
class TaskResult:
    """任务执行结果 —— 与设备无关的统一返回结构。"""
    task_id: str
    passed: bool
    exit_code: int
    detail: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────
# L3 · 断言校验层（Assertion Layer）
# ─────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Assertion:
    """一条断言：判据 + 判定方式。

    人划下「不可逾越的安全包络」（判据），机器负责判定（穷举与交叉验证）。
    判据为**相对量或无量纲关系**，不含任何绝对工程量。
    """
    name: str
    predicate: str            # 人类可读的判据描述
    evaluate: Any             # 可调用对象：接收 task 结果，返回 (bool, str)


class AssertionLayer:
    """断言校验层 —— 汇总判定，产出机器可读的结论集合。"""

    def __init__(self) -> None:
        self._assertions: List[Assertion] = []

    def register(self, assertion: Assertion) -> None:
        self._assertions.append(assertion)

    def check(self, results: Dict[str, TaskResult]) -> Dict[str, Any]:
        """对一批任务结果逐条判定。

        返回：{ passed, failed, total, failures[] , exit_code }
        退出码语义与本项目一致：**0 = 全部通过**。
        """
        failures: List[Dict[str, str]] = []
        passed = 0
        for a in self._assertions:
            res = results.get(a.name)
            if res is None:
                failures.append({"assertion": a.name, "reason": "任务未执行"})
                continue
            ok, why = a.evaluate(res)
            if ok:
                passed += 1
            else:
                failures.append({"assertion": a.name, "reason": why})
        total = len(self._assertions)
        return {
            "passed": passed,
            "failed": len(failures),
            "total": total,
            "failures": failures,
            "exit_code": 0 if not failures else 1,
        }


# ─────────────────────────────────────────────────────────────────────────
# L4 · 编排层（Orchestrator）
# ─────────────────────────────────────────────────────────────────────────

class Orchestrator:
    """编排层：调度、适配、汇总。

    职责边界（刻意收窄，避免 AI 越权产生结论）：
        · 决定**执行哪些任务**、用什么设备后端、如何汇总；
        · **不判断物理对错** —— 那是 L3 断言层的职责；
        · 设备差异在 L1 被吸收，编排层只见统一的任务与结果结构。
    """

    def __init__(self, backend: DeviceBackend, assertions: AssertionLayer) -> None:
        self.backend = backend
        self.assertions = assertions

    def run(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        info = self.backend.describe()
        results: Dict[str, TaskResult] = {}
        for t in tasks:
            res = self.backend.execute(t)
            results[res.task_id] = res

        verdict = self.assertions.check(results)
        return {
            "device": {
                "name": info.name,
                "vendor": info.vendor,
                "backend": info.backend,
                "deterministic": info.supports_deterministic,
            },
            "tasks": len(tasks),
            "verdict": verdict,
        }


# ─────────────────────────────────────────────────────────────────────────
# 演示：编排 3 个任务 × 若干条断言，Mock 后端确定性返回
# ─────────────────────────────────────────────────────────────────────────

def build_demo_backend() -> DeviceBackend:
    """构造 Mock 后端 —— 无需 GPU，纯确定性。"""

    class MockBackend(DeviceBackend):
        def describe(self) -> DeviceInfo:
            return DeviceInfo(
                name="mock-cpu",
                vendor="reference",
                backend="mock",
                supports_fp32=True,
                supports_deterministic=True,
                notes="纯软件 mock，用于验证编排链路；不产生任何工程结论。",
            )

        def execute(self, task: Dict[str, Any]) -> TaskResult:
            # 确定性：同一输入必得同一输出（与本项目 verify/ 脚本同一原则）
            tid = task["id"]
            value = float(task.get("value", 0.0))
            threshold = float(task.get("threshold", 1.0))
            ok = value <= threshold
            return TaskResult(
                task_id=tid,
                passed=ok,
                exit_code=0 if ok else 1,
                detail={"value": value, "threshold": threshold,
                        "margin": round(threshold - value, 6)},
            )

    return MockBackend()


def build_demo_assertions() -> AssertionLayer:
    """构造一组**无量纲**断言 —— 只判相对关系，不含任何绝对工程量。"""
    al = AssertionLayer()

    al.register(Assertion(
        name="wave_attenuation",
        predicate="消浪后残余响应不劣于入射响应（相对量比较）",
        evaluate=lambda r: (r.detail["value"] <= r.detail["threshold"],
                            "残余响应 %.4f 超过阈值 %.4f" % (r.detail["value"], r.detail["threshold"])),
    ))
    al.register(Assertion(
        name="stability_margin",
        predicate="稳性裕度保持为正（相对量 > 0）",
        evaluate=lambda r: (r.detail["value"] > 0.0,
                            "稳性裕度为 %.4f，非正" % r.detail["value"]),
    ))
    al.register(Assertion(
        name="energy_closure",
        predicate="扣除寄生能耗后净能量为正（相对量 > 0）",
        evaluate=lambda r: (r.detail["value"] > 0.0,
                            "净能量为 %.4f，非正" % r.detail["value"]),
    ))
    return al


def main() -> int:
    tasks = [
        {"id": "wave_attenuation", "value": 0.040, "threshold": 0.060},
        {"id": "stability_margin",  "value": 0.125, "threshold": 1.0},
        {"id": "energy_closure",   "value": 0.019, "threshold": 1.0},
    ]

    orch = Orchestrator(build_demo_backend(), build_demo_assertions())
    out = orch.run(tasks)

    print("=" * 74)
    print("SinoPORT-Twin · AI Agent 最小骨架 · 运行演示")
    print("=" * 74)
    d = out["device"]
    print("  设备后端   : %s（vendor=%s, backend=%s, 确定性=%s）"
          % (d["name"], d["vendor"], d["backend"], d["deterministic"]))
    print("  编排任务数 : %d" % out["tasks"])
    v = out["verdict"]
    print("  断言判定   : 通过 %d / 失败 %d / 共 %d"
          % (v["passed"], v["failed"], v["total"]))
    for f in v["failures"]:
        print("    [FAIL] %s —— %s" % (f["assertion"], f["reason"]))
    print("  退出码     : %d" % v["exit_code"])
    print("=" * 74)
    print("说明：本演示仅验证「编排 → 设备抽象 → 断言判定 → 退出码」链路，")
    print("      不含任何物理仿真与工程参数；真实结论以 verify/ 公开脚本为准。")
    print("      迁移国产算力栈时，只需实现 DeviceBackend 接口，编排层与断言层零改动。")

    # 同时输出机器可读结论，便于 CI / 后续 Agent 消费
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return v["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
