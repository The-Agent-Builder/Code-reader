import os
import sys
import requests

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("✅ 已加载 .env 文件")
except ImportError:
    print("⚠️  python-dotenv 未安装，使用系统环境变量")


def test_github_token():
    """测试 GitHub Token 的有效性"""
    print("\n🔍 开始测试 GitHub Token...")
    print("=" * 50)

    # 1. 检查 Token 是否存在
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ 错误: GITHUB_TOKEN 环境变量未设置")
        print("请检查 .env 文件是否存在并包含 GITHUB_TOKEN")
        return False

    print(f"✅ 找到 Token: {token[:10]}...{token[-4:]}")

    # 2. 检查 Token 格式
    if not token.startswith(("ghp_", "github_pat_", "gho_", "ghu_", "ghs_")):
        print(f"⚠️  警告: Token 格式可能不正确 (应以 ghp_ 等开头)")

    if len(token) < 20:
        print(f"⚠️  警告: Token 长度可能太短 ({len(token)} 字符)")

    # 3. 测试 API 访问
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Token-Test/1.0",
    }

    try:
        print("\n🌐 正在测试 GitHub API 连接...")
        response = requests.get("https://api.github.com/user", headers=headers, timeout=15)

        print(f"📡 响应状态码: {response.status_code}")

        if response.status_code == 200:
            user_data = response.json()
            print("\n🎉 GitHub Token 验证成功!")
            print(f"   👤 用户名: {user_data.get('login', 'N/A')}")
            print(f"   🆔 用户ID: {user_data.get('id', 'N/A')}")
            print(f"   📝 用户类型: {user_data.get('type', 'N/A')}")
            print(f"   📧 邮箱: {user_data.get('email', '未公开')}")

            # 显示权限信息
            scopes = response.headers.get("X-OAuth-Scopes", "")
            print(f"   🔑 Token 权限: {scopes if scopes else '无特定权限'}")

            # 显示速率限制信息
            remaining = response.headers.get("X-RateLimit-Remaining", "N/A")
            limit = response.headers.get("X-RateLimit-Limit", "N/A")

            return True

        elif response.status_code == 401:
            print("\n❌ Token 验证失败!")
            error_msg = response.json().get("message", "未知错误")
            print(f"   错误信息: {error_msg}")
            print("   可能原因:")
            print("   - Token 已过期")
            print("   - Token 格式错误")
            print("   - Token 已被撤销")
            return False

        elif response.status_code == 403:
            print("\n❌ Token 权限不足或达到速率限制!")
            error_msg = response.json().get("message", "未知错误")
            print(f"   错误信息: {error_msg}")
            return False

        else:
            print(f"\n❌ 未知错误，状态码: {response.status_code}")
            print(f"   响应内容: {response.text[:200]}...")
            return False

    except requests.exceptions.Timeout:
        print("\n❌ 请求超时!")
        print("   请检查网络连接")
        return False

    except requests.exceptions.ConnectionError:
        print("\n❌ 网络连接错误!")
        print("   请检查网络连接或代理设置")
        return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ 网络请求失败: {e}")
        return False

    except Exception as e:
        print(f"\n❌ 发生未知错误: {e}")
        return False


def main():
    """主函数"""
    print("GitHubToken 验证工具: 检查 .env 文件中的 GITHUB_TOKEN 是否有效")
    print("GitHubToken:", os.getenv("GITHUB_TOKEN"))

    success = test_github_token()

    print("\n" + "=" * 50)
    if success:
        print("🎉 测试完成: GitHub Token 有效且可用!")
        sys.exit(0)
    else:
        print("💥 测试失败: GitHub Token 无效或不可用!")
        print("\n建议:")
        print("1. 检查 .env 文件中的 GITHUB_TOKEN 是否正确")
        print("2. 确认 Token 未过期")
        print("3. 验证网络连接正常")
        sys.exit(1)


if __name__ == "__main__":
    main()
