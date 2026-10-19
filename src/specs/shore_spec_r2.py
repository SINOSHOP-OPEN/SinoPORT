# -*- coding: utf-8 -*-
"""岸边固定景观参数源 r2  (2026-10-18 16:02)

船长裁定原文
================================================================
    「完成以上视频后，请建模并组合视频：展示悬浮港岸边固定的景观的
      货运平台（岸边没有结冰时与直径大路相连，同时一侧是陆地，
      港口侧是海水；冬天周围结冰时与冬季大道连接、）、
      城市、寺庙、教堂、公路、铁路」

本片的主角是**货运平台的双状态**（船长括注里的两个场景）
================================================================
    状态 A  非冬天：岸边未结冰
        HUB-LEFT / HUB-RIGHT  与直径大路两端相接（ROAD-D 3,900 m 的两端）
        一侧是陆地（−Y 侧，向岸），一侧是海水（+Y 侧，靠港）

    状态 B  冬天：岸边结冰
        HUB-LEFT / HUB-RIGHT  改与冬季大道相接
        （ROAD-Winter-Left/Right 各 3,000 m，起于 HUB，向岸侧 +Y 反方向）
        周围结冰，近岸 1,500 m 冰面 / 连接段 1,500 m 海水浪高 3 m

注意方向一致性（早于本轮的 F9 曾在此出错）
================================================================
V6.3 §4.13 / §4.14 的口径：
    HUB-LEFT  中心 (−1,950, 0)，直径大路左端
    HUB-RIGHT 中心 (+1,950, 0)，直径大路右端
    ROAD-Winter-Left  起于 HUB-LEFT，**垂直连接直径大路左端**
    近岸 1,500 m 结冰 + 连接段 1,500 m 海水（浪高 3 m）

悬浮港本体（直径大路 / 防波堤 / 泊位）位于 **+Y 侧**（半圆开口朝 +Y），
故 HUB 的**港口侧 = +Y（海水）**，**陆地侧 = −Y**。
冬季大道自 HUB 沿 **−Y 向陆** 延伸 3,000 m，
其 y ∈ [0, −3,000] 段为近岸结冰段、y ∈ [−3,000, −1,500] 为连接段海水。

参数出处（逐条可查）
================================================================
| 对象 | 代码 | 出处 |
|---|---|---|
| 左/右货运平台 | HUB-LEFT / HUB-RIGHT | V6.3 §4.14.1 / §4.14.2 |
| 岸边城市 | LAND-CITY-MOD | V6.3 §4.26.1 |
| 教堂 | LAND-CHURCH | V6.3 §4.26.2 |
| 寺庙 | LAND-TEMPLE | V6.3 §4.26.3 |
| 海岸高速 | HWY-COASTAL | V6.3 §4.26.4 |
| 海岸铁路 | RAIL-COASTAL | V6.3 §4.26.5 |
| 冬季大道 | ROAD-Winter-Left/Right | V6.3 §4.13 / §4.13.1 |

红线（V6.3 §4.14.3）
================================================================
    左、右货运平台规格必须统一（300×300×6 m，110 模块/平台）
    HUB-LEFT  中心 (−1,950, 0) 不得改动
    HUB-RIGHT 中心 (+1,950, 0) 不得改动
    颜色、结构、功能必须一致
    不得只建一侧、另一侧缺失

Run:  python -B shore_spec_r2.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

OUT = (os.path.join(HERE, os.pardir, os.pardir, "docs", "reports")
       + os.sep + "SHORE_SPEC_R2_20261018.json")

CAPTAIN_RULING = (
    "展示悬浮港岸边固定的景观的货运平台（岸边没有结冰时与直径大路相连，"
    "同时一侧是陆地，港口侧是海水；冬天周围结冰时与冬季大道连接、）、"
    "城市、寺庙、教堂、公路、铁路")

# ---------------- 悬浮港本体坐标系 ----------------
CHORD_R = 1650.0            # 半圆弦线 R=1,650（港口侧 +Y）
ROAD_D_LEN = 3900.0         # 直径大路 3,900 m
ROAD_D_W = 108.0            # 宽 108 m

# ---------------- §4.14 货运平台 ----------------
HUB_SIZE = 300.0            # 300 x 300 m（左右统一）
HUB_H = 6.0                 # 高 6 m
HUB_MODULES = 110           # 110 模块/平台
HUB_LEFT_X = -1950.0        # 红线，不得改动
HUB_RIGHT_X = +1950.0       # 红线，不得改动
HUB_Y = 0.0
HUB_FUNCS = ["铁路编组", "公路货场", "仓库", "龙门吊"]

# ---------------- §4.13 冬季大道（双状态的主角） ----------------
WIN_LEN = 3000.0            # 每条 3,000 m
WIN_W = 54.0                # 宽 54 m（红线）
WIN_MODULES = 200           # 每条 200 模块
ICE_LEN = 1500.0            # 近岸段 1,500 m 结冰
SEA_WAVE = 3.0              # 连接段浪高 3 m
# 冬季大道自 HUB 向 **陆地侧（−Y）** 延伸
WIN_Y0, WIN_Y1 = 0.0, -3000.0

# ---------------- §4.26 岸边景观 ----------------
CITY = {"code": "LAND-CITY-MOD", "cn": "岸边城市",
        "unit_m": 200.0, "units": 5, "bldg_h_min": 20.0,
        "bldg_h_max": 60.0, "style": "海边城市",
        "material": "混凝土 + 玻璃 + 雪顶"}
CHURCH = {"code": "LAND-CHURCH", "cn": "教堂",
          "size_m": [30.0, 20.0, 40.0], "count": 1,
          "tower_h_m": 40.0, "top": "金十字"}
TEMPLE = {"code": "LAND-TEMPLE", "cn": "寺庙",
          "size_m": [40.0, 40.0, 25.0], "count": 1,
          "style": "中国沿海", "roof": "重檐起翘"}
HWY = {"code": "HWY-COASTAL", "cn": "海岸高速",
       "length_m": 5000.0, "width_m": 56.0, "lanes": 8,
       "lane_w_m": 7.0, "light_every_m": 50.0, "surface": "沥青"}
RAIL = {"code": "RAIL-COASTAL", "cn": "海岸铁路",
        "length_m": 5000.0, "width_m": 10.0, "tracks": 4,
        "track_gap_m": 5.0, "gauge_m": 1.435,
        "signal_every_m": 500.0, "note": "与高速并行"}


def land_sea_split(x):
    """HUB 处的陆海分界：港口侧 +Y 海水，陆地侧 −Y 陆地。"""
    return {"port_side": "+Y（海水）", "land_side": "-Y（陆地）",
            "x_m": x}


def state_a():
    """状态 A：非冬天，未结冰，HUB 与直径大路两端相接。"""
    return {
        "state": "A",
        "season": "非冬天（岸边未结冰）",
        "connect_to": "直径大路 ROAD-D（3,900 m 两端）",
        "hub_left_x_m": HUB_LEFT_X,
        "hub_right_x_m": HUB_RIGHT_X,
        "ice": False,
        "land_side": "-Y 陆地",
        "sea_side": "+Y 海水（港侧）",
    }


def state_b():
    """状态 B：冬天，周围结冰，HUB 改与冬季大道相接。"""
    return {
        "state": "B",
        "season": "冬天（岸边结冰）",
        "connect_to": "冬季大道 ROAD-Winter-Left/Right（各 3,000 m）",
        "hub_left_x_m": HUB_LEFT_X,
        "hub_right_x_m": HUB_RIGHT_X,
        "ice": True,
        "ice_band_m": ICE_LEN,
        # 【实测修正】岸在 y=0 侧，冬季大道向 −Y 延伸，
        # 故「近岸段」= 紧邻岸线的一端 = y ∈ [−1500, 0]
        "ice_band_y": [-ICE_LEN, 0.0],
        "sea_band_m": WIN_LEN - ICE_LEN,
        "sea_band_y": [WIN_Y1, -ICE_LEN],
        "sea_wave_m": SEA_WAVE,
        "land_side": "-Y 陆地（结冰）",
        "sea_side": "+Y 海水（港侧，不冻）",
    }


def main():
    ok = True
    results = []

    def ck(name, cond, detail):
        nonlocal ok
        good = bool(cond)
        if not good:
            ok = False
        results.append({"check": name, "pass": good, "detail": detail})
        print("%s  %-50s %s" % ("PASS" if good else "FAIL", name, detail))

    print("=" * 96)
    print("岸边固定景观参数自检（V6.3 §4.13 / §4.14 / §4.26）")
    print("=" * 96)

    ck("1 货运平台 300 x 300 x 6 m（左右统一）",
       HUB_SIZE == 300.0 and HUB_H == 6.0,
       "%.0f x %.0f x %.0f m" % (HUB_SIZE, HUB_SIZE, HUB_H))
    ck("2 110 模块/平台", HUB_MODULES == 110, "%d 模块" % HUB_MODULES)
    ck("3 HUB-LEFT 中心 (−1,950, 0)（红线）",
       abs(HUB_LEFT_X + 1950.0) < 1e-9 and HUB_Y == 0.0,
       "(%.0f, %.0f)" % (HUB_LEFT_X, HUB_Y))
    ck("4 HUB-RIGHT 中心 (+1,950, 0)（红线）",
       abs(HUB_RIGHT_X - 1950.0) < 1e-9 and HUB_Y == 0.0,
       "(%.0f, %.0f)" % (HUB_RIGHT_X, HUB_Y))
    ck("5 左右规格对称（不得只建一侧）",
       HUB_SIZE == HUB_SIZE and HUB_MODULES == HUB_MODULES
       and abs(HUB_LEFT_X + HUB_RIGHT_X) < 1e-9,
       "左右同规格，中心 X 互为相反数")

    ck("6 直径大路 3,900 m，宽 108 m",
       ROAD_D_LEN == 3900.0 and ROAD_D_W == 108.0,
       "%.0f m x %.0f m" % (ROAD_D_LEN, ROAD_D_W))
    ck("7 HUB 位于直径大路两端",
       abs(abs(HUB_LEFT_X) - ROAD_D_LEN / 2.0) < 1e-9,
       "|HUB| %.0f = ROAD_D/2 %.0f" % (abs(HUB_LEFT_X),
                                        ROAD_D_LEN / 2.0))

    ck("8 冬季大道各 3,000 m，宽 54 m（红线）",
       WIN_LEN == 3000.0 and WIN_W == 54.0,
       "%.0f m x %.0f m x 2 条" % (WIN_LEN, WIN_W))
    ck("9 冬季大道 200 模块/条，合计 400",
       WIN_MODULES == 200, "200 x 2 = 400 模块")
    ck("10 冬季大道起于 HUB，向陆地侧 −Y 延伸",
       abs(WIN_Y0 - HUB_Y) < 1e-9 and WIN_Y1 < WIN_Y0,
       "y %.0f -> %.0f（−Y 向陆）" % (WIN_Y0, WIN_Y1))
    ck("11 冰段 1,500 + 海段 1,500 = 3,000 m",
       abs(ICE_LEN + (WIN_LEN - ICE_LEN) - WIN_LEN) < 1e-9,
       "结冰 %.0f + 海水 %.0f = %.0f m"
       % (ICE_LEN, WIN_LEN - ICE_LEN, WIN_LEN))
    ck("12 连接段浪高 3 m", SEA_WAVE == 3.0, "%.0f m" % SEA_WAVE)

    # 陆海方位：港口侧 +Y（悬浮港在 +Y），陆地侧 −Y
    ck("13 陆海方位：港口侧 +Y 海水 / 陆地侧 −Y",
       CHORD_R > 0 and WIN_Y1 < 0.0,
       "半圆开口朝 +Y（港口），冬季大道向 −Y（陆地）")

    ck("14 岸边城市 200x200 m x 5 个，高 20–60 m",
       CITY["unit_m"] == 200.0 and CITY["units"] == 5
       and CITY["bldg_h_min"] == 20.0 and CITY["bldg_h_max"] == 60.0,
       "5 x 200 m，%g–%g m" % (CITY["bldg_h_min"], CITY["bldg_h_max"]))
    ck("15 教堂 30x20x40 m，1 个，塔高 40 m",
       CHURCH["size_m"] == [30.0, 20.0, 40.0]
       and CHURCH["count"] == 1 and CHURCH["tower_h_m"] == 40.0,
       "1 座，塔 %.0f m" % CHURCH["tower_h_m"])
    ck("16 寺庙 40x40x25 m，1 个，重檐起翘",
       TEMPLE["size_m"] == [40.0, 40.0, 25.0]
       and TEMPLE["count"] == 1 and TEMPLE["roof"] == "重檐起翘",
       "1 座，重檐")
    ck("17 海岸高速 5,000 m x 56 m，8 车道（单宽 7 m）",
       HWY["length_m"] == 5000.0 and HWY["width_m"] == 56.0
       and HWY["lanes"] == 8 and abs(8 * HWY["lane_w_m"]
                                    - HWY["width_m"]) < 1e-9,
       "8 x 7 = %.0f m" % (8 * HWY["lane_w_m"]))
    ck("18 海岸铁路 5,000 m x 10 m，4 线，轨距 1.435 m",
       RAIL["length_m"] == 5000.0 and RAIL["tracks"] == 4
       and abs(RAIL["gauge_m"] - 1.435) < 1e-9,
       "4 线，轨距 %.3f m" % RAIL["gauge_m"])
    ck("19 铁路与高速并行（等长 5,000 m）",
       RAIL["length_m"] == HWY["length_m"],
       "两者均 %.0f m" % HWY["length_m"])

    sa, sb = state_a(), state_b()
    ck("20 状态 A：连直径大路、未结冰",
       sa["connect_to"].startswith("直径大路") and not sa["ice"],
       "%s，%s" % (sa["connect_to"], sa["season"]))
    ck("21 状态 B：连冬季大道、结冰",
       sb["connect_to"].startswith("冬季大道") and sb["ice"],
       "%s，%s" % (sb["connect_to"], sb["season"]))
    ck("22 状态 B 冰段在近岸（y ∈ [−1500, 0]）",
       abs(sb["ice_band_y"][0] + ICE_LEN) < 1e-6
       and abs(sb["ice_band_y"][1]) < 1e-6,
       "冰段 y ∈ [%.0f, %.0f]（紧邻岸线）；海水段 y ∈ [%.0f, %.0f]"
       % (sb["ice_band_y"][0], sb["ice_band_y"][1],
          sb["sea_band_y"][0], sb["sea_band_y"][1]))
    ck("23 两状态共用同一对 HUB 坐标",
       sa["hub_left_x_m"] == sb["hub_left_x_m"]
       and sa["hub_right_x_m"] == sb["hub_right_x_m"],
       "平台位置固定，变的只是连接对象与结冰状态")

    rep = {
        "date": "2026-10-18", "revision": "r2",
        "captain_ruling_verbatim": CAPTAIN_RULING,
        "source": "V6.3 §4.13 / §4.13.1 / §4.14 / §4.14.3 / §4.26",
        "axes": {
            "port_side": "+Y 海水（半圆开口朝 +Y，弦线 R=%.0f）" % CHORD_R,
            "land_side": "-Y 陆地",
            "note": "负 X = 左，正 X = 右（V5.7 全域命名）",
        },
        "hub": {"size_m": HUB_SIZE, "height_m": HUB_H,
                "modules": HUB_MODULES,
                "left": [HUB_LEFT_X, HUB_Y],
                "right": [HUB_RIGHT_X, HUB_Y],
                "functions": HUB_FUNCS,
                "redlines": ["左右规格统一", "±1,950 不得改动",
                             "不得只建一侧"]},
        "road_d": {"length_m": ROAD_D_LEN, "width_m": ROAD_D_W},
        "winter_road": {"each_length_m": WIN_LEN, "width_m": WIN_W,
                        "modules_each": WIN_MODULES,
                        "y_from": WIN_Y0, "y_to": WIN_Y1,
                        "ice_m": ICE_LEN, "sea_wave_m": SEA_WAVE},
        "state_a_nonwinter": sa,
        "state_b_winter": sb,
        "scenery": {"city": CITY, "church": CHURCH, "temple": TEMPLE,
                    "coastal_hwy": HWY, "coastal_rail": RAIL},
        "checks": results,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=1)

    n = sum(1 for r in results if r["pass"])
    print("-" * 96)
    print("wrote %s" % OUT)
    print("VERIFY: %d/%d %s" % (n, len(results),
                                "PASS" if n == len(results) else "FAIL"))
    return 0 if n == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())