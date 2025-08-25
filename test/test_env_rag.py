"""
验证 .env 中的 RAG_BASE_URL 是否有效

用法:
    python test/test_env_rag.py

说明:
    - 优先从 .env 加载环境变量 (若已安装 python-dotenv)
    - 验证 RAG_BASE_URL 是否存在、格式是否正确
    - 尝试访问健康检查端点 /health
    - 尝试访问文档端点 /docs (可选，仅做连通性参考)
输出为中文，风格参考 example/rag/ 下示例。
"""

import os
import sys
import requests
from urllib.parse import urlparse

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("✅ 已加载 .env 文件")
except ImportError:
    print("⚠️  python-dotenv 未安装，使用系统环境变量")


class RAGConfigTester:
    """RAG 服务配置测试器"""

    def __init__(self):
        self.base_url = os.getenv("RAG_BASE_URL")
        self.timeout = 15

    def check_environment_variable(self) -> bool:
        """检查环境变量是否存在"""
        print("\n🔍 检查环境变量 RAG_BASE_URL ...")
        if not self.base_url:
            print("❌ 错误: 未在环境变量中找到 RAG_BASE_URL")
            print("👉 请在 .env 中添加形如 RAG_BASE_URL=http://host:port 的配置")
            return False

        masked = self.base_url if len(self.base_url) <= 80 else (self.base_url[:60] + "..." + self.base_url[-10:])
        print(f"✅ 找到 RAG_BASE_URL: {masked}")
        return True

    def validate_base_url(self) -> bool:
        """验证 URL 基本格式"""
        print("\n🧩 验证 RAG_BASE_URL 格式 ...")
        try:
            parsed = urlparse(self.base_url)
            if parsed.scheme not in {"http", "https"}:
                print(f"❌ 错误: 不支持的协议: {parsed.scheme!r}，应为 http 或 https")
                return False
            if not parsed.netloc:
                print("❌ 错误: URL 缺少主机名或端口，例如 http://example.com:1234")
                return False
            print("✅ URL 基本格式有效")
            return True
        except Exception as e:
            print(f"❌ URL 解析失败: {e}")
            return False

    def _join(self, path: str) -> str:
        base = self.base_url.rstrip("/")
        path = path if path.startswith("/") else "/" + path
        return base + path

    def test_health_endpoint(self) -> bool:
        """测试 /health 健康检查端点"""
        print("\n🩺 测试 /health 健康检查端点 ...")
        url = self._join("/health")
        try:
            resp = requests.get(url, timeout=self.timeout)
            print(f"➡️  请求: GET {url}")
            print(f"⬅️  响应: {resp.status_code}")
            if resp.status_code == 200:
                print("✅ 服务健康检查通过")
                # 尝试解析内容（如果是 JSON 更好）
                try:
                    data = resp.json()
                    print(f"📄 健康信息: {data}")
                except Exception:
                    text = resp.text.strip()
                    if text:
                        preview = text if len(text) <= 120 else text[:120] + "..."
                        print(f"📄 响应文本: {preview}")
                return True
            else:
                # 尝试打印错误信息
                try:
                    print(f"❌ 健康检查失败: {resp.json()}")
                except Exception:
                    print(f"❌ 健康检查失败，响应文本: {resp.text[:200]}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return False

    def test_docs_endpoint(self) -> bool:
        """尝试访问 /docs 文档端点（非必须）"""
        print("\n📚 访问 /docs 文档端点 (可选) ...")
        url = self._join("/docs")
        try:
            resp = requests.get(url, timeout=self.timeout)
            print(f"➡️  请求: GET {url}")
            print(f"⬅️  响应: {resp.status_code}")
            if resp.status_code == 200:
                print("✅ 文档页面可访问")
                return True
            else:
                print("ℹ️  文档端点未返回 200，但这不一定影响健康检查")
                return False
        except requests.exceptions.RequestException as e:
            print(f"ℹ️  访问 /docs 失败: {e}")
            return False

    def run_all_tests(self) -> bool:
        print("🧪 RAG 服务配置测试工具")
        print("测试 .env 中的 RAG_BASE_URL 并进行连通性校验")

        steps = []
        steps.append(self.check_environment_variable())
        if not steps[-1]:
            return False

        steps.append(self.validate_base_url())
        if not steps[-1]:
            return False

        steps.append(self.test_health_endpoint())

        # 可选：尝试访问 /docs 以辅助判断
        self.test_docs_endpoint()

        return all(steps)


def main():
    tester = RAGConfigTester()
    ok = tester.run_all_tests()

    print("\n" + "=" * 60)
    if ok:
        print("🎉 测试完成: RAG_BASE_URL 有效且服务可用!")
        sys.exit(0)
    else:
        print("💥 测试失败: RAG_BASE_URL 无效或服务不可用!")
        print("\n建议:")
        print("1. 确认 .env 中的 RAG_BASE_URL 是否正确 (协议/域名/端口)")
        print("2. 检查本机或服务器网络连通性、防火墙/安全组设置")
        print("3. 确认目标服务已启动，并支持 /health 端点")
        print("4. 若使用反向代理，检查转发路径是否正确")
        sys.exit(1)


if __name__ == "__main__":
    main()
