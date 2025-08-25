"""
LLM Prompt 模板模块
包含所有用于代码分析的 prompt 模板
"""


class CodeAnalysisPrompts:
    """代码分析 Prompt 模板类"""

    @staticmethod
    def get_analysis_prompt(code: str, file_path: str, language: str, context: str = "") -> str:
        """获取代码分析的prompt模板，生成详细的文档分析"""
        return f"""
请分析以下{language}代码文件，为每个重要的函数和类生成详细的文档分析。

文件路径: {file_path}
编程语言: {language}

上下文信息:
{context}

代码内容:
```{language}
{code}
```

请按照以下JSON格式返回分析结果，为每个函数和类生成类似技术文档的详细分析：

{{
    "functions": [
        {{
            "title": "函数名称或简短标题",
            "description": "详细描述函数的功能、用途、实现方式和技术特点（3-5句话，要具体和专业）",
            "source": "{file_path}:起始行号-结束行号",
            "language": "{language}",
            "code": "完整的函数代码",
            "parameters": "函数参数说明（如果有）",
            "returns": "返回值说明（如果有）",
            "usage_example": "使用示例或调用方式（如果适用）"
        }}
    ],
    "classes": [
        {{
            "title": "类名称或简短标题",
            "description": "详细描述类的功能、设计模式、继承关系、主要方法和使用场景（3-5句话，要具体和专业）",
            "source": "{file_path}:起始行号-结束行号",
            "language": "{language}",
            "code": "完整的类代码",
            "inheritance": "继承关系说明（如果有）",
            "key_methods": "主要方法列表（如果有）",
            "usage_example": "使用示例或实例化方式（如果适用）"
        }}
    ],
    "code_snippets": [
        {{
            "title": "重要代码片段的标题",
            "description": "描述代码片段的功能和技术实现（如配置、常量定义、重要逻辑等）",
            "source": "{file_path}:起始行号-结束行号",
            "language": "{language}",
            "code": "代码片段内容"
        }}
    ]
}}

分析要求：
1. description要详细专业，类似技术文档的描述风格
2. 重点分析函数/类的技术实现、设计模式、使用场景
3. source格式严格按照"文件名:起始行号-结束行号"
4. 包含重要的配置、常量、工具函数等代码片段
5. 提供实际的使用示例和参数说明
6. 突出代码的技术特点和架构设计
"""

    @staticmethod
    def get_detailed_analysis_prompt(code: str, file_path: str, language: str, context: str = "") -> str:
        """获取详细分析的 prompt 模板，生成类似 res.md 格式的分析"""
        context_section = f"\n相关上下文信息:\n{context}\n" if context else ""

        return f"""
你是一个专业的代码分析专家。请对以下{language}代码文件进行详细的技术分析，为每个重要的函数、类和代码片段生成专业的技术文档。

文件路径: {file_path}
编程语言: {language}{context_section}

代码内容:
```{language}
{code}
```

请按照以下JSON格式返回分析结果，为每个重要的代码元素生成详细的技术分析：

{{
    "analysis_items": [
        {{
            "title": "简洁明确的标题（如：AsyncNode类 或 parse_code_file函数）",
            "description": "详细的技术描述，包括：功能说明、技术实现、设计模式、使用场景、参数说明、返回值等（3-5句专业描述）",
            "source": "{file_path}:起始行号-结束行号",
            "language": "{language}",
            "code": "完整的代码内容"
        }}
    ]
}}

分析要求：
1. **TITLE**: 简洁明确，格式如"AsyncNode类"、"parse_code_file函数"、"配置常量"等
2. **DESCRIPTION**: 详细专业的技术描述，包括：
  - 功能和用途说明
  - 技术实现方式
  - 设计模式或架构特点
  - 参数和返回值说明
  - 使用场景和注意事项
3. **SOURCE**: 严格按照"{file_path}:起始行号-结束行号"格式
4. **LANGUAGE**: 编程语言标识
5. **CODE**: 完整的代码内容

重点分析：
- 类定义及其方法
- 重要函数和方法
- 配置和常量定义
- 核心业务逻辑
- 工具函数和辅助方法
- 重要的代码片段

忽略：
- 简单的getter/setter
- 空方法或占位符
- 过于简单的变量赋值

请确保分析结果专业、详细，类似技术文档的风格。只返回JSON格式的结果，不要其他内容。
"""

    @staticmethod
    def get_system_message() -> str:
        """获取系统消息"""
        return "你是一个专业的代码分析专家，擅长分析各种编程语言的代码结构。"
