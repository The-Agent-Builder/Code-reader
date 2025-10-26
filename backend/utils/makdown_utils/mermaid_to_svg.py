"""
Mermaid to SVG Converter
将 Markdown 中的 Mermaid 图表转换为 SVG 格式
"""
import re
import base64
import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Tuple, Optional
import asyncio
from utils.call_llm import get_llm_caller


class MermaidToSvgConverter:
    """Mermaid 转 SVG 转换器"""
    
    # 匹配 markdown 中的 mermaid 代码块
    MERMAID_PATTERN = re.compile(
        r'```mermaid\s*\n(.*?)```',
        re.DOTALL | re.MULTILINE
    )
    
    def __init__(self, use_cli: bool = True):
        """
        初始化转换器
        
        Args:
            use_cli: 是否使用 mermaid-cli (需要安装 @mermaid-js/mermaid-cli)
                    如果为 False，则使用在线 API (Kroki)
        """
        self.use_cli = use_cli
        self._check_cli_availability()
    
    def _check_cli_availability(self):
        """检查 mermaid CLI 是否可用"""
        if self.use_cli:
            try:
                result = subprocess.run(
                    ['mmdc', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    print("⚠️  mermaid-cli 未安装，将使用在线 API")
                    print("   安装方法: npm install -g @mermaid-js/mermaid-cli")
                    self.use_cli = False
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print("⚠️  mermaid-cli 未找到，将使用在线 API")
                self.use_cli = False
    
    def extract_mermaid_blocks(self, markdown_content: str) -> List[Tuple[str, str]]:
        """
        从 Markdown 内容中提取所有 mermaid 代码块
        
        Args:
            markdown_content: Markdown 文本内容
            
        Returns:
            包含 (完整匹配文本, mermaid代码) 的元组列表
        """
        matches = []
        for match in self.MERMAID_PATTERN.finditer(markdown_content):
            full_match = match.group(0)  # 完整的 ```mermaid...```
            mermaid_code = match.group(1).strip()  # 只是 mermaid 代码
            matches.append((full_match, mermaid_code))
        return matches
    
    def mermaid_to_svg_cli(self, mermaid_code: str) -> Optional[str]:
        """
        使用 mermaid-cli 将 mermaid 代码转换为 SVG
        
        Args:
            mermaid_code: Mermaid 图表代码
            
        Returns:
            SVG 字符串，失败返回 None
        """
        if not self.use_cli:
            return None
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
                f.write(mermaid_code)
                input_file = f.name
            
            output_file = input_file.replace('.mmd', '.svg')
            
            # 构建 mmdc 命令参数
            cmd = ['mmdc', '-i', input_file, '-o', output_file, '-b', 'transparent']
            
            # 如果存在 puppeteer 配置文件，添加配置参数（用于 Docker 环境）
            puppeteer_config = '/root/puppeteer-config.json'
            if os.path.exists(puppeteer_config):
                cmd.extend(['--puppeteerConfigFile', puppeteer_config])
                print(f"✓ 使用 Puppeteer 配置: {puppeteer_config}")
            else:
                print(f"ℹ️  未找到 Puppeteer 配置文件，使用默认模式")
            
            # 调用 mmdc 命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            print(result.stdout)
            print(result.stderr)
            
            if result.returncode == 0 and os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                
                # 清理临时文件
                os.unlink(input_file)
                os.unlink(output_file)
                
                return svg_content
            else:
                print(f"❌ mermaid-cli 转换失败: {result.stderr}")
                # 清理临时文件
                if os.path.exists(input_file):
                    os.unlink(input_file)
                if os.path.exists(output_file):
                    os.unlink(output_file)
                return None
                
        except Exception as e:
            print(f"❌ mermaid-cli 转换异常: {str(e)}")
            return None
    
    def mermaid_to_svg_kroki(self, mermaid_code: str) -> Optional[str]:
        """
        使用 Kroki API 将 mermaid 代码转换为 SVG
        
        Args:
            mermaid_code: Mermaid 图表代码
            
        Returns:
            SVG 字符串，失败返回 None
        """
        try:
            import requests
            import zlib
            
            # 使用 deflate 压缩 + base64 编码
            compressed = zlib.compress(mermaid_code.encode('utf-8'), level=9)
            encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
            
            # Kroki API URL
            url = f"https://kroki.io/mermaid/svg/{encoded}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"❌ Kroki API 返回错误: {response.status_code}")
                return None
                
        except ImportError:
            print("⚠️  需要安装 requests 库: pip install requests")
            return None
        except Exception as e:
            print(f"❌ Kroki API 调用异常: {str(e)}")
            return None
    
    def fix_mermaid_with_llm(self, mermaid_code: str, error_msg: str = "") -> Optional[str]:
        """
        使用大模型修正 mermaid 代码
        
        Args:
            mermaid_code: 原始 Mermaid 图表代码
            error_msg: 错误信息（可选）
            
        Returns:
            修正后的 mermaid 代码，失败返回 None
        """
        try:
            llm_caller = get_llm_caller()
            
            # 构造提示词
            system_prompt = """你是一个 Mermaid 图表语法专家。你的任务是修正有语法错误的 Mermaid 代码，使其能够正常渲染。

要求：
1. 只返回修正后的 Mermaid 代码，不要有任何其他文字说明
2. 不要包含 ```mermaid 标记，只返回纯代码
3. 保持原有的图表结构和逻辑不变
4. 修正语法错误、格式问题、特殊字符转义等
5. 确保返回的代码符合 Mermaid 最新语法规范"""

            user_prompt = f"""请修正以下 Mermaid 代码：

```mermaid
{mermaid_code}
```
"""
            if error_msg:
                user_prompt += f"\n错误信息：{error_msg}\n"
            
            user_prompt += "\n请直接返回修正后的 Mermaid 代码，不要有其他内容："
            
            messages = llm_caller.create_messages(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            # 调用 LLM
            fixed_code = llm_caller.get_text_response(
                messages=messages,
                temperature=0.1  # 较低的温度以保持代码准确性
            )
            
            # 清理返回的代码（去除可能的 markdown 标记）
            fixed_code = fixed_code.strip()
            if fixed_code.startswith('```mermaid'):
                fixed_code = fixed_code[10:]
            if fixed_code.startswith('```'):
                fixed_code = fixed_code[3:]
            if fixed_code.endswith('```'):
                fixed_code = fixed_code[:-3]
            fixed_code = fixed_code.strip()
            return fixed_code if fixed_code else None
            
        except Exception as e:
            print(f"❌ LLM 修正失败: {str(e)}")
            return None
    
    def mermaid_to_svg(self, mermaid_code: str) -> Optional[str]:
        """
        将 mermaid 代码转换为 SVG（自动选择方法）
        
        Args:
            mermaid_code: Mermaid 图表代码
            
        Returns:
            SVG 字符串，失败返回 None
        """
        # 优先使用 CLI
        if self.use_cli:
            svg = self.mermaid_to_svg_cli(mermaid_code)
            if svg:
                return svg
    
    def convert_markdown(
        self, 
        markdown_content: str, 
        embed_type: str = 'inline',
        max_llm_retries: int = 3
    ) -> str:
        """
        转换 Markdown 中的所有 mermaid 代码块为 SVG
        
        Args:
            markdown_content: 原始 Markdown 内容
            embed_type: SVG 嵌入类型
                       - 'inline': 直接嵌入 SVG 代码
                       - 'base64': 使用 base64 编码的 data URI
                       - 'keep': 保留原始 mermaid 代码块（转换失败时的默认行为）
            max_llm_retries: 使用 LLM 修正代码的最大重试次数（默认3次）
            
        Returns:
            转换后的 Markdown 内容
        """
        mermaid_blocks = self.extract_mermaid_blocks(markdown_content)
        
        if not mermaid_blocks:
            print("ℹ️  未找到 mermaid 代码块")
            return markdown_content
        
        print(f"🔍 找到 {len(mermaid_blocks)} 个 mermaid 代码块")
        
        result = markdown_content
        success_count = 0
        
        for i, (full_match, mermaid_code) in enumerate(mermaid_blocks, 1):
            try:
                print(f"🔄 转换第 {i}/{len(mermaid_blocks)} 个图表...")
                
                # 首次尝试转换
                svg_content = self.mermaid_to_svg(mermaid_code)
                
                # 如果首次转换失败，使用 LLM 修正并重试
                if not svg_content and max_llm_retries > 0:
                    current_code = mermaid_code
                    
                    for retry in range(max_llm_retries):
                        print(f"   🤖 使用 LLM 修正代码（第 {retry + 1}/{max_llm_retries} 次）...")
                        
                        # 使用 LLM 修正代码
                        fixed_code = self.fix_mermaid_with_llm(current_code)
                        
                        if not fixed_code:
                            print(f"   ⚠️  LLM 修正失败")
                            break
                        
                        if fixed_code == current_code:
                            print(f"   ⚠️  LLM 返回相同代码，停止重试")
                            break
                        
                        print(f"   ✨ LLM 已修正代码，重新尝试转换...")
                        current_code = fixed_code
                        
                        # 尝试转换修正后的代码
                        svg_content = self.mermaid_to_svg(current_code)
                        
                        if svg_content:
                            print(f"   ✅ 修正后的代码转换成功！")
                            break
                        else:
                            print(f"   ⚠️  修正后的代码仍然无法转换")
                
                if svg_content:
                    # 根据嵌入类型处理 SVG
                    if embed_type == 'base64':
                        svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
                        replacement = f'<img src="data:image/svg+xml;base64,{svg_base64}" alt="Mermaid Diagram" />'
                    elif embed_type == 'inline':
                        # 直接嵌入 SVG（添加一些样式）
                        replacement = f'\n<div class="mermaid-svg-wrapper">\n{svg_content}\n</div>\n'
                    else:  # keep
                        replacement = full_match
                    
                    result = result.replace(full_match, replacement, 1)
                    success_count += 1
                    print(f"✅ 第 {i} 个图表转换成功")
                else:
                    print(f"⚠️  第 {i} 个图表转换失败（已尝试 LLM 修正 {max_llm_retries} 次），保留原始代码块")
                    
            except Exception as e:
                print(f"❌ 第 {i} 个图表处理时发生异常: {str(e)}")
                import traceback
                traceback.print_exc()
                print(f"⚠️  跳过第 {i} 个图表，继续处理下一个...")
                # 继续处理下一个图表
                continue
        
        print(f"🎉 转换完成: {success_count}/{len(mermaid_blocks)} 成功")
        return result
    
    def convert_file(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        embed_type: str = 'inline',
        encoding: str = 'utf-8',
        max_llm_retries: int = 3
    ) -> bool:
        """
        转换 Markdown 文件中的 mermaid 代码块
        
        Args:
            input_file: 输入 Markdown 文件路径
            output_file: 输出文件路径，如果为 None 则覆盖原文件
            embed_type: SVG 嵌入类型 ('inline', 'base64', 'keep')
            encoding: 文件编码
            max_llm_retries: 使用 LLM 修正代码的最大重试次数（默认3次）
            
        Returns:
            转换是否成功
        """
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                print(f"❌ 文件不存在: {input_file}")
                return False
            
            print(f"📖 读取文件: {input_file}")
            with open(input_path, 'r', encoding=encoding) as f:
                markdown_content = f.read()
            
            # 转换内容
            converted_content = self.convert_markdown(markdown_content, embed_type, max_llm_retries)
            
            # 确定输出路径
            if output_file is None:
                output_path = input_path
                print(f"💾 将覆盖原文件: {input_file}")
            else:
                output_path = Path(output_file)
                print(f"💾 写入新文件: {output_file}")
            
            # 写入文件
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(converted_content)
            
            print(f"✅ 文件转换完成!")
            return True
            
        except Exception as e:
            print(f"❌ 文件转换失败: {str(e)}")
            return False
    
    async def convert_markdown_async(
        self, 
        markdown_content: str, 
        embed_type: str = 'inline',
        max_llm_retries: int = 3
    ) -> str:
        """
        异步转换 Markdown 中的所有 mermaid 代码块为 SVG
        
        Args:
            markdown_content: 原始 Markdown 内容
            embed_type: SVG 嵌入类型
            max_llm_retries: 使用 LLM 修正代码的最大重试次数（默认3次）
            
        Returns:
            转换后的 Markdown 内容
        """
        # 在线程池中执行同步转换
        loop = asyncio.get_event_loop()
        
        # 使用 functools.partial 来传递额外的参数
        from functools import partial
        convert_func = partial(self.convert_markdown, embed_type=embed_type, max_llm_retries=max_llm_retries)
        
        return await loop.run_in_executor(
            None, 
            convert_func,
            markdown_content
        )


# 便捷函数

def convert_mermaid_in_markdown(
    markdown_content: str,
    embed_type: str = 'inline',
    use_cli: bool = True,
    max_llm_retries: int = 3
) -> str:
    """
    便捷函数：转换 Markdown 内容中的 mermaid 代码块
    
    Args:
        markdown_content: Markdown 内容
        embed_type: SVG 嵌入类型 ('inline', 'base64')
        use_cli: 是否优先使用 mermaid-cli
        max_llm_retries: 使用 LLM 修正代码的最大重试次数（默认3次）
        
    Returns:
        转换后的 Markdown 内容
    """
    converter = MermaidToSvgConverter(use_cli=use_cli)
    return converter.convert_markdown(markdown_content, embed_type, max_llm_retries)


def convert_mermaid_file(
    input_file: str,
    output_file: Optional[str] = None,
    embed_type: str = 'inline',
    use_cli: bool = True,
    max_llm_retries: int = 3
) -> bool:
    """
    便捷函数：转换 Markdown 文件中的 mermaid 代码块
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（None 表示覆盖原文件）
        embed_type: SVG 嵌入类型 ('inline', 'base64')
        use_cli: 是否优先使用 mermaid-cli
        max_llm_retries: 使用 LLM 修正代码的最大重试次数（默认3次）
        
    Returns:
        转换是否成功
    """
    converter = MermaidToSvgConverter(use_cli=use_cli)
    return converter.convert_file(input_file, output_file, embed_type, max_llm_retries=max_llm_retries)


if __name__ == '__main__':
    # 示例用法
    example_markdown = """

"""
    
    print("=" * 60)
    print("Mermaid to SVG 转换器 - 示例")
    print("=" * 60)
    
    converter = MermaidToSvgConverter(use_cli=False)  # 使用在线 API 演示
    result = converter.convert_markdown(example_markdown, embed_type='inline')
    
    print("\n" + "=" * 60)
    print("转换结果预览 (前500字符):")
    print("=" * 60)
    print(result[:500] + "...\n")


