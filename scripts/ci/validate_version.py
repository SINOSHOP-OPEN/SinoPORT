#!/usr/bin/env python3
"""SINOSHOP R16 版本合规校验脚本"""

import json
import os
import sys

def load_versions(versions_path='governance/VERSIONS.json'):
    try:
        with open(versions_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 致命错误：找不到版本配置文件 {versions_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ 致命错误：{versions_path} 不是有效的 JSON")
        sys.exit(1)

def main():
    # 从 GitHub Actions 环境变量获取 PR 目标分支
    target_branch = os.environ.get('GITHUB_BASE_REF', 'main')
    print(f"🔍 检查目标分支：{target_branch}")

    versions_data = load_versions()
    maintenance_versions = [v['version'] for v in versions_data['sinoshop_versions']['maintenance']]
    eol_versions = [v['version'] for v in versions_data['sinoshop_versions']['eol']]

    target_version = target_branch

    if target_version in eol_versions:
        print(f"❌ 错误：分支 {target_branch} 对应版本 {target_version} 已终止生命周期 (EOL)。")
        print("   除非是紧急安全补丁，否则禁止合并。")
        sys.exit(1)
    elif target_version in maintenance_versions:
        print(f"⚠️ 警告：分支 {target_branch} 处于维护模式 (Maintenance)。")
        print("   该分支仅接受安全修复。请确保 PR 未包含新功能或 API 变更。")
        # 维护模式仅警告，不阻断
    else:
        print(f"✅ 分支 {target_branch} (版本 {target_version}) 处于活跃状态 (Active)，检查通过。")

    sys.exit(0)

if __name__ == '__main__':
    main()
