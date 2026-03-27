#!/usr/bin/env python3
"""插件命令冒烟测试（无需真实 QQ 连接）。

目标：测试每个插件的“命令是否能触发并产生响应（至少一次 send_*）”。

说明：
- 这是“冒烟测试”，不是完整 E2E。它用一个假的 OneBot v11 Bot 和 Event 走 NoneBot 的事件处理流程。
- 部分插件依赖外部资源（网络/文件/数据库/Playwright）时，可能仍会报错或无响应；脚本会记录失败原因。

用法：
  ./venv/bin/python scripts/test_plugin_commands.py

可选参数：
  --limit N   最多测试 N 条命令（排查用）
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import importlib
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 确保脚本能导入项目模块（config/src 等）
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import nonebot


@dataclass
class CmdCase:
    plugin: str
    kind: str  # on_command / on_alconna
    name: str
    aliases: List[str]

    def candidates(self) -> List[str]:
        # 优先测试“无前缀”和“/前缀”两种
        base = [self.name, f"/{self.name}"]
        for a in self.aliases:
            base.append(a)
            base.append(f"/{a}")
        # 去重保持顺序
        seen = set()
        out: List[str] = []
        for s in base:
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        return out


def _parse_on_command(file_path: Path, plugin_name: str) -> List[CmdCase]:
    cases: List[CmdCase] = []
    try:
        code = file_path.read_text(encoding="utf-8")
        tree = ast.parse(code)
    except Exception:
        return cases

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue

        func = node.value.func
        func_name = None
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr

        if func_name != "on_command":
            continue

        # cmd name
        cmd_name: Optional[str] = None
        if node.value.args:
            arg0 = node.value.args[0]
            if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                cmd_name = arg0.value
            elif isinstance(arg0, ast.Str):
                cmd_name = arg0.s

        aliases: List[str] = []
        for kw in node.value.keywords:
            if kw.arg == "aliases":
                v = kw.value
                if isinstance(v, (ast.List, ast.Tuple, ast.Set)):
                    for elt in v.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            aliases.append(elt.value)
                        elif isinstance(elt, ast.Str):
                            aliases.append(elt.s)
                # dict/set 复杂情况略过

        if not cmd_name:
            # fallback: 使用变量名
            for t in node.targets:
                if isinstance(t, ast.Name):
                    cmd_name = t.id
                    if cmd_name.endswith("_cmd"):
                        cmd_name = cmd_name[:-4]
                    break

        if cmd_name:
            cases.append(CmdCase(plugin=plugin_name, kind="on_command", name=cmd_name, aliases=aliases))

    return cases


def _parse_on_alconna(file_path: Path, plugin_name: str) -> List[CmdCase]:
    """解析 on_alconna(Alconna("xxx"), aliases={...}) 形式的命令。"""
    cases: List[CmdCase] = []
    try:
        code = file_path.read_text(encoding="utf-8")
        tree = ast.parse(code)
    except Exception:
        return cases

    def _get_str(node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Str):
            return node.s
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        func_name = None
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr

        if func_name != "on_alconna":
            continue

        # 取第一个参数：通常是 Alconna("命令")
        cmd: Optional[str] = None
        if node.args:
            first = node.args[0]
            if isinstance(first, ast.Call):
                inner_func = first.func
                inner_name = inner_func.id if isinstance(inner_func, ast.Name) else (inner_func.attr if isinstance(inner_func, ast.Attribute) else None)
                if inner_name == "Alconna" and first.args:
                    cmd = _get_str(first.args[0])

        aliases: List[str] = []
        for kw in node.keywords:
            if kw.arg == "aliases":
                v = kw.value
                if isinstance(v, (ast.Set, ast.List, ast.Tuple)):
                    for elt in v.elts:
                        s = _get_str(elt)
                        if s:
                            aliases.append(s)

        if cmd:
            cases.append(CmdCase(plugin=plugin_name, kind="on_alconna", name=cmd, aliases=aliases))

    return cases


async def main() -> int:
    parser = argparse.ArgumentParser(description="测试每个插件命令是否能触发并响应")
    parser.add_argument("--limit", type=int, default=0, help="最多测试 N 条命令（0=不限制）")
    parser.add_argument(
        "--plugins",
        nargs="*",
        default=None,
        help="只测试指定插件（使用 src/plugins 下的目录/文件名，如 memes_api whateat_pic）",
    )
    args = parser.parse_args()

    # 初始化 nonebot
    from config import load_config
    cfg = load_config()

    # 确保 SUPERUSER 测试能通过
    # 这里设置一个默认 superuser=10001（不会写配置，只影响本次进程）
    nonebot.init(
        driver=cfg.driver,
        # 冒烟测试降低噪声，避免大量日志拖慢执行
        log_level="WARNING",
        command_start=["", "/"],
        command_sep=[" ", "."],
        superusers={"10001"},
    )

    driver = nonebot.get_driver()

    # 注册适配器（项目已有封装）
    from src.adapters.onebot_v11 import setup_onebot_adapter
    setup_onebot_adapter(cfg)

    # 加载插件（不依赖数据库写入）
    from src.services.plugin_manager import PluginManager
    pm = PluginManager(cfg.plugins.dir, None, cfg.plugins)
    await pm.load_all_plugins()

    enabled_plugins = list(cfg.plugins.enabled or [])

    # 收集命令：递归扫描每个启用插件对应目录/文件的所有 .py
    project_root = Path(__file__).parent.parent
    plugins_root = project_root / "src" / "plugins"

    wanted = set(args.plugins or [])

    cases: List[CmdCase] = []
    for plugin in enabled_plugins:
        if not plugin.startswith("src.plugins."):
            continue

        rel = plugin.replace("src.plugins.", "")
        if wanted and rel not in wanted:
            continue

        file_py = plugins_root / f"{rel}.py"
        dir_pkg = plugins_root / rel

        scan_files: List[Path] = []
        if file_py.exists():
            scan_files = [file_py]
        elif dir_pkg.exists() and dir_pkg.is_dir():
            # 扫描包内所有 .py（跳过备份目录、migrations 等对命令无关的内容）
            for f in dir_pkg.rglob("*.py"):
                p = str(f)
                if ".bak." in p:
                    continue
                if "/migrations/" in p or p.endswith("/migrations/__init__.py"):
                    continue
                scan_files.append(f)

        for f in scan_files:
            cases.extend(_parse_on_command(f, rel))
            cases.extend(_parse_on_alconna(f, rel))

    # 去重（按 kind+name+plugin）
    uniq: Dict[Tuple[str, str, str], CmdCase] = {}
    for c in cases:
        key = (c.plugin, c.kind, c.name)
        if key not in uniq:
            uniq[key] = c

    all_cases = list(uniq.values())

    # 限制测试数量（排查用）
    if args.limit and args.limit > 0:
        all_cases = all_cases[: args.limit]

    print(f"Collected command cases: {len(all_cases)}")

    # 创建一个假的 Bot，并拦截 call_api 作为“有响应”的判定
    from nonebot.adapters.onebot.v11 import Adapter, Bot, PrivateMessageEvent, Message

    adapter = Adapter(driver)
    bot = Bot(adapter=adapter, self_id="12345")

    sent_calls: List[Tuple[str, Dict[str, Any]]] = []

    async def _fake_call_api(api: str, **data: Any) -> Any:
        sent_calls.append((api, dict(data)))
        return {"ok": True}

    # monkeypatch
    bot.call_api = _fake_call_api  # type: ignore

    # 注册到 driver，便于 get_bots 等使用
    try:
        driver.bots[bot.self_id] = bot  # type: ignore
    except Exception:
        pass

    def make_event(text: str) -> PrivateMessageEvent:
        data = {
            "time": int(time.time()),
            "self_id": bot.self_id,
            "post_type": "message",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": int(time.time() * 1000) % 1000000000,
            "user_id": 10001,  # superuser
            "message": Message(text),
            "raw_message": text,
            "font": 0,
            "sender": {"user_id": 10001, "nickname": "tester", "sex": "unknown", "age": 0},
        }
        return PrivateMessageEvent(**data)

    results: List[Tuple[CmdCase, bool, str]] = []

    for case in all_cases:
        ok = False
        err = ""
        # 对每个 case，尝试多种候选输入，任意一次有 send_* 即算通过
        for text in case.candidates():
            sent_calls.clear()
            try:
                await bot.handle_event(make_event(text))
                # 给异步发送一点时间
                await asyncio.sleep(0.02)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
                continue

            if any(api.startswith("send_") for api, _ in sent_calls):
                ok = True
                err = ""
                break

        results.append((case, ok, err))

    # 输出汇总
    by_plugin: Dict[str, List[Tuple[CmdCase, bool, str]]] = {}
    for case, ok, err in results:
        by_plugin.setdefault(case.plugin, []).append((case, ok, err))

    failed_total = 0
    for plugin, items in sorted(by_plugin.items()):
        passed = sum(1 for _, ok, _ in items if ok)
        failed = len(items) - passed
        failed_total += failed
        print(f"\n[{plugin}] passed={passed} failed={failed}")
        for c, ok, err in items:
            if ok:
                continue
            print(f"  - FAIL {c.kind}:{c.name} {('aliases='+str(c.aliases)) if c.aliases else ''} -> {err or 'no send_*'}")

    print(f"\nDONE total_cases={len(results)} failed={failed_total}")
    return 0 if failed_total == 0 else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
