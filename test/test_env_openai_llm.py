"""
测试 OpenAI API 配置的有效性

测试 .env 文件中的以下配置:
- OPENAI_API_KEY: API 密钥
- OPENAI_BASE_URL: API 基础URL
- OPENAI_MODEL: 模型名称

使用方法:
    python test/test_env_openai_llm.py
"""

import os
import sys
import json
import requests
from urllib.parse import urljoin, urlparse

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("✅ 已加载 .env 文件")
except ImportError:
    print("⚠️  python-dotenv 未安装，使用系统环境变量")


class OpenAIConfigTester:
    """OpenAI API 配置测试器"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self.model = os.getenv("OPENAI_MODEL")
        self.timeout = 30

    def check_environment_variables(self):
        """检查环境变量是否设置"""
        print("\n🔍 检查环境变量...")
        print("=" * 50)

        issues = []

        # 检查 API Key
        if not self.api_key:
            issues.append("❌ OPENAI_API_KEY 未设置")
        else:
            print(f"✅ OPENAI_API_KEY: {self.api_key[:10]}...{self.api_key[-4:]}")

        # 检查 Base URL
        if not self.base_url:
            issues.append("❌ OPENAI_BASE_URL 未设置")
        else:
            print(f"✅ OPENAI_BASE_URL: {self.base_url}")

        # 检查模型名称
        if not self.model:
            issues.append("❌ OPENAI_MODEL 未设置")
        else:
            print(f"✅ OPENAI_MODEL: {self.model}")

        if issues:
            print("\n发现问题:")
            for issue in issues:
                print(f"  {issue}")
            return False

        return True

    def validate_base_url(self):
        """验证 Base URL 格式"""
        print("\n🌐 验证 Base URL 格式...")
        print("=" * 50)

        try:
            parsed = urlparse(self.base_url)

            # 检查协议
            if parsed.scheme not in ["http", "https"]:
                print(f"❌ URL 协议无效: {parsed.scheme} (应为 http 或 https)")
                return False

            # 检查域名
            if not parsed.netloc:
                print("❌ URL 缺少域名")
                return False

            print(f"✅ URL 格式有效")
            print(f"   协议: {parsed.scheme}")
            print(f"   域名: {parsed.netloc}")
            print(f"   路径: {parsed.path}")

            return True

        except Exception as e:
            print(f"❌ URL 格式错误: {e}")
            return False

    def test_api_connectivity(self):
        """测试 API 连接性"""
        print("\n🔗 测试 API 连接性...")
        print("=" * 50)

        # 构建模型列表 URL
        models_url = urljoin(self.base_url.rstrip("/") + "/", "models")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OpenAI-Config-Test/1.0",
        }

        try:
            print(f"📡 请求 URL: {models_url}")
            response = requests.get(models_url, headers=headers, timeout=self.timeout)

            print(f"📊 响应状态码: {response.status_code}")

            if response.status_code == 200:
                print("✅ API 连接成功!")

                try:
                    data = response.json()
                    if "data" in data and isinstance(data["data"], list):
                        models = [model.get("id", "unknown") for model in data["data"]]
                        print(f"📋 可用模型数量: {len(models)}")

                        # 检查配置的模型是否在列表中
                        if self.model in models:
                            print(f"✅ 配置的模型 '{self.model}' 可用")
                        else:
                            print(f"⚠️  配置的模型 '{self.model}' 不在可用列表中")
                            print("   前10个可用模型:")
                            for model in models[:10]:
                                print(f"     - {model}")

                    else:
                        print("⚠️  响应格式异常，无法解析模型列表")

                except json.JSONDecodeError:
                    print("⚠️  响应不是有效的 JSON 格式")
                    print(f"   响应内容: {response.text[:200]}...")

                return True

            elif response.status_code == 401:
                print("❌ API 认证失败!")
                print("   可能原因:")
                print("   - API Key 无效或已过期")
                print("   - API Key 格式错误")
                return False

            elif response.status_code == 403:
                print("❌ API 访问被拒绝!")
                print("   可能原因:")
                print("   - API Key 权限不足")
                print("   - 达到速率限制")
                return False

            elif response.status_code == 404:
                print("❌ API 端点不存在!")
                print("   可能原因:")
                print("   - Base URL 配置错误")
                print("   - API 版本不兼容")
                return False

            else:
                print(f"❌ API 请求失败，状态码: {response.status_code}")
                print(f"   响应内容: {response.text[:200]}...")
                return False

        except requests.exceptions.Timeout:
            print(f"❌ 请求超时 (>{self.timeout}秒)")
            print("   可能原因:")
            print("   - 网络连接慢")
            print("   - 服务器响应慢")
            return False

        except requests.exceptions.ConnectionError:
            print("❌ 网络连接错误!")
            print("   可能原因:")
            print("   - 网络不可达")
            print("   - DNS 解析失败")
            print("   - 代理配置问题")
            return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return False

    def test_chat_completion(self):
        """测试聊天完成 API"""
        print("\n💬 测试聊天完成 API...")
        print("=" * 50)

        chat_url = urljoin(self.base_url.rstrip("/") + "/", "chat/completions")

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        # 简单的测试请求
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": '你好，请回复"测试成功"'}],
            "max_tokens": 50,
            "temperature": 0.1,
        }

        try:
            print(f"📡 请求 URL: {chat_url}")
            print(f"🤖 使用模型: {self.model}")

            response = requests.post(chat_url, headers=headers, json=payload, timeout=self.timeout)

            print(f"📊 响应状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()

                    if "choices" in data and len(data["choices"]) > 0:
                        message = data["choices"][0].get("message", {})
                        content = message.get("content", "").strip()

                        print("✅ 聊天完成 API 测试成功!")
                        print(f"   🤖 模型响应: {content}")

                        # 检查使用情况
                        usage = data.get("usage", {})
                        if usage:
                            print(f"   📊 Token 使用:")
                            print(f"     - 输入: {usage.get('prompt_tokens', 'N/A')}")
                            print(f"     - 输出: {usage.get('completion_tokens', 'N/A')}")
                            print(f"     - 总计: {usage.get('total_tokens', 'N/A')}")

                        return True

                    else:
                        print("❌ 响应格式异常，缺少 choices 字段")
                        print(f"   响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        return False

                except json.JSONDecodeError:
                    print("❌ 响应不是有效的 JSON 格式")
                    print(f"   响应内容: {response.text[:200]}...")
                    return False

            else:
                print(f"❌ 聊天完成 API 请求失败，状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "未知错误")
                    print(f"   错误信息: {error_msg}")
                except:
                    print(f"   响应内容: {response.text[:200]}...")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 OpenAI API 配置测试工具")
        print("测试 .env 文件中的 OpenAI 相关配置")

        results = []

        # 1. 检查环境变量
        results.append(self.check_environment_variables())

        if not results[-1]:
            return False

        # 2. 验证 URL 格式
        results.append(self.validate_base_url())

        # 3. 测试 API 连接
        results.append(self.test_api_connectivity())

        # 4. 测试聊天完成
        if results[-1]:  # 只有连接成功才测试聊天
            results.append(self.test_chat_completion())
        else:
            results.append(False)

        return all(results)


def main():
    """主函数"""
    tester = OpenAIConfigTester()

    success = tester.run_all_tests()

    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过! OpenAI API 配置正确且可用!")
        sys.exit(0)
    else:
        print("💥 测试失败! 请检查 OpenAI API 配置!")
        print("\n建议:")
        print("1. 验证 .env 文件中的配置项是否正确")
        print("2. 检查 API Key 是否有效")
        print("3. 确认 Base URL 是否可访问")
        print("4. 验证模型名称是否正确")
        sys.exit(1)


if __name__ == "__main__":
    main()
