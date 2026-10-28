#!/usr/bin/env python3
"""
SINOSHOP R16 编码校验器 V4.0.1 (公开版)

功能：校验 R16 编码字符串是否符合格式规范。
- 长度校验（32 位）
- 前缀校验（SINOR）
- 各字段字符集校验
- CHK 校验位验证

本脚本仅做格式校验，不验证构件的真实性。
真实性核验由虎符令牌在服务器侧完成。
"""

import re
import hashlib
import sys


def compute_chk(prefix_30: str) -> str:
    """计算 30 位前缀的 CHK 校验位（2 位十六进制）。"""
    sha256_hash = hashlib.sha256(prefix_30.encode('utf-8')).hexdigest()
    # 取哈希值的前 4 个十六进制字符中的前 2 个
    return sha256_hash[:2].upper()


def validate_encoding(encoding: str) -> tuple[bool, str]:
    """
    校验 R16 编码字符串。
    返回 (是否有效, 错误信息)。
    """
    # 1. 长度校验
    if len(encoding) != 32:
        return False, f"编码长度错误：期望 32 位，实际 {len(encoding)} 位"

    # 2. 前缀校验
    if not encoding.startswith("SINOR-"):
        return False, "编码必须以 'SINOR-' 开头"

    # 3. 字段分割
    parts = encoding.split("-")
    if len(parts) != 7:
        return False, f"编码应包含 7 个字段（以 '-' 分隔），实际 {len(parts)} 个"

    sinor, org, seg, zon, com, att, chk = parts

    # 4. ORG 字段校验
    if not re.match(r'^[A-Z0-9]{3,8}$', org):
        return False, f"ORG 字段无效：'{org}' 应为 3-8 位大写字母或数字"

    # 5. SEG 字段校验
    if not re.match(r'^SFT-\d{2,4}$', seg):
        return False, f"SEG 字段无效：'{seg}' 应为 'SFT-' 后跟 2-4 位数字"

    # 6. ZON 字段校验
    valid_zon = {"AFMB", "FLEX", "THRS", "SENS", "BDMP", "ENER", "ECOL"}
    if zon not in valid_zon:
        return False, f"ZON 字段无效：'{zon}' 不在 {valid_zon} 中"

    # 7. COM 字段校验
    if not re.match(r'^[A-Z0-9]{4}$', com):
        return False, f"COM 字段无效：'{com}' 应为 4 位大写字母或数字"

    # 8. ATT 字段校验
    if not re.match(r'^[A-Z0-9]{4}$', att):
        return False, f"ATT 字段无效：'{att}' 应为 4 位大写字母或数字"

    # 9. CHK 校验位验证
    prefix_30 = "-".join([sinor, org, seg, zon, com, att])
    expected_chk = compute_chk(prefix_30)
    if chk.upper() != expected_chk:
        return False, f"CHK 校验失败：期望 {expected_chk}，实际 {chk.upper()}"

    return True, "校验通过"


def main():
    if len(sys.argv) > 1:
        # 从命令行参数读取
        encoding = sys.argv[1]
        valid, message = validate_encoding(encoding)
        if valid:
            print(f"✅ {encoding}：{message}")
        else:
            print(f"❌ {encoding}：{message}")
            sys.exit(1)
    else:
        # 交互模式
        print("SINOSHOP R16 编码校验器 V4.0.1")
        print("输入 R16 编码进行校验（输入 'exit' 退出）：\n")
        while True:
            encoding = input("编码 > ").strip()
            if encoding.lower() == "exit":
                break
            if not encoding:
                continue
            valid, message = validate_encoding(encoding)
            if valid:
                print(f"  ✅ {message}")
            else:
                print(f"  ❌ {message}")
            print()


if __name__ == "__main__":
    main()
