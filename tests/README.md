# 测试文档

## 测试结构

```
tests/
├── __init__.py              # 测试模块初始化
├── conftest.py              # pytest配置和fixtures
├── test_config.py           # 配置管理模块测试
├── test_database.py         # 数据库模块测试
├── test_utils.py            # 工具模块测试
├── test_services.py         # 服务模块测试
├── test_integration.py      # 集成测试
├── run_tests.sh             # Linux/Mac测试脚本
└── run_tests.bat            # Windows测试脚本
```

## 测试类型

### 单元测试

- **test_config.py**: 配置管理模块测试
  - 配置加载器测试
  - 配置验证测试
  - 配置合并测试

- **test_database.py**: 数据库模块测试
  - 数据库连接测试
  - ORM模型测试
  - CRUD操作测试

- **test_utils.py**: 工具模块测试
  - 重试工具测试
  - 日志工具测试

- **test_services.py**: 服务模块测试
  - 插件管理器测试
  - 状态管理器测试

### 集成测试

- **test_integration.py**: 模块集成测试
  - 数据库和插件管理器集成
  - 配置和服务集成
  - 完整工作流程测试

## 运行测试

### 方式1: 使用pytest直接运行

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_config.py

# 运行特定测试类
pytest tests/test_config.py::TestConfigLoader

# 运行特定测试函数
pytest tests/test_config.py::TestConfigLoader::test_load_yaml_config

# 显示详细输出
pytest tests/ -v

# 显示覆盖率
pytest tests/ --cov=src --cov=config --cov-report=html
```

### 方式2: 使用测试脚本

**Linux/Mac:**
```bash
./tests/run_tests.sh
```

**Windows:**
```cmd
tests\run_tests.bat
```

### 方式3: 使用Python模块

```bash
python -m pytest tests/
```

## 测试覆盖率

生成覆盖率报告：

```bash
pytest tests/ --cov=src --cov=config --cov-report=html --cov-report=term
```

覆盖率报告会生成在 `htmlcov/index.html`，可以在浏览器中打开查看。

## 测试标记

使用pytest标记来分类测试：

```bash
# 只运行单元测试
pytest tests/ -m unit

# 只运行集成测试
pytest tests/ -m integration

# 跳过慢速测试
pytest tests/ -m "not slow"
```

## 测试Fixtures

测试中使用的fixtures（定义在 `conftest.py`）：

- `test_config`: 测试配置对象
- `db_manager`: 数据库管理器
- `db_session`: 数据库会话
- `temp_plugin_dir`: 临时插件目录

## 编写新测试

### 测试文件命名

- 测试文件以 `test_` 开头
- 测试类以 `Test` 开头
- 测试函数以 `test_` 开头

### 异步测试

使用 `@pytest.mark.asyncio` 装饰器：

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### 使用Fixtures

```python
def test_with_fixture(db_manager):
    assert db_manager is not None
```

## 测试最佳实践

1. **独立性**: 每个测试应该独立，不依赖其他测试的执行顺序
2. **可重复**: 测试应该可以重复运行，结果一致
3. **快速**: 单元测试应该快速执行
4. **清晰**: 测试名称应该清晰描述测试内容
5. **覆盖**: 尽量覆盖所有代码路径

## 持续集成

可以在CI/CD流程中运行测试：

```yaml
# GitHub Actions示例
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=src --cov-report=xml
```

## 故障排查

### 常见问题

1. **导入错误**: 确保 `PYTHONPATH` 包含项目根目录
2. **数据库错误**: 确保测试数据库路径可写
3. **异步测试失败**: 确保安装了 `pytest-asyncio`

### 调试测试

使用 `-s` 参数显示print输出：

```bash
pytest tests/ -s
```

使用 `--pdb` 在失败时进入调试器：

```bash
pytest tests/ --pdb
```

