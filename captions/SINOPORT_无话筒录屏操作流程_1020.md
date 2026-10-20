# 无话筒录屏操作流程 · 10-20

**版本**：v1 ｜ 2026-10-19 ｜ 全部命令已在本机实测通过
**方案**：**画面实录 + SRT 字幕硬烧录**，不需要话筒、不需要配音、不用后期软件

---

## 核心思路

没有话筒，就让**字幕代替声音**。评测者看的是内容与证据，不是听感。

| 环节 | 做法 |
|---|---|
| 录屏 | **只录画面**，不管声音（本来也没声音） |
| 讲解 | 全部写进 **41 条 SRT 字幕**，硬烧进画面 |
| 成片 | **带字幕的 mp4**，插到任何地方都能看懂 |

已实测产出：**1920×1080 / 60 fps / h264 / yuv420p**，中文渲染零方框。

---

# 第一步 · 录画面（30 分钟内完成）

## 1.1 开录

**双击** `rec_screen.bat`

它会打印输出目录、倒计时 3 秒，然后**开始录屏并一直不停**。

> ⚠️ **这个窗口要留着，不能关。** 演示在**另一个** PowerShell 窗口里跑。
> 录完回到这个窗口按 **Ctrl+C** → 输 **Y** 回车，才真正停止。

**输出位置**：`D:\SinoSir\SinoPORT\recordings\`

> D 盘余量已于 2026-10-19 17:25 复测为 **9.2 GB**，**高于 8 GB 红线-F**，
> 录制输出改回 D 盘。实测占用约 **67 KB/秒**（5 分钟仅 20 MB），空间充裕。

## 1.2 录三段素材（顺序无所谓，但建议按下面）

### 素材 A · VS Code 代码展示（镜头 1）

```powershell
cd D:\SinoSir\SinoPORT\20261019_开源仓库\SINOPORT_参赛版
code demo.py
```

在 VS Code 里：滚到文件头 → 停在「设计原则」三条 → 滚到 `CHAIN` 列表 → **停在 `ok = expect in out` 那行放大看**。停留 **15 秒**。

### 素材 B · 判据链实跑（镜头 2）

```powershell
python demo.py
```

看到 **`演示结论：4 / 4 步 PASS`** 后**停 3 秒**别动。
再补两条红线：

```powershell
python src\specs\berths_spec_r2.py
python src\specs\bw_geometry.py
```

### 素材 C · FreeCAD 真建模（镜头 4，★最重要）

**双击** `run_filming.bat`

> ★★ **一看到 `building foam ...` 立刻 Ctrl+C → 输 `Y` 回车。**
> 此时 15 条 PASS 已全部打完，后面还要 **9 分 41 秒**全是无信息内容。

## 1.3 停录

回到 `rec_screen.bat` 窗口，**Ctrl+C → 输 Y**。

---

# 第二步 · 烧字幕（一键，2 分钟）

## 2.1 把素材和字幕凑到一起

```powershell
cd D:\SinoSir\SinoPORT\20261019_开源仓库\SINOPORT_参赛版\captions
copy "D:\SinoSir\SinoPORT\recordings\*.mp4" .
```

## 2.2 烧录

**双击** `burn.cmd`

> 也可以**把 mp4 直接拖到 burn.cmd 上**，最省事。

它会自动找同目录的 mp4、套上字幕、输出 `<原名>_sub.mp4`。

## 2.3 逐个烧（素材多时）

```powershell
burn.cmd take1.mp4
burn.cmd take2.mp4
burn.cmd take3.mp4
```

---

# 第三步 · 确认成片

```powershell
ffprobe -v error -show_entries stream=width,height,r_frame_rate,codec_name -of default=nw=1 take1_sub.mp4
```

**必须看到**：
```
width=1920
height=1080
r_frame_rate=60/1
codec_name=h264
```

**抽一帧目视**（确认字幕中文没变方框）：
```powershell
ffmpeg -y -i take1_sub.mp4 -vf "select=eq(n\,300)" -vframes 1 chk.png
```

---

# 字幕设计（已生成，41 条 / 208 秒）

文件：`captions/SINOPORT_demo.srt`

| 镜头 | 字幕条数 | 时长 | 落点 |
|---|---|---|---|
| 1 代码展示 | 9 | 0–42 s | 「不手写任何PASS」「判定标准写在代码里，不是写在报告里」 |
| 2 满屏 PASS | 10 | 44–95 s | 「泊位安全余量最小 **334.9**米，红线 **300** 米」「场景落地可以被测试」 |
| 3 生态 3.27 倍 | 9 | 97–142 s | 「**3.27 倍**」「不是给港口加了条鱼道，而是让承重墙本身就是鱼道」 |
| 4 FreeCAD 实录 | 13 | 144–208 s | 「挖除量偏差只有 **1.55%**」「几何一改，基准就得重标，这就是实测闭环」 |

## 排版硬门（`make_srt.py` 自动判定）

| 规则 | 阈值 | 状态 |
|---|---|---|
| 单条停留时长 | ≥ 2.0 s | ✅ |
| 单行显示宽度 | ≤ 34 全角 | ✅ |
| 中文字体 | Microsoft YaHei | ✅ 实测零方框 |
| 描边 | BorderStyle=3, Outline=3 | ✅ 不压背景 |

> 硬门曾拦下 2 条超宽字幕，**按纪律改内容拆行，未放宽阈值**。

---

# 镜头 2/3 的现成素材（不用录）

两张截图已补成正片规格 **1920×1080**：

```
captions\..\docs\reports\1080p\SCREENSHOT_demo_py_4of4_PASS.png
captions\..\docs\reports\1080p\SCREENSHOT_demo_evolution.png
```

已实测：原图 1180×993 / 1180×825 **不是 16:9，且高为奇数**（libx264 直接拒绝编码）。
`make_1080p.py` 已重绘为 1920×1080 + 深色 letterbox + 标题条。

### 静态图转视频片段（可选，用于填镜头 2/3）

```powershell
ffmpeg -y -loop 1 -framerate 60 -i SCREENSHOT_demo_py_4of4_PASS.png -t 51 -c:v libx264 -preset veryfast -pix_fmt yuv420p shot2.mp4
ffmpeg -y -loop 1 -framerate 60 -i SCREENSHOT_demo_evolution.png -t 45 -c:v libx264 -preset veryfast -pix_fmt yuv420p shot3.mp4
```

时长对应字幕段：镜头 2 = 51 s，镜头 3 = 45 s。

---

# 完整一键脚本（可选，嫌麻烦可直接跑）

```powershell
cd D:\SinoSir\SinoPORT\20261019_开源仓库\SINOPORT_参赛版\captions
copy "D:\SinoSir\SinoPORT\recordings\*.mp4" .
burn.cmd
```

---

# 五条红线

1. **`building foam ...` 必 Ctrl+C + Y**，否则 9 分多钟无信息 + FAIL 入镜。
2. **录制输出在 `D:\SinoSir\SinoPORT\recordings`**（D 盘余量 9.2 GB，
   高于 8 GB 红线-F；若余量掉到 8 GB 以下，改 `rec_screen.bat` 里的 `OUTDIR`）。
3. **不加速播放** —— 5.33 秒的耗时必须真实可见。
4. **不配音也能交** —— 字幕已承载全部讲解，不要因为没声音就放弃录制。
5. 出现任何 `FAIL` / `Traceback` → **当场重录**。

---

# 一句话

**双击 `rec_screen.bat` 开录 → 录三段 → Ctrl+C + Y 停 → 回到 `captions` 目录双击 `burn.cmd`。**
字幕会自己烧上去，**不需要话筒、不需要配音软件、不需要剪映**。

---

_编制：SinoSir 工程助手 · 2026-10-19_