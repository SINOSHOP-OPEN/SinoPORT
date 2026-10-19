# -*- coding: utf-8 -*-
"""标准连接件 CONN 修正前的只读实测（不保存、不改动源件）

船长指令（2026-10-17）：
  标准连接件：长 3 m、宽 27 m、高 = 工字平台模块的平台高 7.5 m
  删去内置直径 2 m 的生态鱼道（因 MOD-STD 与 MOD-DM 已具备通水功能）

本脚本只做事实采集，输出 JSON：
  A) CONN.FCStd 现状：真实三轴尺寸 / Z 范围 / 体积 / 面数 / 内腔结构
  B)鱼道是否存在：多高度剖面 + 圆孔检索（直径 2 m）
  C) MOD-STD 平台高裁定：7.500 m 柱长源件是否在库
  D) 目标尺寸推导

安全：源件只读打开，closeDocument 不保存。
用法：freecadcmd probe_conn_fix.py
"""
import os, json
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    os.pardir, os.pardir))
OUT = os.path.join(REPO, "docs", "reports", "CONN_FACTS_20261017.json")
# Source CAD parts are project assets, not repository source.
SRC = os.path.join(REPO, "_build", "FCStd")

import FreeCAD as App
import Part
from FreeCAD import Vector

rep = {"date": "2026-10-17", "ruling": {
    "length_mm": 3000.0, "width_mm": 27000.0, "height_mm": 7500.0,
    "note": "高 = 工字平台模块平台高 7.5 m = 工字墙榫卯柱长"},
    # ============================================================
    # 【2026-10-19 船长裁定 ·术语统一】
    # 「删除独立鱼道」的正名：不是砍掉生态连通，而是**升级**为
    #   **集成式多级活水生态通道** —— 融入承重结构的柱墙阵列。
    #
    # 传统做法：外挂独立鱼道（如七级结构）
    #   缺陷 1：占用额外空间（平面与剖面都要让出通道）
    #   缺陷 2：单独承受风浪，易被破坏，寿命短于主体结构
    #
    # 本方案：升级为 **MOD-STD 10 柱 5 墙 / MOD-DM 6 柱 3 墙** 阵列
    #   墙体既承担抗台风受力，其预留孔洞又构成多级活水生态通道
    #   → **结构承重与生态连通在拓扑层面融合**
    #   → 一套模具同时解决：抗台风 / 模块组装 / 生态通水 三大痛点
    #
    # 实测（模块 27x27x8 m，V6.4 §4.1.1 / §4.3 / §4.6.3）：
    #   承重孔洞（12 直通榫卯柱 phi300）    0.8482 m2
    #   压载水舱三管束（phi2000 x 3）       9.4248 m2
    #   合计贯通面积                      **10.2730 m2**
    #   = 被移除外挂鱼道（phi2000 单管 3.1416 m2）的 **3.27 倍**
    #   对应透水率 **1.4092%**（迎水面投影 729 m2 口径）
    #   （该数字为几何实算，非 CFD 实测；已在参赛材料中如实标注）
    # ============================================================
    "ruling2": {
        # 移除低效的独立鱼道，升级为 MOD-STD 模块的 10 柱 5 墙
        # （MOD-DM 为 6 柱 3 墙）集成生态通水孔
        "delete_fishway": True,
        "fishway_dia_mm": 2000.0,
        "reason": "MOD-STD 与 MOD-DM 均已具备通水功能",
        # ---- 2026-10-19 新增：正名与升级口径 ----
        "terminology": "集成式多级活水生态通道（非「外挂鱼道」）",
        "integrated_into": ["MOD-STD 10柱5墙", "MOD-DM 6柱3墙"],
        "upgrade_rationale":
            "传统独立鱼道占用额外空间且易受风浪破坏；本方案将其升级为"
            "融入承重结构的柱墙阵列——墙体既承担抗台风受力，"
            "其预留孔洞又构成多级活水生态通道，"
            "实现结构承重与生态连通的拓扑级融合。",
        "integrated_flow_area_m2": 10.2730,
        "removed_fishway_area_m2": 3.1416,
        "area_ratio": 3.27,
        "transmissivity_pct_front": 1.4092,
        "calibration": "几何实算（迎水面投影 729 m2 口径），非 CFD 实测",
    },
    "facts": {}, "derived": {}, "checks": []}


def chk(name, ok, detail):
    rep["checks"].append({"name": name, "result": "PASS" if ok else "FAIL",
                          "detail": str(detail)})
    print(("PASS  " if ok else "FAIL  ") + name + "  " + str(detail), flush=True)
    return ok


def dims(o):
    b = o.Shape.BoundBox
    return {"dim_mm": [round(b.XLength, 2), round(b.YLength, 2), round(b.ZLength, 2)],
            "x": [round(b.XMin, 2), round(b.XMax, 2)],
            "y": [round(b.YMin, 2), round(b.YMax, 2)],
            "z": [round(b.ZMin, 2), round(b.ZMax, 2)],
            "vol_m3": round(o.Shape.Volume / 1e9, 4),
            "faces": len(o.Shape.Faces), "solids": len(o.Shape.Solids),
            "shells": len(o.Shape.Shells), "valid": bool(o.Shape.isValid())}


# ---------- A) CONN 现状 ----------
p = os.path.join(SRC, "CONN.FCStd")
doc = App.openDocument(p)
for o in doc.Objects:
    if hasattr(o, "Shape") and not o.Shape.isNull():
        rep["facts"]["CONN"] = dims(o)
        print("=== CONN.FCStd 现状 ===", flush=True)
        print("  obj={} dim={}".format(o.Name, rep["facts"]["CONN"]["dim_mm"]),
              flush=True)
        print("  x={} y={} z={}".format(rep["facts"]["CONN"]["x"],
              rep["facts"]["CONN"]["y"], rep["facts"]["CONN"]["z"]), flush=True)
        print("  vol={} m3  faces={}  solids={}  shells={}".format(
            rep["facts"]["CONN"]["vol_m3"], rep["facts"]["CONN"]["faces"],
            rep["facts"]["CONN"]["solids"], rep["facts"]["CONN"]["shells"]),
            flush=True)
        sh = o.Shape

        # ---------- B) 多高度剖面：查内腔 / 鱼道 ----------
        b = sh.BoundBox
        slices = []
        print("\n=== CONN 多高度剖面（查内腔）===", flush=True)
        for frac in (0.05, 0.15, 0.25, 0.35, 0.5, 0.65, 0.75, 0.85, 0.95):
            z = b.ZMin + b.ZLength * frac
            try:
                sec = sh.slice(Vector(0, 0, 1), z)
                area = 0.0
                for w in sec:
                    try:
                        area += Part.Face(w).Area
                    except Exception:
                        pass
                rec = {"z": round(z, 1), "wires": len(sec),
                       "area_m2": round(area / 1e6, 4)}
                slices.append(rec)
                print("  z={:>8}  wires={:<4} area={} m2".format(
                    round(z, 1), len(sec), round(area / 1e6, 3)), flush=True)
            except Exception as e:
                slices.append({"z": round(z, 1), "error": repr(e)[:120]})
        rep["facts"]["CONN_slices"] = slices

        # ---------- B2) 圆柱面检索（鱼道应为 Φ2000 圆柱内壁）----------
        cyls = []
        for f in sh.Faces:
            s = f.Surface
            t = type(s).__name__
            if t == "Cylinder":
                cyls.append({"radius": round(s.Radius, 2),
                             "height": round(s.Radius and f.BoundBox.ZLength
                                             or 0, 2),
                             "area_m2": round(f.Area / 1e6, 4),
                             "center": [round(s.Center.x, 1), round(s.Center.y, 1),
                                        round(s.Center.z, 1)]})
        rep["facts"]["CONN_cylinders"] = cyls
        print("\n=== CONN 圆柱面检索（鱼道内壁）===", flush=True)
        if cyls:
            for c in cyls:
                print("  R={} (Φ{}) h={} area={} center={}".format(
                    c["radius"], round(c["radius"] * 2, 1), c["height"],
                    c["area_m2"], c["center"]), flush=True)
        else:
            print("  无圆柱面", flush=True)

        # 内腔体积占比：boundbox 体积 vs 实体体积
        bv = b.XLength * b.YLength * b.ZLength / 1e9
        rep["facts"]["CONN_bbox_vol_m3"] = round(bv, 4)
        rep["facts"]["CONN_fill"] = round(sh.Volume / 1e9 / bv, 4)
        print("\n  bbox_vol={} m3  solid_vol={} m3  fill={}".format(
            round(bv, 3), rep["facts"]["CONN"]["vol_m3"],
            rep["facts"]["CONN_fill"]), flush=True)
App.closeDocument(doc.Name)

# ---------- C) GROUP-30M 内的 CONN（交叉核对）----------
p2 = os.path.join(SRC, "GROUP-30M-GTC00001-V01.FCStd")
doc2 = App.openDocument(p2)
for o in doc2.Objects:
    if o.Name == "CONN" and hasattr(o, "Shape") and not o.Shape.isNull():
        rep["facts"]["GROUP30M_CONN"] = dims(o)
        print("\n=== GROUP-30M/CONN 交叉核对 ===", flush=True)
        print("  dim={}  x={}".format(rep["facts"]["GROUP30M_CONN"]["dim_mm"],
              rep["facts"]["GROUP30M_CONN"]["x"]), flush=True)
App.closeDocument(doc2.Name)

# ---------- D) 7.5 m 平台高柱源件是否在库 ----------
C7 = ROOT + "/20261015/_verify/COLUMN_7M5_BUILD_20261015.json"
if os.path.isfile(C7):
    c7 = json.load(open(C7, encoding="utf-8"))
    rep["facts"]["col7m5"] = {
        "col_L_mm": c7["col_L_mm"], "z_bot": c7["z_bot"], "z_top": c7["z_top"],
        "n": len(c7["columns"]),
        "step_dir": ROOT + "/20261015/_step_7m5_column"}
    print("\n=== 7.5 m 平台高裁定 ===", flush=True)
    print("  柱长 {} mm，Z[{}, {}]，{} 根".format(
        c7["col_L_mm"], c7["z_bot"], c7["z_top"], len(c7["columns"])), flush=True)
    sd = rep["facts"]["col7m5"]["step_dir"]
    if os.path.isdir(sd):
        rep["facts"]["col7m5"]["steps"] = sorted(os.listdir(sd))
        print("  STEP 目录{}（{} 个）".format(sd, len(rep["facts"]["col7m5"]["steps"])),
              flush=True)
else:
    rep["facts"]["col7m5"] = {"result": "MISSING"}

# ---------- E) 目标尺寸推导 ----------
cur = rep["facts"]["CONN"]["dim_mm"]
rep["derived"] = {
    "current_mm": cur,
    "target_mm": [3000.0, 27000.0, 7500.0],
    "delta_mm": [round(3000.0 - cur[0], 1), round(27000.0 - cur[1], 1),
                 round(7500.0 - cur[2], 1)],
    "length_is_x": True,
    "width_is_y": True,
    "height_is_z": True,
}
print("\n=== 目标 vs 现况 ===", flush=True)
print("  现况 X={} Y={} Z={}".format(*cur), flush=True)
print("  目标 X=3000 Y=27000 Z=7500", flush=True)
print("  差值X={} Y={} Z={}".format(*rep["derived"]["delta_mm"]), flush=True)

chk("CONN 现况长(X) 应为 3301 -> 目标 3000",
    abs(cur[0] - 3301.0) < 5.0,
    "实测 X={}".format(cur[0]))
chk("CONN 现况宽(Y) 应为 27301 -> 目标 27000",
    abs(cur[1] - 27301.0) < 5.0,
    "实测 Y={}".format(cur[1]))
chk("CONN 现况高(Z) 应为 6301 -> 目标 7500（= 7.5 m 平台高）",
    abs(cur[2] - 6301.0) < 5.0,
    "实测 Z={}（与 7.5 m 差 {} mm）".format(cur[2], round(7500.0 - cur[2], 1)))
chk("CONN 内置鱼道：检索 Φ2000 圆柱面",
    any(abs(c["radius"] - 1000.0) < 30.0 for c in rep["facts"]["CONN_cylinders"]),
    "找到 {} 个圆柱面，半径 {}".format(
        len(rep["facts"]["CONN_cylinders"]),
        [c["radius"] for c in rep["facts"]["CONN_cylinders"]]))
chk("7.5 m 平台高柱源件在库（COLUMN_7M5_BUILD）",
    rep["facts"].get("col7m5", {}).get("col_L_mm") == 7500.0,
    "柱长 {} mm，{} 根".format(rep["facts"].get("col7m5", {}).get("col_L_mm"),
                       rep["facts"].get("col7m5", {}).get("n")))

rep["stats"] = {"pass": sum(1 for c in rep["checks"] if c["result"] == "PASS"),
                "fail": sum(1 for c in rep["checks"] if c["result"] == "FAIL")}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nSTATS:", rep["stats"], flush=True)
print("OUT:", OUT, flush=True)
print("=== END ===", flush=True)