# legal-scan:allow-file —— 本文件按设计包含违规阳性样本（自测用），整体豁免法律用语扫描
# -*- coding: utf-8 -*-
"""
20261031 · 法律用语闸门 · 回归自测（阳性 / 阴性对照）
================================================================================
用途：`scan_legal_terms.py` 的判据一旦修改，必须跑本自测 ——
      阳性用例（真实误导表述）必须**全部抓住**；
      阴性用例（合规表述 / 扫描器自身关键词表）必须**零误报**。

用法：python selftest_legal_scan.py
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scan_legal_terms as S  # noqa: E402

CASES = [
    # ── 阳性：真实误导表述，必须全部命中 ──
    (True, "本页展示的是已确权数据资产的结论级验证证据", "已确权"),
    (True, "我们的数据集已确权，可用于法律主张", "已确权"),
    (True, "相关数据集已获登记证书", "已获证书"),
    (True, "平台已登记成功，权利已授予申请人", "登记成功 / 权利授予"),
    (True, "本次登记审核已通过", "审核通过"),
    (True, "本数据集已公示，满三十日公示期结束", "已公示"),
    (True, "上述作品受法律保护", "受法律保护"),
    (True, "已获官方认证", "官方认证"),
    (True, "已授权给合作方使用", "已授权"),

    # ── 阴性：合规表述，必须零误报 ──
    (False, "已提交登记审核中的数字资产", "标准表述"),
    (False, "尚未取得登记证书，不构成任何形式的权利授予、认证或确权主张", "否定式声明"),
    (False, "当前处于「待审核」阶段", "状态描述"),
    (False, "贡献即确权：合入与复现均获基于 SHA-256 的数字存证凭证", "贡献者语义"),
    (False, "写入数字资产存证库", "存证库"),
    (False, "RWA 资产确权与结算", "RWA 语义"),
    (False, "本白皮书已完成哈希存证（SHA-256 指纹可回溯校验）", "哈希存证"),
    # 扫描器自身的关键词表 —— 必须零误报（自我豁免机制）
    (False, '    ("权利主张", r"(?:已|均已)获得(?:了)?(?:权利|授权|保护|认证)|受法律保护|权利已(?:获|授予)|享有(?:著作权|权利)",  # legal-scan:allow',
     "扫描器规则定义行（显式豁免标记）"),
    (False, '    ("已确权", r"已确权|确权成功|确权完成|已获确权",  # legal-scan:allow', "扫描器规则定义行（显式豁免标记）"),
    (False, '    ("登记成功", r"登记成功|已登记成功",  # legal-scan:allow', "扫描器规则定义行（显式豁免标记）"),
    (False, '    ("已获证", r"已获(?:得)?(?:确权|登记)?证书|已获发证|已领证|已下发证书|证书已(?:下|到)达",  # legal-scan:allow',
     "扫描器规则定义行（显式豁免标记）"),
]


def main():
    print("═" * 78)
    print("  法律用语闸门 · 回归自测")
    print("═" * 78)
    fail = 0
    for i, (should_hit, text, note) in enumerate(CASES, 1):
        hits = S.scan_text("<case>", text)
        got = len(hits) > 0
        ok = (got == should_hit)
        if not ok:
            fail += 1
        mark = "✅" if ok else "❌"
        print("  %s 用例 %-2d  期望%s · 实际%s  │ %s"
              % (mark, i, "命中" if should_hit else "不命中",
                 "命中" if got else "不命中", note))
    print("\n" + "═" * 78)
    print("  用例 %d 条 · 失败 %d 条 · 判定：%s"
          % (len(CASES), fail, "✅ 全部通过" if fail == 0 else "❌ 判据回归失败"))
    print("═" * 78)
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
