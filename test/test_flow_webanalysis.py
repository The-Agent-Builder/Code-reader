#!/usr/bin/env python3
"""
测试 WebAnalysisFlow 的功能
"""

import asyncio
import sys
import os
import logging

# 设置日志格式，确保能看到 logger.info 输出
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from src.flows.web_flow import WebAnalysisFlow, analyze_single_file_data_model

    async def test_web_analysis_flow():
        """测试 WebAnalysisFlow"""
        test_params = {"task_id": 23, "file_id": 415, "vectorstore_index": "document_20250829_20798b3b"}

        flow = WebAnalysisFlow()
        result = await flow.run_async(test_params)

        print(f"状态: {result.get('status')}")
        if result.get("error"):
            print(f"错误: {result.get('error')}")

        return result

    async def test_analyze_function():
        """测试便捷函数"""
        result = await analyze_single_file_data_model(
            task_id=23, file_id=415, vectorstore_index="document_20250829_20798b3b"
        )

        print(f"状态: {result.get('status')}")
        if result.get("error"):
            print(f"错误: {result.get('error')}")

        return result

    async def main():
        """主测试函数"""
        print("WebAnalysisFlow 测试")
        print("参数: task_id=23, file_id=415, vectorstore_index=document_20250829_20798b3b")

        try:
            print("\n测试1: WebAnalysisFlow 类")
            await test_web_analysis_flow()

            # print("\n测试2: analyze_single_file_data_model 函数")
            # await test_analyze_function()

            print("\n测试完成")

        except Exception as e:
            print(f"测试失败: {str(e)}")
            import traceback

            traceback.print_exc()

    if __name__ == "__main__":
        asyncio.run(main())

except ImportError as e:
    print(f"导入失败: {e}")
    print("请安装依赖: pip install python-dotenv aiohttp openai")
