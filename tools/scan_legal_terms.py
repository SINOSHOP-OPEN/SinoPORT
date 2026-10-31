# -*- coding: utf-8 -*-
"""
20261031 · 法律用语合规扫描（确权 / 发证类误导词）
================================================================================
用途：扫描公开门面与交付物，拦截**把「已提交待审核」表述成「已获权利 / 已确权 / 已发证」**
      的法律误导性措辞。

★ 背景（船长 2026-10-31 16:19 裁定）：
  数据集在广东省数据知识产权登记平台处于「**待审核**」，**尚未正式下发确权证书**。
  故公开面**不得**使用「已确权」这类结论性法律用语，须统一表述为  # legal-scan:allow
  「**已提交登记审核中的数字资产**」或「已提交登记」。

★ 两种「确权」语义要分清（避免误伤）：
  ✘ 指「已在官方平台获权利/发证」 → **必须拦截**
  ✓ 指「贡献者身份确认」「SHA-256 哈希存证」「RWA 链上资产通证」 → 另一回事，**不拦**

用法：python scan_legal_terms.py <目标路径...>
"""
import os
import re
import sys

# ── 拦截规则：命中即红 ──
#   每条 = (规则名, 正则, 说明)
FORBIDDEN = [
    # 指官方已发证 / 已获权利
    ("已确权", r"已确权|确权成功|确权完成|已获确权",
     "平台尚未下发登记证书，不得声称已确权"),
    ("已获证", r"已获(?:得)?(?:确权|登记)?证书|已获发证|已领证|已下发证书|证书已(?:下|到)达",
     "未发证前不得声称已获证书"),
    ("登记成功", r"登记成功|已登记成功",
     "当前状态为「待审核」，不得声称登记成功"),
    ("审核通过", r"已通过审核|审核已通过|审核通过|已审核通过|审核通过并公示",
     "当前状态为「待审核」，不得声称审核通过"),
    ("已公示", r"已公示|公示期满|已完成公示",
     "尚未进入公示期，不得声称已公示"),
    ("权利主张", r"(?:已|均已)获得(?:了)?(?:权利|授权|保护|认证)|受法律保护|获得(?:了)?法律保护|权利已(?:获|授予)|享有(?:著作权|权利)",
     "未发证前不得主张权利授予"),
    ("已授权", r"已授权(?:给|于)|获得官方授权|官方认证(?:通过|完成)|已获官方认证",
     "未发证前不得声称官方授权 / 认证"),
]

# ── 豁免白名单：只声明、不主张（合规表述）──
ALLOW_PATTERNS = [
    r"贡献即确权",
    r"数字资产确权库",
    r"RWA[^。\n]{0,12}确权",
    r"资产确权与",
    r"哈希确权",
    r"已提交登记审核中",
    r"已提交登记",
    r"待审核",
]


def line_is_allowlisted(line):
    return any(re.search(p, line) for p in ALLOW_PATTERNS)


# 扫描器自身的关键词表不算命中 ——
#   那是它要**抓**的目标，是工具的工作内容，不是对外表述。
#
# ★ 做法：**行内正则字面量 + 规则定义块**双重豁免
#   ① 行内的 r"..." / r'...' 字面量 → 只洗字面量部分，同行其他文本照常判定；
#   ② 规则定义块（从 FORBIDDEN = [ 到 ] 之间的整段）→ 整块豁免
#      （规则名与说明文字里含中文关键词，不豁免会自我命中）。
_LITERAL_IN_LINE = re.compile(r'r(["\'])(?:(?!\1).)*\1')
# ★ 显式豁免标记：以该前缀开头的行一律豁免（用于「讲解规则的散文」与自测样本）
_ALLOW_MARK = re.compile(r'legal-scan:allow\b')
# ★ 文件级豁免：文件**首行**出现该标记 → 整文件豁免
#   用于「自测样本文件」—— 它按设计必须包含违规文本（阳性样本）。
_ALLOW_FILE_MARK = re.compile(r'legal-scan:allow-file\b')
_RULE_BLOCK_START = re.compile(r'^\s*FORBIDDEN\s*=\s*\[\s*$')
_RULE_BLOCK_END = re.compile(r'^\s*\]\s*$')


def scrub_literals(text):
    """清洗扫描器自身的关键词表：定义块整体豁免，其余行只洗正则字面量。"""
    out = []
    in_block = False
    for ln in text.split("\n"):
        if _RULE_BLOCK_START.match(ln):
            in_block = True
            out.append("")
            continue
        if in_block:
            out.append("")
            if _RULE_BLOCK_END.match(ln):
                in_block = False
            continue
        out.append(_LITERAL_IN_LINE.sub('""', ln))
    return "\n".join(out)


def scan_text(path, text):
    hits = []
    # 文件级豁免（首行标记）
    first = text.split("\n", 1)[0] if text else ""
    if _ALLOW_FILE_MARK.search(first):
        return []
    scrubbed = scrub_literals(text)
    # 逐行判定，但用「整行洗过的版本」判断是否落在关键词表里
    raw_lines = text.split("\n")
    clean_lines = scrubbed.split("\n")
    for i, line in enumerate(raw_lines):
        clean = clean_lines[i] if i < len(clean_lines) else line
        if not clean.strip():
            continue
        if _ALLOW_MARK.search(line):
            continue
        if line_is_allowlisted(clean):
            continue
        for name, pat, why in FORBIDDEN:
            m = re.search(pat, clean)
            if m:
                hits.append((path, i + 1, name, m.group(0), why, line.strip()[:90]))
    return hits


def main():
    targets = sys.argv[1:]
    if not targets:
        print("用法：python scan_legal_terms.py <路径...>")
        return 2

    hits = []
    n_files = 0
    for t in targets:
        if os.path.isfile(t):
            try:
                txt = open(t, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            n_files += 1
            hits += scan_text(t, txt)
        else:
            for dp, dn, fn in os.walk(t):
                dn[:] = [d for d in dn if d not in (".git", "__pycache__", "node_modules")]
                for f in fn:
                    if not f.endswith((".md", ".html", ".txt", ".py", ".json", ".yml", ".yaml")):
                        continue
                    p = os.path.join(dp, f)
                    try:
                        txt = open(p, encoding="utf-8", errors="ignore").read()
                    except Exception:
                        continue
                    n_files += 1
                    hits += scan_text(p, txt)

    print("═" * 82)
    print("  法律用语合规扫描（确权 / 发证类误导词）")
    print("═" * 82)
    print("\n  扫描文件：%d 个" % n_files)
    if hits:
        print("\n  ── 命中明细 ──")
        for p, i, name, hit, why, ctx in hits:
            print("  🔴 %s" % p)
            print("     L%-5d 规则「%s」 命中「%s」" % (i, name, hit))
            print("     理由：%s" % why)
            print("     原文：%s" % ctx)
    else:
        print("\n  （零命中）")

    print("\n  总判定：%s" % ("✅ 无误导性法律用语 —— 合规" if not hits
                            else "❌ %d 处需修正" % len(hits)))
    print("═" * 82)
    return 0 if not hits else 1


if __name__ == "__main__":
    sys.exit(main())
