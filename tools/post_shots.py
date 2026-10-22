# -*- coding: utf-8 -*-
"""把两张实测截图挂到 Gitee Issue #IKORUR 与 PR #1 的评论区。
令牌从环境变量 gitee_token 取，明文不落盘。"""
import os
import json
import urllib.request
import urllib.parse

TOK = os.environ["gitee_token"]
BASE = "https://gitee.com/api/v5/repos/sinoshop/SinoPORT"
RAW = "https://gitee.com/sinoshop/SinoPORT/raw/feature/upgrade-eco-fishway-10p5w/docs/reports"
BLOB = "https://gitee.com/sinoshop/SinoPORT/raw/feature/upgrade-eco-fishway-10p5w/docs/reports"


def raw(method, url, data=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        r = urllib.request.urlopen(req, timeout=40)
        return r.status, r.read().decode("utf-8", "replace")
    except Exception as e:
        return getattr(e, "code", "ERR"), repr(e.read()[:300])


IMG1 = "SCREENSHOT_demo_py_4of4_PASS.png"
IMG2 = "SCREENSHOT_demo_evolution.png"

BODY = """## 实测证据挂载 · 软硬一体闭环

本条评论随重构分支 `feature/upgrade-eco-fishway-10p5w` 自动生成，
图片为**本机真实运行**的终端截图，非渲染图、非修图。

---

### ① `demo.py` —— 4 / 4 步 PASS

![demo.py 4/4 PASS]({b1}/{i1})

命令行：

```powershell
python demo.py
```

**结论**：`演示结论：4 / 4 步 PASS  （总耗时 5.33 s）`

四个判据源逐一通过：

| 判据源 | 结果 | 判定内容 |
|---|---|---|
| `pyramid_spec_r6.py` | **26/26 PASS** | 7 排 1/1/2/3/5/8/13 x 4 面 = **132 孔**，孔径 **D900**，单实体 `isValid()=True` |
| `bw_geometry.py` | **PASS** | 半圆防波堤单侧 **381 m** = 81+200+100，弦线 **R=1650**，9 开口 x 150 m |
| `berths_spec_r2.py` | **9/9 PASS** | 9 泊位全含于 R=1650 半圆内，**最小余量 334.9 m ≥ 安全红线 300 m** |
| `shore_spec_r2.py` | **23/23 PASS** | 岸边景观冬夏双状态，A→B→C→D 建造时序 |

### ② `demo_evolution.py` —— 集成式活水生态通道 3.27 倍

![demo_evolution]({b2}/{i2})

命令行：

```powershell
python demo_evolution.py
```

**结论**：贯通面积 **3.1416 m² → 10.2730 m²**，即 **3.27 倍**。

| 通水路径 | 规格 | 面积 |
|---|---|---|
| 承重预留孔洞 | 12 直通榫卯柱 φ300 mm | 0.8482 m² |
| 压载舱体三管束 | φ2000 mm x 3 | 9.4248 m² |
| **合计** | — | **10.2730 m²** |

被移除外挂鱼道（φ2000 单管）仅 3.1416 m²；
迎水面投影 729 m² 口径下几何透水率 **1.4092%**。

> **口径声明**：1.4092% 为**几何实算**，非 CFD 实测的流量交换率。
> **几何一改，基准必须重新标定** —— 孔径 1000→900 时实测系数
> K = **0.8609**（非 D² 外推的 0.8100），偏差由 +7.93% 收敛至 **+1.55%**。

---

**文件路径**（随代码入库）：
- [`docs/reports/{i1}`]({b1}/{i1})
- [`docs/reports/{i2}`]({b2}/{i2})

_本评论由 API 自动发布 · 令牌取自环境变量，明文未落盘_""".format(
    b1=BLOB, i1=IMG1, b2=BLOB, i2=IMG2
)

PR_BODY = BODY.replace(
    "## 实测证据挂载 · 软硬一体闭环",
    "## 实测 4/4 PASS 与 3.27 倍贯通面积验证通过",
).replace(
    "本条评论随重构分支",
    "**实测 4/4 PASS 与 3.27 倍贯通面积验证通过。**\n\n本条评论随重构分支",
)

jobs = [
    ("PR #1 评论", f"{BASE}/pulls/1/comments?access_token={TOK}", PR_BODY),
    ("Issue #IKORUR 评论", f"{BASE}/issues/IKORUR/comments?access_token={TOK}", BODY),
]

for name, url, body in jobs:
    st, d = raw("POST", url, {"body": body})
    ok = st in (200, 201)
    print(f"{name}: HTTP {st} {'OK' if ok else 'FAIL'}")
    if ok:
        try:
            j = json.loads(d)
            print("   id=", j.get("id"), " url=", j.get("url") or j.get("html_url"))
        except Exception:
            print("   ", d[:120])
    else:
        print("   ", d[:200])
