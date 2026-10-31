# -*- coding: utf-8 -*-
"""
20261031 · 保密终检（公开面专项）
================================================================================
用途：在关机前对**全部公开面**做最严格的一轮保密核查，
      重点是「红线级」与五关扫描未覆盖的项目：

  ★ 最高优先级：内部资料库链接与内部门面入口
    （workbuddy.cn/space/…、workbuddy.link/p/…）
  ★ 内部文档名 / 内部台账字段 / 内部资产目录名
  ★ 内部登记申请号（粤 2026…）
  ★ 邮箱 / 签名 / 联系方式
  ★ 本地绝对路径与工作区目录
  ★ 内部工艺参数关键词（尺寸/配比/控制律/标定）
  ★ AI 生成水印残留（公开面不得出现「AI生成」标识）

用法：python final_secrecy_audit.py <目标路径...>
"""
import os
import re
import sys

# ── 红线级：内部资料库链接与内部门面入口 ──
REDLINE = [
    ("内部资料库链接", re.compile(r"workbuddy\.cn/space|workbuddy\.link/p|workbuddy\.cn/p/")),
    ("内部门面入口", re.compile(r"资料库|知识库入口|内部文档库|内部资料库")),
]

# ── 内部信息 ──
INTERNAL = [
    ("内部登记申请号", re.compile(r"粤\d{10,}")),
    ("内部台账文件名", re.compile(r"登记总台账|归档索引|资产总清单|实测台账|项目自述底稿")),
    ("内部资产目录名", re.compile(r"20261031前已提交数据集资料汇总|数字资产登记总汇总|20261021_数据知识产权登记"
                                  r"|20261024_要素数据集登记|20261027_数据知识产权登记|20261029_数字资产登记总汇总")),
    ("内部工作流脚本名", re.compile(r"upload_tonight|replace_email|_pw/run_|sync_ledger_from_platform"
                                   r"|archive_submitted_datasets|crosscheck_registry|merge_registry_sources")),
    ("本地绝对路径", re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?:Users|SinoSir|workbudy|workbuddy|SINOSIR)[^\s\"'\)<>]*")),
    ("邮箱地址", re.compile(r"[A-Za-z0-9._%+-]+@(?:qq|gmail|163|126|outlook|hotmail|sinoshop)\.[A-Za-z]{2,}")),
    ("AI生成水印", re.compile(r"AI生成|WORKBUDDY\.?$|生成物")),
    ("密级自引用", re.compile(r"L3_PRIVATE|绝密|机密级|秘密级|受控库")),
    ("内部工艺参数", re.compile(r"标定值|反解口|内控参数|控制律伪代码")),
]

# ── 合规豁免：合理表述不算泄密 ──
ALLOW = [
    r"贡献即确权", r"数字资产存证库", r"RWA[^。\n]{0,12}确权", r"哈希确权",
    r"资产确权与", r"已提交登记审核中", r"已提交登记", r"待审核",
    r"不构成任何形式的权利授予", r"不构成任何权利授予",
    r"规范经大修", r"参考资料", r"受控发布", r"受控单元",
    r"数据自洽性检验", r"控制律可用",
    # ★ 项目公开联系邮箱（standards@sinoshop.org）是**刻意披露**的对外联系方式，
    #   已发布在官网与各仓 README 多年 —— 属公开信息，不是私人邮箱泄漏。
    r"standards@sinoshop\.org",
]


def line_allowed(line):
    return any(re.search(p, line) for p in ALLOW)


def scan(path):
    hits = []
    for dp, dn, fn in os.walk(path):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__")]
        for f in fn:
            if not f.endswith((".md", ".html", ".txt", ".py", ".json", ".yml", ".yaml", ".css", ".js")):
                continue
            p = os.path.join(dp, f)
            try:
                t = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for i, line in enumerate(t.split("\n"), 1):
                if not line.strip():
                    continue
                if line_allowed(line):
                    continue
                for name, pat in REDLINE + INTERNAL:
                    m = pat.search(line)
                    if m:
                        hits.append((p, i, name, m.group(0)[:60], line.strip()[:80]))
    return hits


def main():
    targets = sys.argv[1:]
    if not targets:
        print("用法：python final_secrecy_audit.py <路径...>")
        return 2

    print("═" * 94)
    print("  保密终检 · 公开面专项")
    print("═" * 94)

    total_files = 0
    all_hits = []
    for t in targets:
        if os.path.isfile(t):
            files = [t]
        else:
            files = []
            for dp, dn, fn in os.walk(t):
                dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__")]
                for f in fn:
                    files.append(os.path.join(dp, f))
        hits = []
        for p in files:
            if not p.endswith((".md", ".html", ".txt", ".py", ".json", ".yml", ".yaml", ".css", ".js")):
                continue
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            total_files += 1
            for i, line in enumerate(txt.split("\n"), 1):
                if not line.strip():
                    continue
                if line_allowed(line):
                    continue
                for name, pat in REDLINE + INTERNAL:
                    m = pat.search(line)
                    if m:
                        hits.append((p, i, name, m.group(0)[:56], line.strip()[:78]))
        label = os.path.basename(t.rstrip("/")) or t
        print("\n▸ %-22s %d 个文件 —— %s"
              % (label, len(files), "✅ 零命中" if not hits else "🔴 %d 处" % len(hits)))
        for p, i, name, val, ctx in hits[:14]:
            print("   🔴 %-16s %s  «%s»" % (name, val, ctx))
        all_hits += hits

    print("\n" + "═" * 94)
    print("  扫描文件 %d 个 · 命中 %d 处" % (total_files, len(all_hits)))
    if all_hits:
        print("\n  ── 按规则汇总 ──")
        from collections import Counter
        c = Counter(h[2] for h in all_hits)
        for k, v in c.most_common():
            print("    %-20s %d 处" % (k, v))
    print("  总判定：%s" % ("✅ 保密合规 —— 零泄漏" if not all_hits
                            else "❌ %d 处需处理" % len(all_hits)))
    print("═" * 94)
    return 0 if not all_hits else 1


if __name__ == "__main__":
    sys.exit(main())
