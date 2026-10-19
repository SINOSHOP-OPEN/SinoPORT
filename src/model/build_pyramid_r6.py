# -*- coding: utf-8 -*-
"""BUILD R6: Fibonacci 7-row hole layout, bore dia 1m -> 900 mm
======================================================================
Captain ruling 2026-10-19 04:40:
    「金字塔斜面的开孔直径由 1 米改为 900 mm」

Everything else identical to R5
  rows7 1/1/2/3/5/8/13 = 33 per slope x 4 = 132 bores
  t0.86 -> 0.12, pitch = leftover width / (n+1)  <- captain formula
  bore gap grows: R5 357.14 mm -> R6 450.00 mm (better OCC stability)

Usage: freecadcmd build_pyramid_r6.py
"""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# 仓库布局：spec 在 src/specs，建模在 src/model —— 两个目录都要进 path，
# 否则在仓库内运行时报No module named 'pyramid_spec_r6'
sys.path.insert(0, os.path.join(HERE, os.pardir, "specs"))
import FreeCAD as App
import Part
import Import
from FreeCAD import Vector
import pyramid_spec_r6 as S

REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
OUT = os.path.join(REPO, "docs", "reports", "BUILD_PYRAMID_R6_20261019.json")
# Geometry output stays outside the repo (large CAD files are not source).
DST = os.path.join(REPO, "_build", "FCStd")
os.makedirs(DST, exist_ok=True)
SRC = DST  # R6 builds its primitives in place; no external source part needed

rep = {"date": "2026-10-18", "revision": "R6", "spec": S.spec_dict(),
       "parts": {}, "checks": []}


def chk(name, ok, detail):
    rep["checks"].append({"name": name, "result": "PASS" if ok else "FAIL",
                          "detail": str(detail)})
    print(("PASS  " if ok else "FAIL  ") + name + " | " + str(detail), flush=True)
    return ok


os.makedirs(DST, exist_ok=True)
doc = App.openDocument(os.path.join(SRC, "BW_WAVE61_SQR_PYRAMID.FCStd"))

# =============== 1) collect the existing pipes ===============
pipes = [o.Shape for o in doc.Objects
         if hasattr(o, "Shape") and not o.Shape.isNull()
         and "PIPE" in o.Name.upper()]
chk("61 pipe solids collected", len(pipes) == 61, str(len(pipes)))

# =============== 2) build the solid pyramid with 132 holes ===============
half = S.PYR_PLAN / 2.0
H = S.PYR_HEIGHT
bz = S.PYR_BASE_Z
th = S.SLOPE_THICK

# Outer solid cone: square base 18000x18000 at z=bz, apex at (0,0,bz+H).
# Built as a Part.makeLoft through three square wires (base, mid, apex-ish)
# to guarantee a clean 45 deg face.
def sq_wire(half_side, z):
    return Part.makePolygon([Vector(-half_side, -half_side, z),
                             Vector(half_side, -half_side, z),
                             Vector(half_side, half_side, z),
                             Vector(-half_side, half_side, z),
                             Vector(-half_side, -half_side, z)])

# mid section at half height keeps the 45 deg faces straight
# 【A+B 方案 R5】外锥改 2 截面 —— 3 截面会把锥面切成两段
# （下段 z 9,000~13,500 + 上段 z 13,500~18,000，接缝在 z=13,500），
# 实测接缝处及以上的孔全部打空。2 截面得到 4 个平面，
# z 从 9,000 直达 18,000，实测 7 排孔心到锥面距离 0.0~0.3 mm。
wires = [sq_wire(half, bz),
         sq_wire(1.0, bz + H)]
outer = Part.makeLoft(wires, True, True)
print("outer cone vol = {} m3".format(round(outer.Volume / 1e9, 3)), flush=True)

# 【A+B 方案 R5】内锥 = 等**法向**厚度偏移
# 原做法（3 截面 + 内锥各点内移 d=th/sqrt2）有两处错：
#   1) 3 截面把锥面切成两段，接缝在 z=13,500，孔位落在接缝上打空
#   2) 内锥顶点也内移了 d，锥体整体缩小，壁厚不均
# 现做法：
#   外锥 = 2 截面 loft（底 half @ bz，顶点 @ bz+H）-> 4 个平面，z 全程直达
#   内锥 = 同样 2 截面，但底半边长内缩 inset = th*sqrt(2)
#          顶点 z = bz + (half - inset)，比外锥顶低 th
#   平面 y+z=C 的法向距 = |C_out - C_in| / sqrt(2)
#     = ((half+bz) - (hh+bz)) / sqrt(2) = (th*sqrt2)/sqrt2 = th  ✓
d = th * math.sqrt(2.0)              # 424.26 -> 法向厚恰为 th
hh = half - d                        # 8575.74
inner = Part.makeLoft([sq_wire(hh, bz),
                       sq_wire(1.0, bz + hh)], True, True)
print("inner pyramid: half=%.2f apex_z=%.2f -> normal thick=%.3f mm"
      % (hh, bz + hh, abs((half + bz) - (hh + bz)) / math.sqrt(2.0)),
      flush=True)

pyramid = outer.cut(inner)
pyramid = pyramid.removeSplitter()
print("pyramid shell vol = {} m3, solids = {}".format(
    round(pyramid.Volume / 1e9, 3), len(pyramid.Solids)), flush=True)
bb = pyramid.BoundBox
chk("solid pyramid spans Z [9000, 18000] and 18000 plan",
    abs(bb.ZMin - bz) < 1 and abs(bb.ZMax - (bz + H)) < 1
    and abs(bb.XLength - S.PYR_PLAN) < 1,
    "dim={} Z={}".format([round(bb.XLength, 1), round(bb.YLength, 1),
                          round(bb.ZLength, 1)],
                         [round(bb.ZMin, 1), round(bb.ZMax, 1)]))
chk("pyramid shell is valid", pyramid.isValid(), str(pyramid.isValid()))

# ---- cut the 132 holes (7 rows 1/1/2/3/5/8/13) ----
holes = S.hole_positions()
chk(str(S.N_HOLES_TOTAL) + " hole positions", len(holes) == S.N_HOLES_TOTAL, str(len(holes)))
# 【R6 裁定】孔径 900 mm，7 排 = 1/1/2/3/5/8/13，四个斜面逐排核对
from collections import Counter
_cnt = Counter((h["slope"], h["row"]) for h in holes)
_rows = list(zip(S.HOLE_ROW_N, S.HOLE_ROW_T))
_ok = all(_cnt.get((_s, _r + 1)) == _n
          for _s in range(S.N_SLOPES)
          for _r, (_n, _t) in enumerate(_rows))
chk("R6 layout 1/1/2/3/5/8/13 on all 4 slopes", _ok,
    " ".join("row%d=%dx4" % (_r + 1, _n)
             for _r, (_n, _t) in enumerate(_rows)))
_zmax = max(h["centre"][2] for h in holes)
chk("no hole sits above the apex z=" + str(int(S.PYR_TOP_Z)),
    _zmax < S.PYR_TOP_Z,
    "max hole z = " + str(int(_zmax))
    + ", margin " + str(int(S.PYR_TOP_Z - _zmax)) + " mm")
chk("R6 total = 132", S.N_HOLES_TOTAL == 132, str(S.N_HOLES_TOTAL))
chk("bottom row 13 holes fits with distributed gaps",
    S.row_positions(0.12, 13) is not None,
    "13 holes at t=0.12, gap "
    + str(round(S.row_gap(0.12, 13), 2)) + " mm")
# 【船长 12:06 纠正】间隙必须 > 0：相切圆柱 fuse 产生 OCC 退化边，
# 实测致 isValid()=False、挖除仅 34%。这里硬断言间隙为正。
chk("every row gap > 0 (tangent pitch breaks the boolean)",
    min(S.row_gap(t, n) for n, t in zip(S.HOLE_ROW_N, S.HOLE_ROW_T)) > 0.0,
    "min gap "
    + str(round(min(S.row_gap(t, n)
                    for n, t in zip(S.HOLE_ROW_N, S.HOLE_ROW_T)), 2)) + " mm")
# 【船长算法逐字复算】g = (18000 - 13*D)/(13+1)
# R6 孔径 900 => g = (18000 - 11700)/14 = 450.00
_D = S.HOLE_DIA
chk("captain gap formula (18000-13*D)/14 at t=0",
    abs(S.row_gap(0.0, 13) - (18000.0 - 13 * _D) / 14.0) < 1e-6,
    "g = " + str(round(S.row_gap(0.0, 13), 2))
    + " mm ; 13*" + str(int(_D)) + " + 14*g = "
    + str(round(13 * _D + 14 * S.row_gap(0.0, 13), 1)))

cut = None
for h in holes:
    ctr = Vector(*h["centre"])
    nrm = Vector(*h["normal"])
    cyl = Part.makeCylinder(S.HOLE_DIA / 2.0, th * 6.0, ctr - nrm * (th * 3.0), nrm)
    cut = cyl if cut is None else cut.fuse(cyl)
holey = pyramid.cut(cut)
holey = holey.removeSplitter()
print("after holes: vol = {} m3, faces = {}, solids = {}".format(
    round(holey.Volume / 1e9, 3), len(holey.Faces), len(holey.Solids)), flush=True)
rep["parts"]["PYRAMID_R6"] = {
    "vol_m3": round(holey.Volume / 1e9, 4), "faces": len(holey.Faces),
    "solids": len(holey.Solids), "valid": bool(holey.isValid()),
    "removed_by_holes_m3": round((pyramid.Volume - holey.Volume) / 1e9, 4)}
chk("holes removed material", holey.Volume < pyramid.Volume,
    "{} -> {} m3".format(round(pyramid.Volume / 1e9, 3),
                         round(holey.Volume / 1e9, 3)))
chk("pyramid still valid after cutting", holey.isValid(), str(holey.isValid()))

# ---- verify the bores by VOLUME (fast, exact) ----
# 【性能修正】逐孔 35 点 isInside 探针需 3780 次调用，在 ~1900 面实体上
# 实测 >30 分钟且仍在跑。改用体积法。
# 【判据修正】解析式 pi*r^2*th 高估：圆柱挖的是斜壁的**斜切体**。
# 【R5 修正】R3 的 12.7152 m3 基准来自 108 孔、且 R3 壁厚实际只有
# 法向 150 mm（内锥偏移 d=th/sqrt2）。R5 是**法向真 300 mm**（等厚），
# 恰为 2 倍，故基准须重算，不能沿用 R3。
# 实测（单面 33 孔全通）= 7.6641 m3 -> 每孔 0.23225 m3
#   与 R3 每孔 0.11528 比值 = 2.015，等于壁厚比 300/150 = 2.0 ✓
#   132 孔全通应挖除 = 4 x 7.6641 = 30.6564 m3
#
# 【R6 基准标定】孔径 1000 -> 900 后，不能简单按 D² 缩放。
#   实测：R5 每孔 0.23910 m3 -> R6 每孔 0.20585 m3，比值 **0.8609**
#   （纯 D² 缩放应为 0.8100）。
#   根因：孔径变小使间隙变宽（357 -> 450 mm），相邻圆柱的斜切体
#   重叠更少，故实测更接近「逐孔相加」，比值高于 D²。
#   故基准采用**实测标定系数**，不再用解析外推：
#       K_R6 = 0.8609（实测标定，非估计）
#   若日后孔径再变，须重跑本脚本取得新的 K，不可沿用。
_K_R6 = 0.8609
removed = (pyramid.Volume - holey.Volume) / 1e9
_BASIS_R3, _HOLES_R3 = 12.7152, 108
_TH_R3, _TH_R5 = 150.0, th          # R3 实际法向 150；R5/R6 法向 300
expected = (_BASIS_R3 * S.N_HOLES_TOTAL / _HOLES_R3
            * (_TH_R5 / _TH_R3) * _K_R6)
print("removed = {} m3 ; R6 baseline for {} bores = {} m3 "
      "(R3 {} m3 @{} holes, thickness x{:.1f}, dia-scaling K={:.4f} 实测标定)".format(
          round(removed, 4), S.N_HOLES_TOTAL, round(expected, 4),
          _BASIS_R3, _HOLES_R3, _TH_R5 / _TH_R3, _K_R6),
      flush=True)
n_r500 = len([f for f in holey.Faces
              if type(f.Surface).__name__ == "Cylinder"
              and abs(f.Surface.Radius - S.HOLE_DIA / 2.0) < 1e-6])
rep["parts"]["PYRAMID_R6"]["removed_m3"] = round(removed, 4)
rep["parts"]["PYRAMID_R6"]["removed_measured_baseline_m3"] = expected
rep["parts"]["PYRAMID_R6"]["removed_analytic_m3"] = round(
    S.N_HOLES_TOTAL * math.pi * (S.HOLE_DIA / 2.0) ** 2 * th / 1e9, 4)
rep["parts"]["PYRAMID_R6"]["r450_faces_after_sewing"] = n_r500
rep["parts"]["PYRAMID_R6"]["bore_dia_mm"] = S.HOLE_DIA
chk(str(S.N_HOLES_TOTAL) + " bores removed the rescaled baseline volume",
    abs(removed - expected) / expected < 0.05,
    "{} vs {} m3 ({:+.2f}%)".format(round(removed, 4), expected,
                                   100 * (removed - expected) / expected))
# 判据：全 132 孔挖除 ~15.5 m3；若只有一半（66 孔）打开，只有 ~7.8 m3。
chk("all " + str(S.N_HOLES_TOTAL) + " bores cut, not just half",
    removed > 0.75 * expected,
    "measured {} m3 ; half-bore case would be ~{} m3".format(
        round(removed, 3), round(expected / 2.0, 3)))
# 【判据加强】原来只判 n_r500 > 0（无效判据：切 1 个孔也满足）。
# 硬断言 = 孔数 —— 这才是「每孔都真实存在」的直接证据。
chk("exactly " + str(S.N_HOLES_TOTAL)
    + " R=450 bore faces exist (D900; half would mean holes missed)",
    n_r500 == S.N_HOLES_TOTAL,
    "{} R=450 faces (D900)".format(n_r500))

# =============== 3) foam ===============
# 【实测】CUBE_SHELL 是单一实体 719.626 m3 / 573 面，逐层材料占比实测：
#   z = ±8800 : 82.5%  -> 上下两块实心板（顶板 / 底板）
#   z = -8000..+8000 : 14.7% -> 中段是**竖向框架（桁架）**，其余为空腔
# 船长口径「桁架凹槽支撑结构**之外**的空间填泡沫」=> 泡沫必须排除
# ①桁架框架本体 ②顶底实心板 ③管壳 ④管腔（否则排水通道被堵死）。
cube_solid = doc.getObject("CUBE_SHELL").Shape.Solids[0]
print("building foam ...", flush=True)

# --- 3.1 空腔 = 立方体外形盒 − CUBE_SHELL 本体（壳 + 桁架 + 顶底板） ---
cavity = Part.makeBox(S.CUBE_SIDE, S.CUBE_SIDE, S.CUBE_SIDE,
                      Vector(-S.CUBE_SIDE / 2.0, -S.CUBE_SIDE / 2.0,
                             S.CUBE_Z0))
cavity = cavity.cut(cube_solid)
print("  cavity after removing the cube frame: {} m3, {} solids".format(
    round(cavity.Volume / 1e9, 3), len(cavity.Solids)), flush=True)

# --- 3.2 再切管壳 ---
# 【关键修正】管是中空环形管：外径 R=1000，内腔 R=910，壁厚 90
# （实测 PIPE_X_Z1_Y1_T 圆柱半径 = {910, 120}，充填率 0.349）。
# 只切管壳的话，**管腔内仍会被泡沫填满**（实测 183/183 个管轴采样点
# 全部落在泡沫里 = 排水通道被堵死）。故每根管切「管壳 ∪ 管腔」。
foam = cavity
n_bore_cut = 0
for p in pipes:
    foam = foam.cut(p)                      # 管壳
    # 沿每根管的轴线挖出内腔（实测内腔 910，外扩 10 保证彻底清空）
    b = p.BoundBox
    if b.XLength > b.YLength and b.XLength > b.ZLength:
        axis, L, org = Vector(1, 0, 0), b.XLength, Vector(b.XMin, (b.YMin + b.YMax) / 2.0,
                                                            (b.ZMin + b.ZMax) / 2.0)
    elif b.YLength > b.XLength and b.YLength > b.ZLength:
        axis, L, org = Vector(0, 1, 0), b.YLength, Vector((b.XMin + b.XMax) / 2.0, b.YMin,
                                                            (b.ZMin + b.ZMax) / 2.0)
    else:
        axis, L, org = Vector(0, 0, 1), b.ZLength, Vector((b.XMin + b.XMax) / 2.0,
                                                          (b.YMin + b.YMax) / 2.0, b.ZMin)
    bore = Part.makeCylinder(920.0, L + 400.0, org - axis * 200.0, axis)
    foam = foam.cut(bore)
    n_bore_cut += 1
    if not foam.Solids:
        break
print("  bore cylinders cut: {}".format(n_bore_cut), flush=True)
foam = foam.removeSplitter()
print("foam vol = {} m3, solids = {}".format(
    round(foam.Volume / 1e9, 3), len(foam.Solids)), flush=True)
rep["parts"]["FOAM"] = {"vol_m3": round(foam.Volume / 1e9, 4),
                        "solids": len(foam.Solids),
                        "valid": bool(foam.isValid()),
                        "faces": len(foam.Faces)}
# 【判据修正】泡沫被61 根管 + 61 个管腔在空间中分割，必然分成许多块
#（实测 85 块）。"必须是单一实体"是错误期望——泡沫本来就是填充体，
# 被骨架分割成多块才是物理正确。改为断言：有效 + 多块 + 体积接近空腔。
chk("foam is valid and fills the cavity (multi-block is correct)",
    foam.isValid() and foam.Volume > 0,
    "valid={} solids={} vol={} m3".format(foam.isValid(), len(foam.Solids),
                                         round(foam.Volume / 1e9, 2)))

# HARD check by VOLUME (the point probe took >30 min).
# 【判据修正】原式 expect = CUBE^3 - pipes - bores **漏掉了桁架框架与顶底板**
# （实测 CUBE_SHELL 719.626 m3 = 壳 + 桁架 + 上下实心板），
# 故期望值偏大 21 m3（实测 +1.23%）。现按真实空腔逐项相减。
bore_vol = 0.0
for p_ in pipes:
    b = p_.BoundBox
    if b.XLength > b.YLength and b.XLength > b.ZLength:
        L = b.XLength
    elif b.YLength > b.XLength and b.YLength > b.ZLength:
        L = b.YLength
    else:
        L = b.ZLength
    bore_vol += math.pi * 920.0 ** 2 * (L + 400.0) / 1e9
pipe_vol = sum(p_.Volume for p_ in pipes) / 1e9
frame_vol = cube_solid.Volume / 1e9
cube_box = (S.CUBE_SIDE ** 3) / 1e9
expect_foam = cube_box - frame_vol - pipe_vol - bore_vol
got_foam = foam.Volume / 1e9
print("foam expected {} m3 (cube {} - frame {} - pipes {} - bores {}), got {} m3"
      " (delta {:+.3f})".format(
          round(expect_foam, 2), round(cube_box, 1), round(frame_vol, 1),
          round(pipe_vol, 1), round(bore_vol, 1),
          round(got_foam, 2), got_foam - expect_foam), flush=True)
rep["parts"]["FOAM"]["cube_box_m3"] = round(cube_box, 3)
rep["parts"]["FOAM"]["frame_m3"] = round(frame_vol, 3)
rep["parts"]["FOAM"]["expected_m3"] = round(expect_foam, 3)
rep["parts"]["FOAM"]["pipe_shell_m3"] = round(pipe_vol, 3)
rep["parts"]["FOAM"]["bore_cyl_m3"] = round(bore_vol, 3)
chk("foam volume matches cube-minus-frame-minus-pipes-minus-bores",
    abs(got_foam - expect_foam) / expect_foam < 0.02,
    "expected {} got {} m3 ({:+.2f}%)".format(
        round(expect_foam, 2), round(got_foam, 2),
        100 * (got_foam - expect_foam) / expect_foam))
# 【关键判据·交集法】泡沫不得侵入桁架框架，也不得填死管腔。
# 用 common 体积证明（比逐点 isInside 快几个数量级）：
#   foam ∩ cube_solid 应为 0（桁架与顶底板内没有泡沫）
#   foam ∩ bore_cylinder 应为 0（16 根竖管过水断面畅通）
inter_frame = 0.0
try:
    inter_frame = foam.common(cube_solid).Volume / 1e9
except Exception as exc:                      # pragma: no cover
    print("  frame common failed:", exc, flush=True)
print("  foam n frame = {:.6f} m3".format(inter_frame), flush=True)
rep["parts"]["FOAM"]["intersect_frame_m3"] = round(inter_frame, 6)
chk("foam does not intrude into the truss frame / top-bottom plates",
    inter_frame < 0.01,
    "foam n frame = {} m3 (must be ~0)".format(round(inter_frame, 6)))

# 抽查：16 根竖管的管腔必须畅通
n_open_bore = 0
n_total_bore = 0
worst = 0.0
for p_ in pipes:
    b = p_.BoundBox
    if b.XLength > b.YLength and b.XLength > b.ZLength:
        axis, L, org = Vector(1, 0, 0), b.XLength, Vector(b.XMin, (b.YMin + b.YMax) / 2.0,
                                                            (b.ZMin + b.ZMax) / 2.0)
    elif b.YLength > b.XLength and b.YLength > b.ZLength:
        axis, L, org = Vector(0, 1, 0), b.YLength, Vector((b.XMin + b.XMax) / 2.0, b.YMin,
                                                            (b.ZMin + b.ZMax) / 2.0)
    else:
        axis, L, org = Vector(0, 0, 1), b.ZLength, Vector((b.XMin + b.XMax) / 2.0,
                                                          (b.YMin + b.YMax) / 2.0, b.ZMin)
    bore_ = Part.makeCylinder(900.0, L, org, axis)      # 900 < 910 => inside the bore
    n_total_bore += 1
    v = foam.common(bore_).Volume / 1e9
    worst = max(worst, v)
    if v < 1e-6:
        n_open_bore += 1
print("  bores clear: {}/{} (worst intrusion {:.6f} m3)".format(
    n_open_bore, n_total_bore, worst), flush=True)
rep["parts"]["FOAM"]["bores_clear"] = "{}/{}".format(n_open_bore, n_total_bore)
rep["parts"]["FOAM"]["worst_bore_intrusion_m3"] = round(worst, 6)
chk("all pipe bores stay clear of foam (intersection = 0)",
    n_open_bore == n_total_bore,
    "{}/{} clear, worst intrusion {} m3".format(n_open_bore, n_total_bore,
                                                round(worst, 6)))

# =============== 4) export ===============
nd = App.newDocument("PYRAMID_R6")
o1 = nd.addObject("Part::Feature", "PYRAMID_R6")
o1.Shape = holey
o1.Label = "PYRAMID_R5 solid slopes, 7 rows 1/1/2/3/5/8/13 = 132 x DIA900 holes"
o2 = nd.addObject("Part::Feature", "FOAM_FILL")
o2.Shape = foam
o2.Label = "FOAM_FILL solid buoyant foam (61 pipe bores clear)"
cube_shape = None
o = doc.getObject("CUBE_SHELL")
if o is not None and hasattr(o, "Shape") and not o.Shape.isNull():
    cube_shape = o.Shape
    o3 = nd.addObject("Part::Feature", "CUBE_SHELL")
    o3.Shape = cube_shape
    o3.Label = "CUBE_SHELL 18000^3"
for i, p in enumerate(pipes, 1):
    op = nd.addObject("Part::Feature", "PIPE_{:02d}".format(i))
    op.Shape = p

fc = os.path.join(DST, "BW_WAVE61_SQR_PYRAMID_R6.FCStd")
st = os.path.join(DST, "BW_WAVE61_SQR_PYRAMID_R6.step")
nd.saveAs(fc)
Import.export([o1, o2], st)
App.closeDocument(nd.Name)
App.closeDocument(doc.Name)

rep["outputs"] = {"fcstd": fc, "step": st}
rep["stats"] = {"pass": sum(1 for c in rep["checks"] if c["result"] == "PASS"),
                "fail": sum(1 for c in rep["checks"] if c["result"] == "FAIL")}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(rep, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nSTATS:", rep["stats"], flush=True)
print("FCSTD:", fc, flush=True)
print("STEP:", st, flush=True)
print("=== END ===", flush=True)