# Python 缩进错误修复规则

## 问题描述
当遇到 Python 缩进错误 "unindent does not match any outer indentation level" 时的修复方法。

## 常见原因
1. try-except 块中的代码缩进不一致
2. if-else 语句的缩进级别错误
3. 混合使用空格和制表符
4. 代码块内部的缩进不统一

## 修复步骤
1. 查看错误行号及其周围的上下文
2. 检查 try-except 块的完整结构
3. 确保同一代码块内的所有语句使用相同的缩进级别
4. 特别注意 if-else 语句应该与同级别的其他语句对齐

## 示例修复
```python
# 错误的缩进
try:
        if condition:  # 错误：额外的缩进
            do_something()
        else:
            do_other()
    
    other_code()  # 错误：缩进不匹配
except Exception as e:
    handle_error()

# 正确的缩进
try:
    if condition:  # 正确：与 try 块内其他语句对齐
        do_something()
    else:
        do_other()
    
    other_code()  # 正确：与 if 语句同级
except Exception as e:
    handle_error()
```

## 检查工具
使用 IDE 的诊断功能或 Python 语法检查器来验证修复结果。

## 修复案例记录

### 案例1: code_parsing_batch_node.py
- **错误**: 第108行 except 语句缩进不匹配
- **原因**: try 块内的 if 语句和其他代码缩进不一致
- **修复**: 统一 try 块内所有语句的缩进级别

### 案例2: result_storage.py
- **错误**: 第247行 except 语句缩进不匹配
- **原因**: try 块内的 with 语句有多余的缩进
- **修复**: 将 with 语句的缩进从8个空格减少到4个空格，与同级语句对齐
