#!/bin/sh
# =============================================================================
# 一键启用本地脱敏钩子
#
# 用法（在仓库根执行）：
#       sh scripts/enable_hooks.sh
#       或 Windows Git Bash：  bash scripts/enable_hooks.sh
#
# 作用：把本地 Git 钩子目录指向仓库内随代码分发的 .githooks/，
#       之后每次提交与推送都会自动跑公开层尺寸/密度扫描。
#
# 说明：Git 不会自动分发钩子配置（core.hooksPath 是本地设置），
#       因此首次克隆后需执行一次本脚本。
# =============================================================================

set -e

ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "❌ 请在 Git 仓库内执行本脚本。" >&2
    exit 1
}

cd "$ROOT"

if [ ! -d "$ROOT/.githooks" ]; then
    echo "❌ 未找到 .githooks/ 目录，仓库可能不完整。" >&2
    exit 1
fi

git config core.hooksPath .githooks
echo "✅ 已启用本地脱敏钩子（core.hooksPath = .githooks）"
echo ""
echo "此后："
echo "  · git commit   时自动检查提交信息"
echo "  · git push     时自动扫描整个工作树"
echo ""
echo "解除：git config --unset core.hooksPath"
