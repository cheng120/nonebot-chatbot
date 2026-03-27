#!/usr/bin/env python3
"""
测试 CLI 工具
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.add_plugin import create_plugin_file, get_plugin_template

def test_template_generation():
	"""测试模板生成"""
	print("测试模板生成...")
	template = get_plugin_template("test_plugin", "测试插件")
	assert "test_plugin" in template
	assert "测试插件" in template
	assert "PluginMetadata" in template
	print("✅ 模板生成测试通过")

def test_plugin_creation():
	"""测试插件创建"""
	print("\n测试插件创建...")
	test_dir = Path(__file__).parent / "test_plugins"
	test_dir.mkdir(exist_ok=True)
	
	# 创建测试插件
	success = create_plugin_file(
		plugin_name="test_cli_plugin",
		plugin_dir=test_dir,
		description="CLI工具测试插件",
		force=True
	)
	
	if success:
		plugin_file = test_dir / "test_cli_plugin.py"
		if plugin_file.exists():
			print(f"✅ 插件文件创建成功: {plugin_file}")
			# 清理测试文件
			plugin_file.unlink()
			test_dir.rmdir()
			print("✅ 测试文件已清理")
		else:
			print("❌ 插件文件未创建")
			return False
	else:
		print("❌ 插件创建失败")
		return False
	
	return True

if __name__ == "__main__":
	print("=" * 50)
	print("CLI 工具测试")
	print("=" * 50)
	
	try:
		test_template_generation()
		test_plugin_creation()
		print("\n" + "=" * 50)
		print("✅ 所有测试通过")
		print("=" * 50)
	except Exception as e:
		print(f"\n❌ 测试失败: {e}")
		import traceback
		traceback.print_exc()
		sys.exit(1)

