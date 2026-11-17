#!/usr/bin/env python3
"""SINOSHOP 公开层尺寸脱敏扫描器（Public-Layer Sanitizer）

================================ 设计原则 ================================
本脚本只描述「泄露的**形状**」，不包含任何「工程**数值**」：

  · 规则形态公开 —— 「数字 + 米制」「三维尺寸串」「密度量纲」等正则模式
    对所有贡献者可见，任何人都能自查、能复现、能提 PR 修正误报。
  · 具体词表保密 —— 工程的真实尺寸真值、内部控制变量名清单保存在
    内控侧（受控层），**绝不进入公开仓库**。

这一取舍遵循「结论与底牌分离」原则：
公开层告诉外界「我们禁止披露物理尺寸」这一**规则**，
而不告诉外界「我们具体在防哪些数值」这一**底牌**。

========================================================================

用法：
    python3 scripts/ci/scan_public_layer.py [目标路径]     # 扫描目录树
    python3 scripts/ci/scan_public_layer.py --msg <文件>     # 扫描提交信息
    python3 scripts/ci/scan_public_layer.py --strict <路径>  # PDF 未扫描时也判 FAIL

退出码：
    0 = PASS
    1 = FAIL（存在命中）
    2 = BLOCKED（无法完成扫描 / PDF 层不可用且处于 strict 模式）

依赖：
    仅需 Python 3.8+。PDF 层需 pymupdf（缺失则跳过并显式告警，不伪造 PASS）。
"""

import os
import re
import subprocess
import sys

# ─────────────────────────── 一、通用规则形态 ───────────────────────────
# 说明：以下全部是「量纲模式」，不含任何工程真值。
# 数字边界用 (?<![\d.]) / (?![0-9A-Za-z]) 而非 \b ——
# 中文属 Unicode 词字符，\b 在「圆<数字>m的」处不成立，会造成系统性漏报。

_R_BARE_M = re.compile(r"(?<![\d.])\d{1,5}(?:\.\d+)?\s?[mM](?![0-9A-Za-z])")
_R_CN_M = re.compile(r"[一二三四五六七八九十百千万零两数几]+\s*[米公尺]")
_R_AR_CN_M = re.compile(r"(?<![\d.])\d{1,5}(?:\.\d+)?\s*(?:毫米|厘米|公分|公里|公尺|米)(?![一-鿿])")
_R_AR_CN_M_LOOSE = re.compile(r"(?<![\d.])\d{1,5}(?:\.\d+)?\s*(?:毫米|厘米|公分|公里|公尺|米)")
# 「米」作名词时常见的非量纲搭配（粮食 / 器件 / 行当）——
# 这些后面跟的汉字不是量词/修饰语，据此排除，避免误报。
_M_NOT_DIM_AFTER = set("粒饭粉丝带格店市摊业制表线型圈球团段期批层列组件")
_R_3D = re.compile(r"\d{1,5}\s*[×xX]\s*\d{1,5}\s*[×xX]\s*\d{1,5}")
_R_DENSITY = re.compile(r"\d{2,4}\s*[-–~]\s*\d{2,4}\s*(?:kg/m³|t/m³|g/cm³|kg/m3|t/m3)")
BANNED_RE = [
    (_R_BARE_M, "阿拉伯数字+米制"),
    (_R_CN_M, "中文数字+米制"),
    (_R_AR_CN_M, "阿拉伯数字+中文米制"),
    (_R_3D, "三维尺寸串"),
    (_R_DENSITY, "密度量纲"),
]
# 注：「裸四位以上数值」不纳入规则集。理由：物理尺寸必带米制量纲、
# 材料密度必带质量/体积量纲，裸数值（时间戳、哈希、牛顿值、分辨率）
# 不构成尺寸披露。文件名层的尺寸代号另有专用规则。

# ─────────────────────── 二、语境豁免（仅外部工况/媒体参数） ───────────────────────
# 铁律：豁免词**不得**使用层级代号（L1/L2/L3/C-1 之类）充数。
# 否则「……属受控层，壳体宽 <尺寸>」这类同句真实尺寸会被整句放过。
_CTX_EXTERNAL = ("浪高", "浪况", "浪级", "风浪", "台风", "钱塘江", "潮差",
                 "水位", "河床", "水深", "波高", "标高", "波浪")
_CTX_MEDIA = ("分辨率", "像素", "画幅", "帧率", "fps", "px", "分辨率",
              "MP4", "1080p", "4K", "视频", "渲染", "切片")
_CTX_NON_DIM = ("版本", "修订", "哈希", "sha", "commit", "发布", "生效",
                "日期", "年份", "Copyright", "Apache", "许可证")

# ─────────────────────────── 三、文件名层 ───────────────────────────
_NAME_M = re.compile(r"(?<![0-9A-Za-z])\d{3,5}(?=[_-](?:m\b|mm\b|cm\b|meter|metre))", re.IGNORECASE)

TEXT_EXT = (".md", ".txt", ".html", ".htm", ".py", ".js", ".ts", ".tsx", ".jsx",
            ".json", ".yaml", ".yml", ".xml", ".csv", ".sh", ".bat", ".ps1",
            ".c", ".h", ".cpp", ".hpp", ".rs", ".go", ".java", ".toml", ".ini")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "dist", "build", ".mypy_cache", ".pytest_cache"}
MAX_FILE_BYTES = 8 << 20          # 8 MiB（用移位写法，避免脚本内出现裸四位数值）


def _ctx(text, start, end, pad=6):
    """取命中点邻域文本。pad 必须足够小 —— 窗口过大会让同句的
    合规语境词把同句的真实尺寸一并放过（同 V1.0 的层级代号豁免毛病）。
    另：合规形态一律是「浪高 尺度」「尺度 浪高」这种数值与语境词相邻的写法，
    故取 6 字符窗口已足够覆盖。"""
    return text[max(0, start - pad):end + pad].replace("\n", " ")


def _exempt(label, token, ctx):
    """判定命中点是否属于允许公开的语境。"""
    c = ctx.lower()
    if label in ("阿拉伯数字+米制", "中文数字+米制", "阿拉伯数字+中文米制"):
        # 外部工况（浪高/水文）与媒体参数（分辨率）属结论级公开信息
        if any(a in ctx for a in _CTX_EXTERNAL):
            return True
        if any(a in c for a in _CTX_MEDIA):
            return True
        # 量级表述属宏观描述，只对「中文数字+米制」生效。
        # 「<阿拉伯数字>m 级别」是具体值，仍必须拦下。
        if label == "中文数字+米制" and any(a in ctx for a in ("量级", "量值", "级别")):
            return True
        return False
    if label == "三维尺寸串":
        if re.search(r"(?:分辨率|像素|画幅|画面|矩阵)\s*[^\d]{0,6}" + re.escape(token), ctx):
            return True
        return any(a in c for a in _CTX_MEDIA)
    if label == "密度量纲":
        # 密度属材料配方层，禁止公开 —— 不设语境豁免
        return False
    return False


def scan_text(text, src):
    hits = []
    for pat, label in BANNED_RE:
        for m in pat.finditer(text):
            token = m.group(0)
            ctx = _ctx(text, m.start(), m.end())
            if _exempt(label, token, ctx):
                continue
            hits.append((src, label, token, ctx.strip()[:80]))
    # 松弛版：单位后接汉字时，只有确属「米」的名词搭配才排除，
    # 其余（如「<数值>米示范段」）判为命中 —— 宁可误报不可漏报。
    for m in _R_AR_CN_M_LOOSE.finditer(text):
        if m.group(0) in (x[2] for x in hits if x[1] == "阿拉伯数字+中文米制"):
            continue
        nxt = text[m.end():m.end() + 1]
        if nxt and nxt in _M_NOT_DIM_AFTER:
            continue
        ctx = _ctx(text, m.start(), m.end())
        if _exempt("阿拉伯数字+中文米制", m.group(0), ctx):
            continue
        hits.append((src, "阿拉伯数字+中文米制", m.group(0), ctx.strip()[:80]))
    return hits


def scan_name(name, src):
    """文件名层 —— 与正文同口径：数字+米制 / 密度量纲 / 尺寸代号后缀。"""
    hits = []
    for m in _NAME_M.finditer(name):
        hits.append((src, "文件名尺寸代号", m.group(0), name))
    # 文件名里出现「数字+米制」同样是尺寸代号（形如「…_<数值>m」后缀）
    for pat, label in BANNED_RE:
        for m in pat.finditer(name):
            hits.append((src, "文件名-" + label, m.group(0), name))
    return hits


def scan_pdf(path, rel):
    """PDF 内嵌文本扫描。pymupdf 不可用时返回 (None, 提示)。"""
    try:
        import pymupdf  # noqa
    except Exception:
        try:
            import fitz as pymupdf  # noqa
        except Exception:
            return None, "pymupdf 不可用 → PDF 层未扫描（需人工核验）"
    hits = []
    try:
        doc = pymupdf.open(path)
        for pno in range(len(doc)):
            t = doc[pno].get_text()
            if t:
                hits += scan_text(t, "%s#p%d" % (rel, pno + 1))
        doc.close()
    except Exception as e:
        return None, "PDF 解析失败：%s" % str(e)[:80]
    return hits, None


def iter_dirs(root):
    """单独产出目录（空目录名同样可能带尺寸代号）。"""
    if os.path.isfile(root):
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".git")]
        for d in dirnames:
            yield os.path.join(dirpath, d)


def iter_files(root):
    """产出待扫描的文件。"""
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".git")]
        for fn in filenames:
            yield os.path.join(dirpath, fn)


def scan_tree(root, strict=False):
    hits = []
    n_text = n_pdf = 0
    pdf_warn = None
    # 目录名层（空目录也要扫）
    for d in iter_dirs(root):
        rel = os.path.relpath(d, root)
        hits += scan_name(os.path.basename(d), rel)
    for p in iter_files(root):
        rel = os.path.relpath(p, root)
        # 文件名层
        for part in rel.replace("\\", "/").split("/"):
            hits += scan_name(part, rel)
        ext = os.path.splitext(p)[1].lower()
        try:
            size = os.path.getsize(p)
        except OSError:
            continue
        if size > MAX_FILE_BYTES:
            continue
        if ext == ".pdf":
            h, warn = scan_pdf(p, rel)
            if warn:
                pdf_warn = warn
            else:
                n_pdf += 1
                hits += h
            continue
        if ext not in TEXT_EXT:
            continue
        try:
            with open(p, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        if b"\x00" in raw[:4 << 10]:
            continue
        text = raw.decode("utf-8", "ignore")
        if not text.strip():
            continue
        n_text += 1
        hits += scan_text(text, rel)
    return hits, n_text, n_pdf, pdf_warn


def scan_msg_file(path):
    try:
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8", "ignore")
    except OSError as e:
        print("❌ 无法读取提交信息文件：%s" % e)
        return 1
    hits = scan_text(text, os.path.basename(path))
    if hits:
        print("🚫 提交信息命中公开层脱敏规则：")
        for h in hits:
            print("   ✗ [%s] %s   ← %s" % (h[1], h[2], h[3]))
        print("\n提交信息只写宏观描述：做了什么、为什么改、影响哪一层。")
        print("物理参数 / 内部编号 / 修订细节 / 底牌一律不进提交信息。")
        return 1
    return 0


def report(hits, n_text, n_pdf, pdf_warn):
    print("=" * 66)
    print("SINOSHOP 公开层尺寸脱敏扫描")
    print("=" * 66)
    print("已扫描文本文件：%d　已扫描 PDF：%d" % (n_text, n_pdf))
    if pdf_warn:
        print("⚠️  %s" % pdf_warn)
    if not hits:
        print("✅ PASS —— 公开层未检出尺寸 / 密度类泄露。")
        return 0
    print("🚫 FAIL —— 检出 %d 项命中：" % len(hits))
    byfile = {}
    for src, label, token, ctx in hits:
        byfile.setdefault(src, []).append((label, token, ctx))
    for src in sorted(byfile):
        print("\n  ▸ %s" % src)
        for label, token, ctx in byfile[src]:
            print("      [%s] %s" % (label, token))
            print("         上下文：%s" % ctx)
    print("\n处置口径：尺寸 / 容积 / 重量 / 材料密度属受控范围，")
    print("公开层请改用「按受控口径」「量级表述」「见受控层文档」等措辞。")
    return 1


def main(argv):
    args = argv[1:]
    if not args:
        args = ["."]
    if args[0] == "--msg":
        if len(args) < 2:
            print("❌ --msg 需要提供文件路径")
            return 2
        return scan_msg_file(args[1])
    strict = "--strict" in args
    paths = [a for a in args if not a.startswith("--")]
    root = paths[0] if paths else "."
    if not os.path.exists(root):
        print("❌ 路径不存在：%s" % root)
        return 2
    hits, n_text, n_pdf, warn = scan_tree(root, strict)
    rc = report(hits, n_text, n_pdf, warn)
    if rc == 0 and strict and warn:
        print("❌ strict 模式：PDF 层未能扫描 → BLOCKED")
        return 2
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        sys.exit(2)
