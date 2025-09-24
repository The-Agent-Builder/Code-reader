# 文件过滤改进规则

## 概述
本规则记录了文件过滤功能的改进，解决了文件过多的问题，通过在前端进行预过滤来减少不必要的文件上传。

## 核心原则

### 1. 前端预过滤
- **在用户选择文件时就进行过滤**，而不是在后端处理时过滤
- 减少网络传输和后端处理负担
- 提升用户体验，避免上传大量无用文件

### 2. 统一过滤规则
- 创建统一的文件过滤配置 (`fileFilterConfig.ts`)
- 前端和后端使用相同的过滤逻辑
- 避免重复实现和不一致的规则

### 3. 支持.gitignore
- 自动读取和解析项目的.gitignore文件
- 支持常见的gitignore规则语法
- 与默认规则结合使用

## 实现组件

### 1. 文件过滤配置 (`frontend/src/utils/fileFilterConfig.ts`)
- `DEFAULT_IGNORE_DIRS`: 默认忽略的目录
- `DEFAULT_IGNORE_FILES`: 默认忽略的文件
- `DEFAULT_IGNORE_EXTENSIONS`: 默认忽略的文件扩展名
- `SUPPORTED_CODE_EXTENSIONS`: 支持的代码文件扩展名
- 包含uv.lock等新的锁文件类型

### 2. .gitignore解析器 (`frontend/src/utils/gitignoreParser.ts`)
- 支持标准gitignore语法
- 支持否定规则 (!)
- 支持目录规则 (/)
- 支持通配符 (* 和 ?)

### 3. 综合文件过滤器 (`frontend/src/utils/fileFilter.ts`)
- 结合默认规则和.gitignore规则
- 提供灵活的过滤选项
- 返回详细的过滤统计信息

## 默认排除列表

### 新增的重要文件类型
- `uv.lock` - Python uv包管理器的锁文件
- `pnpm-lock.yaml` - pnpm的锁文件
- `poetry.lock` - Poetry的锁文件
- `Cargo.lock` - Rust的锁文件
- `composer.lock` - PHP Composer的锁文件

### 扩展的目录类型
- `.pytest_cache`, `.mypy_cache` - Python测试和类型检查缓存
- `.parcel-cache`, `.rpt2_cache_*` - 前端构建缓存
- `.tox`, `.nox` - Python测试环境
- `.hypothesis` - Python属性测试缓存

## 使用方式

### 前端文件上传
```typescript
import { applyAllFilters } from "../utils/fileFilter";

const filteredFiles = await applyAllFilters(files);
```

### 自定义过滤选项
```typescript
import { FileFilter } from "../utils/fileFilter";

const filter = new FileFilter({
  useGitignore: true,
  useDefaultRules: true,
  onlyCodeFiles: false,
});

const result = await filter.filterFiles(files);
```

## 后续改进建议

### 1. 后端统一
- 将相同的过滤逻辑应用到后端
- 创建Python版本的文件过滤器
- 统一前后端的过滤规则

### 2. 用户配置
- 允许用户自定义过滤规则
- 提供过滤规则的可视化配置界面
- 支持项目级别的过滤配置

### 3. 性能优化
- 对大型项目的过滤性能优化
- 异步处理大量文件
- 提供过滤进度反馈

## 测试要点

### 1. 基本过滤功能
- 验证默认规则正确过滤常见无用文件
- 验证.gitignore规则正确解析和应用
- 验证文件扩展名过滤

### 2. 边界情况
- 空文件列表
- 没有.gitignore文件的项目
- 包含特殊字符的文件名
- 深层嵌套的目录结构

### 3. 性能测试
- 大量文件的过滤性能
- 复杂.gitignore规则的解析性能
- 内存使用情况

## 维护注意事项

### 1. 规则更新
- 定期更新默认排除列表
- 关注新的包管理器和构建工具
- 收集用户反馈，优化过滤规则

### 2. 兼容性
- 确保新规则不会误过滤重要文件
- 保持向后兼容性
- 提供规则迁移指南

### 3. 文档维护
- 及时更新过滤规则文档
- 提供清晰的配置示例
- 记录重要的规则变更
