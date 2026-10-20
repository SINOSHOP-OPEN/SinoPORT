# -*- coding: utf-8 -*-
"""把终端截图补成正片规格 1920x1080（深色letterbox + 标题条）。

原截图1180x993 / 1180x825，不是 16:9，且高为奇数（libx264 不收）。
本脚本重绘为 1920x1080，可直接进剪辑与烧字幕。
产物：docs/reports/1080p/<同名>.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

F = r"C:\Windows\Fonts"
cn = ImageFont.truetype(os.path.join(F, "msyh.ttc"), 34)
cnb = ImageFont.truetype(os.path.join(F, "msyhbd.ttc"), 36)

SRC_DIR = r"D:\SinoSir\SinoPORT\20261019_开源仓库\SINOPORT_参赛版\docs\reports"
DST_DIR = os.path.join(SRC_DIR, "1080p")
os.makedirs(DST_DIR, exist_ok=True)

BG = (14, 16, 21)
BAR = (24, 27, 34)
TITLE = {
    "SCREENSHOT_demo_py_4of4_PASS.png":
        "SinoPORT demo.py  —  4 / 4 步 PASS（实测终端实录）",
    "SCREENSHOT_demo_evolution.png":
        "SinoPORT demo_evolution.py  —  集成式生态通道 3.27 倍（实测终端实录）",
}

W, H = 1920, 1080
BAR_H = 74
PAD = 18

for name, title in TITLE.items():
    src = os.path.join(SRC_DIR, name)
    im = Image.open(src).convert("RGB")

    box_w = W - PAD * 2
    box_h = H - BAR_H - PAD * 2
    scale = min(box_w / im.width, box_h / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)

    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, W, BAR_H], fill=BAR)
    d.text((36, (BAR_H - 44) // 2), title, font=cnb, fill=(226, 231, 240))

    ox = (W - nw) // 2
    oy = BAR_H + PAD + (box_h - nh) // 2
    canvas.paste(im.resize((nw, nh), Image.LANCZOS), (ox, oy))
    d.rectangle([ox - 1, oy - 1, ox + nw, oy + nh], outline=(58, 64, 78), width=2)

    out = os.path.join(DST_DIR, name)
    canvas.save(out)
    chk = Image.open(out)
    assert chk.size == (W, H), chk.size
    print("OK  %-42s %s -> %s  %s  %.0f KB"
          % (name, im.size, (W, H), out, os.path.getsize(out) / 1024))

print("1080p 素材就绪:", DST_DIR)
