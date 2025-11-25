# 测试性能优化指南

## 🔍 问题分析

测试运行缓慢的主要原因：

### 1. **重试机制导致延迟** ⚠️ (主要原因)

**问题**: `creative_service`中的`_call_gemini_api_internal`函数使用了`tenacity`重试装饰器：
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),  # 每次重试等待2-30秒
    retry=retry_if_exception_type((Exception,)),
)
```

**影响**: 
- 即使mock了`call_gemini_text`，如果mock没有完全绕过重试逻辑，仍会触发2-30秒的延迟
- 每个creative_service测试耗时16-42秒

### 2. **测试串行执行** ⚠️

**问题**: 202个测试串行执行，无法利用多核CPU

**影响**: 总耗时 = 所有测试耗时之和

### 3. **Fixture重复创建** ⚠️

**问题**: 每个测试都创建新的TestClient

**影响**: 增加启动开销

---

## ✅ 已实施的优化

### 1. 优化Mock，绕过重试逻辑 ✅

**修改**: `tests/conftest.py`中的mock fixtures现在同时mock内部函数：

```python
@pytest.fixture
def mock_gemini_text():
    # Mock内部函数，完全绕过重试逻辑
    with patch('app.services.creative_service.creative_utils._call_gemini_api_internal') as mock_internal, \
         patch('app.services.creative_service.creative_utils.call_gemini_text') as mock:
        mock_internal.return_value = '{"headline": "...", "primary_text": "..."}'
        mock.return_value = '{"headline": "...", "primary_text": "..."}'
        yield mock
```

**预期效果**: creative_service测试从16-42秒减少到1-3秒

### 2. 优化Fixture作用域 ✅

**修改**: TestClient fixtures改为`scope="session"`：

```python
@pytest.fixture(scope="session")
def creative_client():
    """TestClient for creative_service (session scope for performance)."""
    from app.services.creative_service.main import app
    return TestClient(app)
```

**预期效果**: 减少TestClient创建开销，节省10-15%时间

### 3. 添加并行测试支持 ✅

**新增**: Makefile中添加`test-parallel`目标

**使用方法**:
```bash
# 安装pytest-xdist
pip install pytest-xdist

# 运行并行测试
make test-parallel
# 或
pytest tests/ -n auto
```

**预期效果**: 测试时间减少60-70%

---

## 🚀 立即优化步骤

### 步骤1: 安装pytest-xdist

```bash
cd /Users/xingbo.huang/code/ad-campaign/ad-campaign-agent
./venv/bin/pip install pytest-xdist
```

### 步骤2: 运行优化后的测试

```bash
# 方式1: 使用脚本（自动检测并行支持）
./run_tests_with_progress.sh

# 方式2: 使用Makefile并行测试
make test-parallel

# 方式3: 直接运行
./venv/bin/pytest tests/ -n auto -v --tb=short --durations=10
```

---

## 📊 预期性能提升

| 优化措施 | 当前耗时 | 优化后耗时 | 提升 |
|---------|---------|-----------|------|
| **优化Mock绕过重试** | 287s | ~180s | 37% |
| **+ 并行执行** | 180s | ~60s | 67% |
| **+ 优化Fixture** | 60s | ~50s | 17% |
| **总计** | **287s** | **~50s** | **83%** |

---

## 🎯 进一步优化建议

### 1. 标记慢测试

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    # 慢测试
    pass

# 只运行快速测试
pytest tests/ -m "not slow"
```

### 2. 减少测试数据量

对于`test_generate_creatives_max_limit`，减少产品数量：
- 当前: 9个产品
- 优化: 3-5个产品（足够测试逻辑）

### 3. 优化E2E测试

- 使用更轻量的mock
- 减少实际服务调用
- 只测试关键路径

---

## 📝 总结

**主要问题**: 
1. ✅ **已修复**: Mock没有完全绕过重试逻辑
2. ✅ **已优化**: Fixture作用域
3. ⚡ **建议**: 使用pytest-xdist并行执行

**预期效果**: 
- 从287秒减少到50-60秒
- **性能提升: 80%+**

