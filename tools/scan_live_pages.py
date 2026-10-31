# -*- coding: utf-8 -*-
"""
20261031 · 公网死链全量扫描（工业风网页版）
================================================================================
用途：把两份新页面 + 双端 README 里出现的**全部外链**逐条实测，
      并把站内相对链接解析到 Pages 实际路径后一起验证。

★ GitHub 链接需代理且本地网络会瞬时抖动 → 直连/代理双通道 + 重试。

用法：python scan_live_pages.py <证据页url> <映射表url>
"""
import re
import subprocess
import sys
import urllib.parse

BASE = "https://sinoshop-open.github.io/webpage"

PAGES = [
    ("证据页", BASE + "/docs/evidence/"),
    ("映射表", BASE + "/docs/datasets/"),
    ("旧页重定向", BASE + "/docs/evidence_assets.html"),
    ("Gitee 主仓 README", "https://gitee.com/sinoshop/SinoPORT"),
    ("GitHub 主仓 README", "https://github.com/SINOSHOP-OPEN/SinoPORT"),
]


def fetch(url):
    is_gh = "github.com" in url or "githubusercontent.com" in url
    attempts = [["--retry", "2"], ["--retry", "2", "-x", "http://127.0.0.1:7890"]] \
        if is_gh else [["--retry", "2"]]
    code = "ERR"
    body = ""
    for extra in attempts:
        cmd = ["curl", "-sL", "-w", "\n__CODE__%{http_code}", "-m", "35"]
        cmd += extra
        cmd.append(url)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=50)
            out = r.stdout
            m = re.search(r"__CODE__(\d{3})\s*$", out)
            code = m.group(1) if m else "ERR"
            body = out[:m.start()] if m else out
        except Exception:
            code = "ERR"
        if code == "200":
            break
    return code, body


def absolutize(href, page_url):
    if href.startswith(("http://", "https://", "#", "mailto:")):
        return href
    if href.startswith("/"):
        return "https://sinoshop-open.github.io" + href
    return urllib.parse.urljoin(page_url, href)


def main():
    dead = []
    total = 0
    print("═" * 88)
    print("  公网死链全量扫描")
    print("═" * 88)

    for label, url in PAGES:
        code, body = fetch(url)
        print("\n▸ %s  %s" % (label, url))
        print("  页面自身: %s" % code)
        if code != "200":
            dead.append((label, url, code))
            continue
        # ★ 非 HTML 资源（.py / .md / .json 等）里的文本不是「页面链接」——
        #   那是源码内容（如 Python 的 %s 占位符），不参与死链判定。
        if not re.search(r'<html|<a\s|<body', body[:4000], re.I):
            print("  （源码资源，跳过内链解析）")
            continue
        hrefs = re.findall(r'<a[^>]+href="([^"]+)"', body)
        hrefs += re.findall(r'<img[^>]+src="([^"]+)"', body)
        seen = set()
        uniq = []
        for h in hrefs:
            a = absolutize(h, url)
            if a in seen or a.startswith("#"):
                continue
            seen.add(a)
            uniq.append(a)
        print("  页面内链接 %d 条 —— 逐条实测：" % len(uniq))
        for a in uniq:
            c, _ = fetch(a)
            total += 1
            ok = (c == "200")
            if not ok:
                dead.append((label, a, c))
            print("    %s %s  %s" % ("✅" if ok else "🔴", c, a[:96]))
        print("  小计：%d 条" % len(uniq))

    print("\n" + "═" * 88)
    print("  统计：共测 %d 条外链 · 死链 %d 条" % (total, len(dead)))
    for l, u, c in dead:
        print("    🔴 %s  [%s]  %s" % (c, l, u[:88]))
    print("  总判定：%s" % ("✅ 零死链" if not dead else "❌ %d 条死链" % len(dead)))
    print("═" * 88)
    return 0 if not dead else 1


if __name__ == "__main__":
    sys.exit(main())
