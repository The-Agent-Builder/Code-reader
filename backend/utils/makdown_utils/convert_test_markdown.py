"""
将 test_markdown.md 中的 Mermaid 图表转换为 SVG
"""
from .mermaid_to_svg import MermaidToSvgConverter
import os


def main():
    """主函数"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 输入和输出文件路径
    input_file = os.path.join(current_dir, 'test_markdown.md')
    output_file = os.path.join(current_dir, 'test_markdown_converted.md')
    
    print("=" * 70)
    print("Mermaid 转 SVG 转换工具")
    print("=" * 70)
    print(f"📖 输入文件: {input_file}")
    print(f"💾 输出文件: {output_file}")
    print()
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 错误: 输入文件不存在: {input_file}")
        return
    
    # 创建转换器（使用在线 API，避免依赖 mermaid-cli）
    print("🔧 初始化转换器...")
    converter = MermaidToSvgConverter(use_cli=True)
    print()
    
    # 读取文件内容
    print("📖 读取文件内容...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        print(f"✅ 成功读取文件，大小: {len(markdown_content)} 字符")
    except Exception as e:
        print(f"❌ 读取文件失败: {str(e)}")
        return
    result = converter.convert_markdown(markdown_content, embed_type='inline', max_llm_retries=3)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"✅ 成功转换: {success_count} 个图表")
    print(f"⚠️  转换失败: {failed_count} 个图表")
    print(f"📈 成功率: {success_count / len(mermaid_blocks) * 100:.1f}%")
    print()
if __name__ == '__main__':
    main()


