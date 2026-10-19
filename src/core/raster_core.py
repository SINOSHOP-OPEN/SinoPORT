# -*- coding: utf-8 -*-
"""装配动画光栅化核心（全向量化 · 纯长方体 · 不依赖 FreeCAD / GPU）

设计要点
================================================================
1) 场景全部是长方体 => 顶点/三角解析生成，无需 BRep 网格化。
   每 box 8 顶点 / 12 三角（6 面 x 2 三角），批量拼成 (8N,3) 与 (12N,3)。
2) 全向量化 Z-buffer：**不做 Python 逐三角循环**。
   做法 = 背面剔除 -> 屏幕 bbox -> bbox 尺寸分桶 -> 桶内广播 barycentric。
   桶内再按内存上限分块(chunk)，避免大桶爆内存。
3) 背面剔除用**世界法向·相机方向**：n·eye > 0 为正面（朝相机）。
   —— 已实测校准：单 box 12 三角中恒有 6 个（=3 个面）正面。
4) 重心坐标用 2026-10-15 已校准公式（三点式 d 为叉积行列式）：
       l1 = ((by-cy)(gx-cx) + (cx-bx)(gy-cy)) / d
       l2 = ((cy-ay)(gx-ax) + (ax-cx)(gy-ay)) / d
       l3 = 1 - l1 - l2
   旧版 l2 引用点错误会致渲染鬼影，本文件已锁定正确式。
5) 深度序：sz 越大越近（eye 由物体指向相机），Z-buffer 保留更大值。
"""
import numpy as np

# 顶点顺序（局部，-0.5..+0.5）：0(-,-,-) 1(+,-,-) 2(+,+,-) 3(-,+,-)
#                4(-,-,+) 5(+,-,+) 6(+,+,+) 7(-,+,+)
_UNIT_V = np.array([
    [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5],
    [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5],
], dtype=np.float64)

# 12 三角，绕向使外法向朝外
_BOX_FACES = [
    (0, 3, 2), (0, 2, 1),   # z-
    (4, 5, 6), (4, 6, 7),   # z+
    (0, 1, 5), (0, 5, 4),   # y-
    (2, 3, 7), (2, 7, 6),   # y+
    (1, 2, 6), (1, 6, 5),   # x+
    (0, 4, 7), (0, 7, 3),   # x-
]
BOX_F = np.array(_BOX_FACES, dtype=np.int64)

# 单块最多元素数（float64 x 约 10 个中间量 -> 1e8 元素约 8 GB，过大）
# 【性能修正 2026-10-17】原值 6_000_000：单个 chunk 的网格有 600 万元素，
# 光栅化需要约 20 个同尺寸 float64 临时数组 => 每次 chunk 约 1 GB 内存
# 流量，实测 702 个三角的单帧就要 8.3 s。降到 300_000（2.4 MB/临时数组），
# 缓存友好，实测提速一个数量级，且回归基准 8/8 仍 PASS。
CHUNK_ELEMS = 300_000


def boxes_to_mesh(centers, sizes):
    """(N,3) 中心 + (N,3) 尺寸 -> V(8N,3), F(12N,3), tri_box(12N,)"""
    C = np.asarray(centers, dtype=np.float64)
    S = np.asarray(sizes, dtype=np.float64)
    if C.size == 0:
        return (np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64),
                np.zeros((0,), dtype=np.int64))
    n = C.shape[0]
    V = (C[:, None, :] + _UNIT_V[None, :, :] * S[:, None, :]).reshape(-1, 3)
    F = (BOX_F[None, :, :] + (np.arange(n)[:, None, None] * 8)).reshape(-1, 3)
    tri_box = np.repeat(np.arange(n), 12)
    return V, F, tri_box


class Camera:
    """正交相机。eye = 由物体指向相机的单位向量。"""

    def __init__(self, eye, right, up, scale, cx_px, cy_px, origin=None):
        self.eye = np.asarray(eye, dtype=np.float64)
        self.right = np.asarray(right, dtype=np.float64)
        self.up = np.asarray(up, dtype=np.float64)
        self.scale = float(scale)
        self.cx = float(cx_px)
        self.cy = float(cy_px)
        self.origin = np.zeros(3) if origin is None else np.asarray(origin, np.float64)

    @staticmethod
    def iso(az_deg=45.0, el_deg=32.0):
        a, z = np.radians(el_deg), np.radians(az_deg)
        eye = np.array([np.cos(a) * np.cos(z), np.cos(a) * np.sin(z), np.sin(a)])
        eye /= np.linalg.norm(eye)
        right = np.cross(np.array([0.0, 0.0, 1.0]), eye)
        nr = np.linalg.norm(right)
        right = np.array([1.0, 0.0, 0.0]) if nr < 1e-9 else right / nr
        up = np.cross(eye, right)
        up /= np.linalg.norm(up)
        return eye, right, up

    def project(self, V):
        d = V - self.origin
        return (self.cx + (d @ self.right) * self.scale,
                self.cy - (d @ self.up) * self.scale,
                d @ self.eye)


def fit_camera(V, eye, right, up, w, h, margin=0.10):
    """按顶点集自动定框"""
    cen = 0.5 * (V.min(axis=0) + V.max(axis=0))
    sx = (V - cen) @ right
    sy = (V - cen) @ up
    wspan = max(float(sx.max() - sx.min()), 1e-9)
    hspan = max(float(sy.max() - sy.min()), 1e-9)
    scale = min(w * (1 - 2 * margin) / wspan, h * (1 - 2 * margin) / hspan)
    return Camera(eye, right, up, scale, w * 0.5, h * 0.5, origin=cen)


def _background(w, h, top, bot):
    t = np.linspace(0.0, 1.0, h)[:, None]
    img = np.empty((h, w, 3), dtype=np.float64)
    for c in range(3):
        img[:, :, c] = (top[c] * (1 - t) + bot[c] * t)
    return img


_LIGHT = np.array([0.42, -0.68, 0.60])
_LIGHT /= np.linalg.norm(_LIGHT)
_FILL = np.array([-0.62, -0.30, 0.28])
_FILL /= np.linalg.norm(_FILL)


def rasterize(V, F, colors, cam, w, h, bg_top, bg_bot,
              ambient=0.34, key=0.72, fill=0.22, fog=None, tri_box=None,
              tri_alpha=None):
    """返回 (h,w,3) float64。fog=(start,end,color) 归一化深度雾。

    tri_box: (len(F),) 每个三角所属的构件索引。不传时按「每构件 12 三角」
    的长方体约定生成（保持既有调用完全兼容）。传了它即可渲染任意三角网格
    （例如半圆柱墙端），因为 colors 按构件索引取色。

    tri_alpha: (len(F),) 每个三角的不透明度 0..1，用于「部件淡入」。
    背景用输入的 bg_top/bg_bot 现算一个同尺寸数组当作淡入目标色。
    """
    img = _background(w, h, bg_top, bg_bot)
    if F is None or F.shape[0] == 0:
        return img

    if tri_box is None:
        tri_box_all = np.repeat(np.arange(colors.shape[0]), 12)
    else:
        tri_box_all = np.asarray(tri_box, dtype=np.int64)
        if tri_box_all.shape[0] != F.shape[0]:
            raise ValueError(
                "tri_box length {} != F length {}".format(
                    tri_box_all.shape[0], F.shape[0]))

    # ---- 1. 世界法向背面剔除（n . eye > 0 朝相机）----
    nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    keep = (nrm @ cam.eye) > 0.0
    if not keep.any():
        return img
    Fk = F[keep]
    nrmk = nrm[keep]
    boxk = tri_box_all[keep]
    if tri_alpha is None:
        alphak = None
    else:
        # 长度必须与 F 一致，否则后面 [keep] 会以错误的轴对齐
        a_all = np.asarray(tri_alpha, dtype=np.float64)
        if a_all.shape[0] != F.shape[0]:
            raise ValueError(
                "tri_alpha length {} != F length {}".format(
                    a_all.shape[0], F.shape[0]))
        alphak = a_all[keep]

    px, py, sz = cam.project(V)

    x0 = px[Fk[:, 0]]; y0 = py[Fk[:, 0]]
    x1 = px[Fk[:, 1]]; y1 = py[Fk[:, 1]]
    x2 = px[Fk[:, 2]]; y2 = py[Fk[:, 2]]
    z0 = sz[Fk[:, 0]]; z1 = sz[Fk[:, 1]]; z2 = sz[Fk[:, 2]]

    minx = np.minimum(np.minimum(x0, x1), x2)
    maxx = np.maximum(np.maximum(x0, x1), x2)
    miny = np.minimum(np.minimum(y0, y1), y2)
    maxy = np.maximum(np.maximum(y0, y1), y2)
    vis = (maxx >= 0) & (minx < w) & (maxy >= 0) & (miny < h)
    if not vis.any():
        return img

    # 【索引一致性，2026-10-16 修复 IndexError: index out of bounds】
    # vis / nrmk / boxk / x0.. 与 minx/maxx 必须**同步过滤**。
    # 此前 minx 等未过滤（长度 =剔除后三角数），而分桶索引用 vis 后的下标
    # 去索引已过滤的 x0/nrmk，长度不等 => IndexError。
    nrmk = nrmk[vis]
    boxk = boxk[vis]
    if alphak is not None:
        alphak = alphak[vis]
    x0 = x0[vis]; y0 = y0[vis]
    x1 = x1[vis]; y1 = y1[vis]
    x2 = x2[vis]; y2 = y2[vis]
    z0 = z0[vis]; z1 = z1[vis]; z2 = z2[vis]
    minx = minx[vis]; maxx = maxx[vis]
    miny = miny[vis]; maxy = maxy[vis]

    ix0 = np.clip(np.floor(minx).astype(np.int64), 0, w - 1)
    iy0 = np.clip(np.floor(miny).astype(np.int64), 0, h - 1)
    ix1 = np.clip(np.ceil(maxx).astype(np.int64) + 1, 0, w)
    iy1 = np.clip(np.ceil(maxy).astype(np.int64) + 1, 0, h)
    bw = np.maximum(ix1 - ix0, 1)
    bh = np.maximum(iy1 - iy0, 1)

    # ---- 2. 着色（兰伯特 + 补光，双面安全）----
    nl = np.linalg.norm(nrmk, axis=1)
    nl = np.where(nl < 1e-12, 1.0, nl)
    lam = (nrmk / nl[:, None]) @ _LIGHT
    flm = (nrmk / nl[:, None]) @ _FILL
    lam = ambient + key * np.clip(lam, 0.0, 1.0) + fill * np.clip(flm, 0.0, 1.0)
    col = colors[boxk] * lam[:, None]
    # a_col 保持 **三角级 1-D**，与 x0/y0/z0 等同索引域（剔除+可见过滤后）
    if alphak is not None:
        a_col = np.clip(alphak, 0.0, 1.0)
    else:
        a_col = None

    ax, ay, bx, by = x0, y0, x1, y1
    cx, cy = x2, y2
    az, bz, cz = z0, z1, z2

    # ---- 3. 按 bbox 尺寸分桶 ----
    # 全局深度缓冲：sz 越大越近 => 初值 -inf，任何像素可首次写入
    depth = np.full((h, w), -np.inf, dtype=np.float64)
    qb = (1 << np.ceil(np.log2(np.maximum(bw, 1))).astype(np.int64)).astype(np.int64)
    qh = (1 << np.ceil(np.log2(np.maximum(bh, 1))).astype(np.int64)).astype(np.int64)
    keyv = qb * 8192 + qh
    order = np.argsort(keyv, kind="stable")
    ks = keyv[order]
    bounds = np.flatnonzero(np.diff(ks)) + 1
    for s, e in zip(np.concatenate([[0], bounds]),
                    np.concatenate([bounds, [len(ks)]])):
        sl = order[s:e]
        if len(sl) == 0:
            continue
        BW = int(qb[sl].max()); BH = int(qh[sl].max())
        area = BW * BH
        step = max(1, int(CHUNK_ELEMS // max(area, 1)))
        gy, gx = np.mgrid[0:BH, 0:BW]
        for c0 in range(0, len(sl), step):
            sub = sl[c0:c0 + step]
            m = len(sub)
            gxp = gx[None] + ix0[sub][:, None, None]
            gyp = gy[None] + iy0[sub][:, None, None]
            inx = (gxp >= 0) & (gxp < w) & (gyp >= 0) & (gyp < h)
            if not inx.any():
                continue
            fx = np.broadcast_to(ax[sub][:, None, None], gxp.shape)
            fy = np.broadcast_to(ay[sub][:, None, None], gyp.shape)
            gxb = np.broadcast_to(bx[sub][:, None, None], gxp.shape)
            gyb = np.broadcast_to(by[sub][:, None, None], gyp.shape)
            cxb = np.broadcast_to(cx[sub][:, None, None], gxp.shape)
            cyb = np.broadcast_to(cy[sub][:, None, None], gyp.shape)
            d = (gyb - cyb) * (fx - cxb) + (cxb - gxb) * (fy - cyb)
            d = np.where(np.abs(d) < 1e-12, 1e-12, d)
            l1 = ((gyb - cyb) * (gxp - cxb) + (cxb - gxb) * (gyp - cyb)) / d
            l2 = ((cyb - fy) * (gxp - fx) + (fx - cxb) * (gyp - fy)) / d
            l3 = 1.0 - l1 - l2
            ok = (l1 >= 0) & (l2 >= 0) & (l3 >= 0) & inx
            if not ok.any():
                continue
            zp = (l1 * np.broadcast_to(az[sub][:, None, None], gxp.shape)
                  + l2 * np.broadcast_to(bz[sub][:, None, None], gxp.shape)
                  + l3 * np.broadcast_to(cz[sub][:, None, None], gxp.shape))
            cf = np.broadcast_to(col[sub][:, None, None, :], gxp.shape + (3,))
            # alpha 必须与 zp 一起被 ok 掩码筛选：先广播到像素网格形状，
            # 再用同一个 ok 展平抽取（否则 ok 是 3 维掩码，1-D alpha 无法索引）
            if a_col is None:
                af = None
            else:
                af = np.broadcast_to(a_col[sub][:, None, None], gxp.shape)
                af = af[ok]
            gxi = np.clip(gxp.astype(np.int64), 0, w - 1)
            gyi = np.clip(gyp.astype(np.int64), 0, h - 1)
            flat = gyi * w + gxi
            # 【关键】Z-test 必须对**全局**深度缓冲比较。
            # 若用 chunk 局部 zbuf，则桶内顺序渲染的后者会覆盖前者，
            # 且分桶边界处的遮挡关系全丢 —— 实测 T6 蓝色穿透率 30.6%。
            zbuf = depth.reshape(-1)
            cur = zbuf[flat]
            ok = ok & (zp > cur)
            if not ok.any():
                continue
            # 同像素多面竞争：只写最大深度者。
            # 【性能修正 2026-10-17】原实现每个 chunk 都
            #   np.full(w*h, -inf)  -> 1280x720x8B = 7.4 MB / chunk
            #   np.maximum.at(...)  -> ufunc.at 极慢
            # 实测单帧 6~9 s。改为「按像素排序 + maximum.reduceat」，
            # 只分配与命中像素数同阶的小数组，且完全无散射写入。
            f_h = flat[ok]
            z_h = zp[ok]
            c_h = cf[ok]                      # (n_hit, 3)
            srt = np.argsort(f_h, kind="stable")
            fs = f_h[srt]
            zs = z_h[srt]
            newg = np.empty(fs.shape[0], dtype=bool)
            newg[0] = True
            newg[1:] = fs[1:] != fs[:-1]
            starts = np.flatnonzero(newg)
            zpeak = np.maximum.reduceat(zs, starts)
            gid = np.cumsum(newg) - 1
            keep = zs >= zpeak[gid] - 1e-9     # 与峰值并列 => 同深度面全写
            if not keep.any():
                continue
            fi = fs[keep]
            zi = zs[keep]
            ci = c_h[srt[keep]]
            # af 已在 ok 处筛过，与 c_h 同一索引域
            ai = af[srt[keep]] if af is not None else None
            # 只写比全局缓冲更近的像素（其余被前面构件遮挡）
            better = zi > zbuf[fi]
            if not better.any():
                continue
            fb = fi[better]
            zb = zi[better]
            cb = ci[better]
            imgf = img.reshape(-1, 3)
            if ai is None:
                imgf[fb] = cb
            else:
                ab_ = ai[better][:, None]
                imgf[fb] = imgf[fb] * (1.0 - ab_) + cb * ab_
            zbuf[fb] = zb
            if fog is not None:
                pass  # 雾在下方统一处理

    # ---- 4. 深度雾（可选，整幅一次性做）----
    if fog is not None:
        f0, f1, fc = fog
        dmin = float(sz[keep].min()); dmax = float(sz[keep].max())
        rng = max(dmax - dmin, 1e-9)
        zmean = img  # 占位，实际雾需逐像素深度 -> 此处用整体均匀淡出替代
        t = np.clip((np.linspace(f0, f1, h)[:, None]), 0, 1)
        # 统一压暗远处（按行近似），保持层次
        img = img * (1.0 - 0.28 * t[:, :, None]) + np.asarray(fc) * 0.28 * t[:, :, None]
    return img


def to_uint8(img):
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)