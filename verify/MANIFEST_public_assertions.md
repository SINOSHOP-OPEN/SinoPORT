# 公开断言层 · 发布清单

本清单由脚本按**磁盘实际字节**重算生成，任何一份文件被改动后其指纹即与本清单不符。

## 指纹口径（两类，不可混用）

| 类型 | 适用对象 | 算法 |
|---|---|---|
| **字节指纹** | 脚本 / 运行器 / AI Agent 骨架 / 公开数据 CSV | 对文件原始字节取 SHA-256（前 16 位） |
| **语义指纹** | 核验结果 JSON | 解析 JSON → 键排序 → 规范化序列化 → 取 SHA-256（前 16 位） |

> 结果 JSON 是验证脚本**运行时写出的产物**，每次运行都会重排浮点与缩进，
> 字节指纹天然不稳定；**语义指纹**才对应「结论逐次一致」这一真正要存证的事实。
> 静态资产的字节指纹依赖换行符统一（仓库已用 `.gitattributes` 锁定 LF）。

## 物理断言脚本 · 15 条验证主线

| 文件 | 字节 | 字节指纹 SHA-256（前 16） |
|---|---:|---|
| `public_verify_01_wave_attenuation_381m.py` | 14564 | `d9a2e3d27337cd8b` |
| `public_verify_02_lcs_load_cancellation.py` | 19025 | `467dbc7d4308ac15` |
| `public_verify_03_tidal_height_constant.py` | 13919 | `9f035345ae60c907` |
| `public_verify_04_wave_multilevel.py` | 9414 | `104c16e1bf065b81` |
| `public_verify_05_lcs_tonnage.py` | 16668 | `d8b024009cea7510` |
| `public_verify_06_composite_material.py` | 22141 | `bcbf7cd6d6ce64a1` |
| `public_verify_07_cable_stress.py` | 14700 | `f76ea998ef232c66` |
| `public_verify_08_tidal48.py` | 14048 | `0ae006cdd6656693` |
| `public_verify_09_bidirectional_berth_flow.py` | 18659 | `b863b1653bdf1cfb` |
| `public_verify_10_load_transfer.py` | 11964 | `dd36c9d03dce91db` |
| `public_verify_11_economics_lcc.py` | 24045 | `1dea4fad842d4489` |
| `public_verify_12_pressure_unload.py` | 30708 | `e8a65a913ac30a82` |
| `public_verify_13_band_allocation.py` | 11847 | `5dd03f1a4af1f36b` |
| `public_verify_14_load_allocation.py` | 10014 | `f912e60c6a32a46b` |
| `public_verify_15_ab_coupling.py` | 10099 | `5a2931d6cdac77f3` |

## 聚合运行器

| 文件 | 字节 | 字节指纹 SHA-256（前 16） |
|---|---:|---|
| `run_all_public_verifications.py` | 3615 | `e7f25f236c569b02` |

## AI Agent 最小骨架

| 文件 | 字节 | 字节指纹 SHA-256（前 16） |
|---|---:|---|
| `agent_min_skeleton.py` | 11299 | `c342e456a4deffff` |

## 核验结果 JSON（语义指纹）

| 文件 | 字节 | 语义指纹 SHA-256（前 16） |
|---|---:|---|
| `verify_01_summary.json` | 8833 | `e6f859f46d54907b` |
| `verify_01_wave_attenuation_381m_results.json` | 8833 | `e6f859f46d54907b` |
| `verify_02_lcs_load_cancellation_results.json` | 7052 | `461afffbca0da478` |
| `verify_02_summary.json` | 7504 | `54346d3e95b5c413` |
| `verify_03_summary.json` | 5331 | `e6e91acf83ae22d2` |
| `verify_03_tidal_height_constant_results.json` | 1082845 | `aaa8865eacef6af0` |
| `verify_04_summary.json` | 9458 | `1d7d9c18f6f39dba` |
| `verify_04_wave_multilevel_summary.json` | 9458 | `1d7d9c18f6f39dba` |
| `verify_05_lcs_tonnage_summary.json` | 120744 | `1d361c844415ef81` |
| `verify_06_composite_material_summary.json` | 122732 | `617252248605064a` |
| `verify_07_cable_stress_summary.json` | 44043 | `5af2024b70236dbd` |
| `verify_08_tidal48_summary.json` | 1623794 | `9bf8cf10df9b78de` |
| `verify_09_bidirectional_berth_summary.json` | 17426 | `220d9aa9fcf81716` |
| `verify_10_load_transfer_summary.json` | 3878 | `07324f59dd66f551` |
| `verify_11_economics_lcc_summary.json` | 1702 | `d3bdb9a1c5b8efb0` |
| `verify_12_pressure_unload_summary.json` | 1131 | `e261adb7d6ca90c4` |
| `verify_13_band_allocation_summary.json` | 2795 | `1c2e264dcfd3d713` |
| `verify_14_load_allocation_summary.json` | 2667 | `1bbf29f7030f4fb7` |
| `verify_15_ab_coupling_summary.json` | 2567 | `171b800cd4779543` |

## 公开数据 CSV

| 文件 | 字节 | 字节指纹 SHA-256（前 16） |
|---|---:|---|
| `data/payload_response.csv` | 213 | `e75cdd53fcae3d23` |
| `data/tonnage_sweep.csv` | 244 | `8072604807fdeab3` |
| `data_cable_stress.csv` | 6736 | `37032ba54284df4e` |
| `data_lcs_tonnage.csv` | 556 | `9555178d09644586` |
| `data_lcs_tonnage_drive.csv` | 40091 | `176ee745a3cbed0c` |
| `data_tidal48_turbine.csv` | 157419 | `a0776068f74c095d` |

## 数据自洽性脚本

| 文件 | 字节 | 字节指纹 SHA-256（前 16） |
|---|---:|---|
| `verify_public_dataset.py` | 7197 | `e2503a534d7f06a5` |

---

共 %d 份文件。对外统一口径：**361 项物理断言**，全部通过，退出码 0。

一键运行（须先安装 `numpy`，仅此一项依赖）：

```bash
git clone https://gitee.com/sinoshop/sinoport-public.git
# 或：git clone https://github.com/SINOSHOP-OPEN/SinoPORT.git
cd sinoport-public/verify
python run_all_public_verifications.py
```

AI Agent 最小骨架（编排器 + 断言校验 + 设备抽象接口 + Mock 后端）：

```bash
python agent_min_skeleton.py
```
