#!/usr/bin/env python3
"""批量迁移指定第三方插件到本地 `src/plugins`。

默认迁移（你给的清单）：
- nonebot_plugin_pokemonle
- nonebot_plugin_mhguesser
- nonebot_plugin_epicfree
- nonebot_plugin_jrrp3
- nonebot_plugin_anans_sketchbook
- nonebot_plugin_manosaba_memes
- nonebot_plugin_memes_api
- nonebot_plugin_whateat_pic
- nonebot_plugin_who_is_spy
- nonebot_plugin_WWwiki

设计目标：
- 可重复执行：目标目录存在会自动备份到 `*.bak.<timestamp>`。
- 尽量少改第三方源码：迁移时只做必要的导入/require 替换（迁移工具内部控制）。
- 配置自动更新：把 `configs/config.yaml` 的 `plugins.enabled` 改成 `src.plugins.xxx`。
- 可自测：可选执行 `python -m compileall src/plugins`。

推荐使用虚拟环境运行：
  ./venv/bin/python scripts/migrate_all_third_party.py
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DEFAULT_MODULES: List[str] = [
    "nonebot_plugin_pokemonle",
    "nonebot_plugin_mhguesser",
    "nonebot_plugin_epicfree",
    "nonebot_plugin_jrrp3",
    "nonebot_plugin_anans_sketchbook",
    "nonebot_plugin_manosaba_memes",
    "nonebot_plugin_memes_api",
    "nonebot_plugin_whateat_pic",
    "nonebot_plugin_who_is_spy",
    "nonebot_plugin_WWwiki",
]

# 特殊包名大小写（PyPI 通常不敏感，但这里用于生成本地目录名，需保持一致）
SPECIAL_PACKAGE_NAME: Dict[str, str] = {
    "nonebot_plugin_WWwiki": "nonebot-plugin-WWwiki",
}


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def module_to_package_candidates(module_name: str) -> List[str]:
    """给定模块名，返回可能的 pip 包名候选。"""
    if module_name in SPECIAL_PACKAGE_NAME:
        pkg = SPECIAL_PACKAGE_NAME[module_name]
        return [pkg, pkg.lower(), module_name.replace("_", "-"), module_name]

    # 常见：nonebot_plugin_xxx -> nonebot-plugin-xxx
    base = module_name
    if base.startswith("nonebot_plugin_"):
        base = base.replace("nonebot_plugin_", "nonebot-plugin-")
    base = base.replace("_", "-")

    candidates = [
        base,
        base.lower(),
        module_name.replace("_", "-"),
        module_name,
    ]

    # 去重保持顺序
    seen = set()
    uniq: List[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def canonical_package_name(module_name: str) -> str:
    """用于迁移目录命名的 canonical 包名（尽量保持 nonebot-plugin- 前缀）。"""
    if module_name in SPECIAL_PACKAGE_NAME:
        return SPECIAL_PACKAGE_NAME[module_name]

    if module_name.startswith("nonebot_plugin_"):
        # nonebot_plugin_xxx -> nonebot-plugin-xxx
        return "nonebot-plugin-" + module_name.replace("nonebot_plugin_", "").replace("_", "-")

    # fallback
    name = module_name.replace("_", "-")
    return name if name.startswith("nonebot-plugin-") else f"nonebot-plugin-{name}"


def local_plugin_path_from_package(package_name: str) -> str:
    base = package_name
    if base.startswith("nonebot-plugin-"):
        base = base.replace("nonebot-plugin-", "")
    return f"src.plugins.{base.replace('-', '_')}"


def update_enabled_list_in_yaml(
    config_path: Path,
    module_name: str,
    package_name: str,
    local_plugin_path: str,
) -> bool:
    """把 config.yaml 的 plugins.enabled 更新为本地路径，移除外部写法。"""
    import yaml

    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        return False

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    plugins = config.setdefault("plugins", {})
    enabled = plugins.get("enabled") or []
    if not isinstance(enabled, list):
        enabled = []

    remove_set = {
        module_name,
        module_name.lower(),
        package_name,
        package_name.lower(),
        module_name.replace("_", "-"),
        module_name.replace("_", "-").lower(),
    }

    enabled = [p for p in enabled if str(p) not in remove_set]
    if local_plugin_path not in enabled:
        enabled.append(local_plugin_path)

    plugins["enabled"] = enabled

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="批量迁移指定第三方插件到 src/plugins")
    parser.add_argument(
        "--plugins",
        nargs="*",
        default=None,
        help="要迁移的插件模块名列表（默认使用内置清单）",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="不自动 pip install（模块缺失则直接失败）",
    )
    parser.add_argument(
        "--no-add-config",
        action="store_true",
        help="不自动向 config.yaml 追加插件配置模板",
    )
    parser.add_argument(
        "--self-check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="迁移完成后执行 compileall 自检（默认开启）",
    )

    args = parser.parse_args()

    # 使用脚本模式，避免 NoneBot 未初始化报错
    os.environ["MIGRATE_SCRIPT_MODE"] = "1"

    project_root = get_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 导入迁移函数
    from src.plugins.migrate_plugin import (
        install_plugin,
        copy_plugin_to_local,
        detect_plugin_config,
        add_plugin_config_to_yaml,
        get_plugin_config_template,
    )

    modules = args.plugins if args.plugins else DEFAULT_MODULES

    config_path = project_root / "configs" / "config.yaml"

    print("=" * 70)
    print("开始迁移第三方插件 -> src/plugins")
    print("项目根目录:", project_root)
    print("目标插件数量:", len(modules))
    print("=" * 70)

    ok_count = 0
    fail_count = 0

    for module_name in modules:
        print("\n" + "-" * 70)
        print(f"🔄 迁移: {module_name}")

        package_name = canonical_package_name(module_name)

        # 1) 确保模块存在（必要时安装）
        if not importlib.util.find_spec(module_name):
            if args.skip_install:
                print(f"❌ 模块未安装且 --skip-install: {module_name}")
                fail_count += 1
                continue

            candidates = module_to_package_candidates(module_name)
            installed = False
            last_err: Optional[str] = None

            for cand in candidates:
                print(f"📦 尝试安装: {cand}")
                success, err = install_plugin(cand)
                if success and importlib.util.find_spec(module_name):
                    installed = True
                    # 用成功安装的候选做为 package_name（影响本地目录名）
                    package_name = cand if cand.startswith("nonebot-plugin-") else package_name
                    break
                last_err = err

            if not installed:
                print(f"❌ 安装失败: {module_name}")
                if last_err:
                    print(last_err[:800])
                fail_count += 1
                continue

        # 2) 可选：追加配置模板
        if not args.no_add_config:
            try:
                plugin_config = detect_plugin_config(module_name)
                if plugin_config:
                    plugin_key = module_name.replace("nonebot_plugin_", "").replace("_", "-")
                    add_plugin_config_to_yaml(package_name, {plugin_key: plugin_config})
                else:
                    tmpl = get_plugin_config_template(package_name)
                    if tmpl:
                        add_plugin_config_to_yaml(package_name, tmpl)
            except Exception as e:
                print(f"⚠️ 配置检测/追加失败（可忽略，后续可手动补配置）: {e}")

        # 3) 复制到本地
        try:
            copy_success, local_path, copy_error = copy_plugin_to_local(module_name, package_name)
        except Exception as e:
            copy_success, local_path, copy_error = False, None, str(e)

        if not copy_success or not local_path:
            print(f"❌ 复制失败: {copy_error}")
            fail_count += 1
            continue

        # 4) 更新 config.yaml enabled
        if update_enabled_list_in_yaml(config_path, module_name, package_name, local_path):
            print(f"✅ 配置已更新: {module_name} / {package_name} -> {local_path}")
        else:
            print("⚠️ 配置更新失败，请手动把插件加入 plugins.enabled")

        print(f"✅ 迁移完成: {module_name} -> {local_path}")
        ok_count += 1

    print("\n" + "=" * 70)
    print("迁移结束")
    print(f"✅ 成功: {ok_count}")
    print(f"❌ 失败: {fail_count}")
    print("=" * 70)

    # 自检：只做语法级 compile 检查（不执行插件逻辑）
    if args.self_check:
        import subprocess

        print("\n🧪 自检: python -m compileall src/plugins")
        r = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", str(project_root / "src" / "plugins")],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            print("❌ compileall 失败")
            if r.stdout:
                print(r.stdout)
            if r.stderr:
                print(r.stderr)
            return 2
        print("✅ compileall 通过")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
