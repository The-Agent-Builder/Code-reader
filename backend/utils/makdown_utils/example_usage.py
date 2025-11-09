"""
Mermaid to SVG 转换器使用示例
"""
from mermaid_to_svg import MermaidToSvgConverter, convert_mermaid_in_markdown, convert_mermaid_file


def example_1_basic_usage():
    """示例1: 基本用法 - 转换 Markdown 字符串"""
    print("\n" + "="*60)
    print("示例1: 基本用法")
    print("="*60)
    
    markdown = """
# 项目流程图

```mermaid
graph LR
    A[需求分析] --> B[设计]
    B --> C[开发]
    C --> D[测试]
    D --> E[部署]
```
"""
    
    # 使用便捷函数
    result = convert_mermaid_in_markdown(markdown, embed_type='inline', use_cli=False)
    print("✅ 转换完成!")
    print(f"原文长度: {len(markdown)} -> 转换后: {len(result)}")


def example_2_convert_file():
    """示例2: 转换文件"""
    print("\n" + "="*60)
    print("示例2: 转换文件")
    print("="*60)
    
    # 创建测试文件
    test_content = """
# 系统架构

```mermaid
graph TB
    subgraph 前端
        A[React]
        B[TypeScript]
    end
    subgraph 后端
        C[FastAPI]
        D[Python]
    end
    A --> C
    B --> D
```
"""
    
    # 写入测试文件
    with open('test_input.md', 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    # 转换文件
    success = convert_mermaid_file(
        'test_input.md',
        'test_output.md',
        embed_type='inline',
        use_cli=False
    )
    
    if success:
        print("✅ 文件转换成功!")
        print("   输入: test_input.md")
        print("   输出: test_output.md")
    else:
        print("❌ 文件转换失败")


def example_3_multiple_diagrams():
    """示例3: 多个图表"""
    print("\n" + "="*60)
    print("示例3: 处理多个图表")
    print("="*60)
    
    markdown = """
# 文档标题

## 流程图
```mermaid
graph TD
    Start --> Stop
```

## 时序图
```mermaid
sequenceDiagram
    Alice->>John: Hello John
    John-->>Alice: Hi Alice
```

## 类图
```mermaid
classDiagram
    Animal <|-- Duck
    Animal <|-- Fish
```
"""
    
    converter = MermaidToSvgConverter(use_cli=False)
    
    # 先提取所有 mermaid 块
    blocks = converter.extract_mermaid_blocks(markdown)
    print(f"📊 找到 {len(blocks)} 个 Mermaid 图表")
    
    # 转换
    result = converter.convert_markdown(markdown, embed_type='inline')
    print(f"✅ 转换完成!")


def example_4_different_embed_types():
    """示例4: 不同的嵌入方式"""
    print("\n" + "="*60)
    print("示例4: 不同的 SVG 嵌入方式")
    print("="*60)
    
    markdown = """
```mermaid
graph LR
    A --> B
```
"""
    
    converter = MermaidToSvgConverter(use_cli=False)
    
    # 方式1: 内联嵌入
    print("\n1️⃣  内联嵌入 (embed_type='inline')")
    result1 = converter.convert_markdown(markdown, embed_type='inline')
    print(f"   结果长度: {len(result1)} 字符")
    
    # 方式2: Base64 编码
    print("\n2️⃣  Base64 编码 (embed_type='base64')")
    result2 = converter.convert_markdown(markdown, embed_type='base64')
    print(f"   结果长度: {len(result2)} 字符")


async def example_5_async_usage():
    """示例5: 异步使用"""
    print("\n" + "="*60)
    print("示例5: 异步转换")
    print("="*60)
    
    markdown = """
```mermaid
graph TD
    A[异步处理] --> B[非阻塞]
```
"""
    
    converter = MermaidToSvgConverter(use_cli=False)
    result = await converter.convert_markdown_async(markdown, embed_type='inline')
    print("✅ 异步转换完成!")


if __name__ == '__main__':
    print("🎨 Mermaid to SVG 转换器 - 使用示例")
    
    # 运行示例
    example_1_basic_usage()
    example_2_convert_file()
    example_3_multiple_diagrams()
    example_4_different_embed_types()
    
    # 异步示例
    import asyncio
    asyncio.run(example_5_async_usage())
    
    print("\n" + "="*60)
    print("✅ 所有示例运行完成!")
    print("="*60)

