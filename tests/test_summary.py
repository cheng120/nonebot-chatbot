#!/usr/bin/env python3
"""
测试执行和结果汇总
直接运行测试并生成报告
"""
import sys
import os
import subprocess
from pathlib import Path

# 添加项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))
os.chdir(project_dir)

def run_tests():
	"""运行测试并生成报告"""
	print("=" * 70)
	print("NoneBot通用聊天机器人 - 测试执行报告")
	print("=" * 70)
	print()
	
	# 检查依赖
	print("检查测试依赖...")
	dependencies = {
		"pytest": "pytest",
		"pytest_asyncio": "pytest-asyncio",
		"pytest_cov": "pytest-cov"
	}
	
	missing = []
	for module, package in dependencies.items():
		try:
			__import__(module)
			print(f"  ✅ {package}")
		except ImportError:
			print(f"  ❌ {package} 未安装")
			missing.append(package)
	
	if missing:
		print(f"\n正在安装缺失的依赖: {', '.join(missing)}")
		subprocess.check_call([
			sys.executable, "-m", "pip", "install", "-q"
		] + missing)
		print("✅ 依赖安装完成\n")
	
	# 运行测试
	print("开始执行测试...")
	print("-" * 70)
	
	test_cmd = [
		sys.executable, "-m", "pytest",
		"tests/",
		"-v",
		"--tb=short",
		"--color=yes",
		"-q"
	]
	
	try:
		result = subprocess.run(test_cmd, capture_output=True, text=True)
		
		# 输出测试结果
		if result.stdout:
			print(result.stdout)
		if result.stderr:
			print(result.stderr, file=sys.stderr)
		
		print("-" * 70)
		
		if result.returncode == 0:
			print("\n✅ 所有测试通过！")
		else:
			print(f"\n⚠️  测试完成，退出码: {result.returncode}")
		
		# 尝试生成覆盖率报告
		print("\n生成覆盖率报告...")
		coverage_cmd = [
			sys.executable, "-m", "pytest",
			"tests/",
			"--cov=src",
			"--cov=config",
			"--cov-report=term",
			"--cov-report=html:htmlcov",
			"-q"
		]
		
		try:
			subprocess.run(coverage_cmd, check=False)
			print("\n✅ 覆盖率报告已生成: htmlcov/index.html")
		except Exception as e:
			print(f"\n⚠️  覆盖率报告生成失败: {e}")
		
		return result.returncode
		
	except Exception as e:
		print(f"\n❌ 测试执行失败: {e}")
		import traceback
		traceback.print_exc()
		return 1

if __name__ == "__main__":
	sys.exit(run_tests())

