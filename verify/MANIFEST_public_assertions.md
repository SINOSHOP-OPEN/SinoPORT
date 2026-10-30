# 公开断言层 · 发布清单

本清单由脚本按**磁盘实际字节**重算生成（SHA-256 前 16 位）。
任何一份文件被改动后，其指纹即与本清单不符 —— 这正是数字存证的意义。

## 物理断言脚本 · 15 条验证主线

| 文件 | 字节 | SHA-256（前 16） |
|---|---:|---|
| `public_verify_01_wave_attenuation_381m.py` | 14564 | `d9a2e3d27337cd8b` |
| `public_verify_02_lcs_load_cancellation.py` | 19025 | `467dbc7d4308ac15` |
| `public_verify_03_tidal_height_constant.py` | 13919 | `9f035345ae60c907` |
| `public_verify_04_wave_multilevel.py` | 9654 | `26342de0ce3cb05b` |
| `public_verify_05_lcs_tonnage.py` | 16668 | `d8b024009cea7510` |
| `public_verify_06_composite_material.py` | 22141 | `bcbf7cd6d6ce64a1` |
| `public_verify_07_cable_stress.py` | 14700 | `f76ea998ef232c66` |
| `public_verify_08_tidal48.py` | 14048 | `0ae006cdd6656693` |
| `public_verify_09_bidirectional_berth_flow.py` | 19108 | `b5e5bc364cf6a4df` |
| `public_verify_10_load_transfer.py` | 11964 | `dd36c9d03dce91db` |
| `public_verify_11_economics_lcc.py` | 24556 | `9ef0893315933976` |
| `public_verify_12_pressure_unload.py` | 30708 | `e8a65a913ac30a82` |
| `public_verify_13_band_allocation.py` | 11847 | `5dd03f1a4af1f36b` |
| `public_verify_14_load_allocation.py` | 10014 | `f912e60c6a32a46b` |
| `public_verify_15_ab_coupling.py` | 10099 | `5a2931d6cdac77f3` |

## 聚合运行器

| 文件 | 字节 | SHA-256（前 16） |
|---|---:|---|
| `run_all_public_verifications.py` | 3615 | `e7f25f236c569b02` |

## AI Agent 最小骨架

| 文件 | 字节 | SHA-256（前 16） |
|---|---:|---|
| `agent_min_skeleton.py` | 11299 | `c342e456a4deffff` |

## 核验结果 JSON

| 文件 | 字节 | SHA-256（前 16） |
|---|---:|---|
| `verify_01_summary.json` | 9223 | `7721ddf3c3361b66` |
| `verify_01_wave_attenuation_381m_results.json` | 9223 | `7721ddf3c3361b66` |
| `verify_02_lcs_load_cancellation_results.json` | 7319 | `5758335e5a6668f5` |
| `verify_02_summary.json` | 7504 | `40faa161330b5ca6` |
| `verify_03_summary.json` | 5331 | `301a0ae505a7a8c7` |
| `verify_03_tidal_height_constant_results.json` | 1129112 | `6ddd588f490799f3` |
| `verify_04_summary.json` | 9810 | `2033e7cfac605dca` |
| `verify_04_wave_multilevel_summary.json` | 9810 | `2033e7cfac605dca` |
| `verify_05_lcs_tonnage_summary.json` | 127391 | `5c87dcf76d1ad659` |
| `verify_06_composite_material_summary.json` | 127944 | `8b937c5bfbdcfef5` |
| `verify_07_cable_stress_summary.json` | 45563 | `578ffe12ff4a5c3d` |
| `verify_08_tidal48_summary.json` | 1693092 | `c704f2cff261f579` |
| `verify_09_bidirectional_berth_summary.json` | 18099 | `bb88aac9eee7432f` |
| `verify_10_load_transfer_summary.json` | 3973 | `913ff31ea6f412e7` |
| `verify_11_economics_lcc_summary.json` | 1775 | `c9e08688d0e08967` |
| `verify_12_pressure_unload_summary.json` | 1171 | `11702498f9782de9` |
| `verify_13_band_allocation_summary.json` | 2854 | `a9d56bf68e9085ba` |
| `verify_14_load_allocation_summary.json` | 2721 | `b2a774d3eda141cb` |
| `verify_15_ab_coupling_summary.json` | 2619 | `2fedef8f20e07992` |

## 公开数据 CSV

| 文件 | 字节 | SHA-256（前 16） |
|---|---:|---|
| `data/payload_response.csv` | 222 | `47591c5a4c3889c8` |
| `data/tonnage_sweep.csv` | 253 | `3b1d7e018c17273e` |
| `data_cable_stress.csv` | 6833 | `dace39587a779837` |
| `data_lcs_tonnage.csv` | 561 | `e788725ff0d7dcd0` |
| `data_lcs_tonnage_drive.csv` | 41692 | `49aa6cd6270a1e8f` |
| `data_tidal48_turbine.csv` | 160300 | `f3c232ac193d021d` |

## 数据自洽性脚本

| 文件 | 字节 | SHA-256（前 16） |
|---|---:|---|
| `verify_public_dataset.py` | 7394 | `793541539d72b799` |

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
