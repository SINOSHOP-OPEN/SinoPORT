# -*- coding: utf-8 -*-
"""生成 SINOPORT 演示终端截图（demo.py 4/4 PASS + demo_evolution.py 参数进化）"""
import os
from PIL import Image, ImageDraw, ImageFont

F = r"C:\Windows\Fonts"
mono = ImageFont.truetype(os.path.join(F, "consola.ttf"), 15)
cn = ImageFont.truetype(os.path.join(F, "msyh.ttc"), 15)

REPO = r"D:\SinoSir\SinoPORT\20261019_开源仓库\SINOPORT_参赛版"


def render(lines, out, title, cmdline):
    W, pad, lh = 1180, 18, 21
    H = 34 + pad + lh + 8 + lh * len(lines) + 30
    img = Image.new("RGB", (W, H), (24, 26, 32))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 34], fill=(38, 42, 52))
    d.ellipse([14, 13, 24, 23], fill=(237, 106, 94))
    d.ellipse([30, 13, 40, 23], fill=(245, 191, 79))
    d.ellipse([46, 13, 56, 23], fill=(98, 198, 85))
    d.text((70, 9), title, font=cn, fill=(220, 224, 232))
    y = 44 + pad
    d.text((pad, y), cmdline, font=cn, fill=(120, 200, 255))
    y += lh + 8
    d.rectangle([pad - 4, y - 6, W - pad, y + lh * len(lines) + 4], fill=(18, 20, 25))

    def is_cjk(ch):
        return "\u2e80" <= ch <= "\u9fff" or "\uff00" <= ch <= "\uffef" or "\u3000" <= ch <= "\u303f"

    def mixed(x, yy, s, color):
        for ch in s:
            f = cn if is_cjk(ch) else mono
            d.text((x, yy), ch, font=f, fill=color)
            x += d.textlength(ch, font=f)
        return x

    for i, ln in enumerate(lines):
        c = (214, 218, 226)
        s = ln.strip()
        if s.startswith("PASS"):
            c = (126, 211, 133)
        elif "FAIL" in s or "BLOCKED" in s:
            c = (237, 106, 94)
        elif s.startswith("$") or "演示结论" in s or "VERIFY" in s:
            c = (245, 191, 79)
        mixed(pad, y + i * lh, ln[:150], c)
    d.rectangle([0, H - 30, W, H], fill=(38, 42, 52))
    d.text((pad, H - 23), "PowerShell - sinoport-demo", font=cn, fill=(140, 146, 158))
    img.save(out)
    print("saved", out, img.size)


def load(p):
    return [l for l in open(p, encoding="utf-8", errors="replace").read().splitlines() if l.strip()]


T = r"C:\Users\Administrator\AppData\Local\Temp"
demo = load(T + r"\demo_out.txt")
evo = load(T + r"\demo_evo.txt")

render(demo[-42:], REPO + r"\SCREENSHOT_demo_py_4of4_PASS.png",
       "SinoPORT demo.py - 4 / 4 PASS", r"PS D:\SinoSir\SinoPORT\20261019_开源仓库\SINOPORT_参赛版> python demo.py")
render(evo[-34:], REPO + r"\SCREENSHOT_demo_evolution.png",
       "SinoPORT demo_evolution.py - 3.27x", r"PS D:\SinoSir\SinoPORT\20261019_开源仓库\SINOPORT_参赛版> python demo_evolution.py")