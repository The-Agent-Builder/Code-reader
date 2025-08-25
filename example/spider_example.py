import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime


class GitHubSpider:
    def __init__(self, github_token=None):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        self.github_token = github_token
        if github_token:
            self.session.headers.update({"Authorization": f"token {github_token}"})

    def extract_repo_info(self, github_url):
        """
        爬取GitHub仓库基础信息

        Args:
            github_url (str): GitHub仓库URL

        Returns:
            dict: 包含仓库基础信息的字典
        """
        # 如果有GitHub token，优先使用API
        if self.github_token:
            api_result = self._get_repo_info_via_api(github_url)
            if "error" not in api_result:
                return api_result
            # 如果API失败，回退到网页爬取
            print("API获取失败，回退到网页爬取...")

        try:
            # 验证URL格式
            if not self._is_valid_github_url(github_url):
                return {"error": "无效的GitHub URL"}

            response = self.session.get(github_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 提取基础信息
            primary_lang = self._get_primary_language(soup)
            repo_info = {
                "url": github_url,
                "name": self._get_repo_name(soup),
                "description": self._get_description(soup),
                "primary_language": primary_lang,
                "languages": {"message": "网页爬取无法获取语言占比，请使用GitHub API"},
                "stars": self._get_stars(soup),
                "forks": self._get_forks(soup),
                "watchers": self._get_watchers(soup),
                "topics": self._get_topics(soup),
                "last_updated": self._get_last_updated(soup),
                "license": self._get_license(soup),
                "source": "网页爬取",
            }

            return repo_info

        except requests.RequestException as e:
            return {"error": f"请求失败: {str(e)}"}
        except Exception as e:
            return {"error": f"解析失败: {str(e)}"}

    def _get_repo_info_via_api(self, github_url):
        """
        通过GitHub API获取仓库信息

        Args:
            github_url (str): GitHub仓库URL

        Returns:
            dict: 包含仓库基础信息的字典
        """
        try:
            # 从URL提取owner和repo名称
            parts = github_url.rstrip("/").split("/")
            if len(parts) < 2:
                return {"error": "无法解析GitHub URL"}

            owner = parts[-2]
            repo = parts[-1]

            # 调用GitHub API获取基本信息
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(api_url)
            response.raise_for_status()

            data = response.json()

            # 获取语言占比信息
            languages_info = self._get_languages_via_api(owner, repo)

            # 格式化时间
            updated_at = data.get("updated_at", "")
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    updated_at = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except:
                    pass

            # 构建返回信息
            repo_info = {
                "url": github_url,
                "name": data.get("name", "未知"),
                "description": data.get("description", "无描述"),
                "primary_language": data.get("language", "未知"),
                "languages": languages_info,
                "stars": self._format_number(data.get("stargazers_count", 0)),
                "forks": self._format_number(data.get("forks_count", 0)),
                "watchers": self._format_number(data.get("watchers_count", 0)),
                "topics": data.get("topics", []),
                "last_updated": updated_at or "未知",
                "license": data.get("license", {}).get("name", "未知") if data.get("license") else "未知",
                "source": "GitHub API",
            }

            return repo_info

        except requests.RequestException as e:
            return {"error": f"API请求失败: {str(e)}"}
        except Exception as e:
            return {"error": f"API解析失败: {str(e)}"}

    def _get_languages_via_api(self, owner, repo):
        """
        通过GitHub API获取语言占比信息

        Args:
            owner (str): 仓库所有者
            repo (str): 仓库名称

        Returns:
            dict: 语言占比信息
        """
        try:
            # 调用GitHub Languages API
            api_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
            response = self.session.get(api_url)
            response.raise_for_status()

            languages_data = response.json()

            if not languages_data:
                return {"message": "未检测到编程语言"}

            # 计算总字节数
            total_bytes = sum(languages_data.values())

            # 计算每种语言的占比
            languages_percentage = {}
            for language, bytes_count in languages_data.items():
                percentage = (bytes_count / total_bytes) * 100
                languages_percentage[language] = {"bytes": bytes_count, "percentage": round(percentage, 2)}

            # 按占比排序
            sorted_languages = dict(
                sorted(languages_percentage.items(), key=lambda x: x[1]["percentage"], reverse=True)
            )

            return sorted_languages

        except requests.RequestException as e:
            return {"error": f"语言API请求失败: {str(e)}"}
        except Exception as e:
            return {"error": f"语言数据解析失败: {str(e)}"}

    def _format_number(self, num):
        """格式化数字显示"""
        if num >= 1000:
            return f"{num/1000:.1f}k"
        return str(num)

    def _is_valid_github_url(self, url):
        """验证是否为有效的GitHub URL"""
        pattern = r"^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$"
        return bool(re.match(pattern, url))

    def _get_repo_name(self, soup):
        """获取仓库名称"""
        name_elem = soup.find("strong", {"itemprop": "name"})
        return name_elem.text.strip() if name_elem else "未知"

    def _get_description(self, soup):
        """获取仓库描述"""
        desc_elem = soup.find("p", class_="f4 my-3")
        return desc_elem.text.strip() if desc_elem else "无描述"

    def _get_primary_language(self, soup):
        """获取主要编程语言"""
        # 方法1: 标准的itemprop选择器
        lang_elem = soup.find("span", {"itemprop": "programmingLanguage"})
        if lang_elem:
            return lang_elem.text.strip()

        # 方法2: 查找语言统计区域
        lang_bar = soup.find("div", class_="BorderGrid-cell")
        if lang_bar:
            lang_items = lang_bar.find_all("span", class_="color-fg-default")
            for item in lang_items:
                text = item.get_text(strip=True)
                # 过滤掉百分比和数字
                if text and not any(char in text for char in ["%", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]):
                    return text

        # 方法3: 查找文件列表中的语言信息
        file_icons = soup.find_all("svg", class_="octicon")
        for icon in file_icons:
            parent = icon.find_parent()
            if parent and parent.name == "span":
                next_elem = parent.find_next_sibling()
                if next_elem and next_elem.text:
                    text = next_elem.text.strip()
                    # 检查是否是常见的编程语言
                    common_langs = [
                        "Python",
                        "JavaScript",
                        "TypeScript",
                        "Java",
                        "C++",
                        "C#",
                        "Go",
                        "Rust",
                        "PHP",
                        "Ruby",
                    ]
                    if any(lang.lower() in text.lower() for lang in common_langs):
                        return text

        return "未知"

    def _get_stars(self, soup):
        """获取星标数"""
        # 尝试多种选择器获取星标数
        stars_elem = soup.find("a", href=lambda x: x and "/stargazers" in x)
        if stars_elem:
            # 查找包含数字的元素
            for elem in stars_elem.find_all(["strong", "span"]):
                text = elem.get_text(strip=True)
                if text and (text.isdigit() or "k" in text.lower()):
                    return text

        # 备用方法：查找包含"star"的按钮或链接
        star_button = soup.find("button", {"data-view-component": "true"})
        if star_button:
            star_text = star_button.get_text(strip=True)
            if "star" in star_text.lower():
                # 提取数字
                import re

                numbers = re.findall(r"[\d,]+", star_text)
                if numbers:
                    return numbers[0]
        return "0"

    def _get_forks(self, soup):
        """获取分叉数"""
        forks_elem = soup.find("a", href=lambda x: x and "/forks" in x)
        if forks_elem:
            for elem in forks_elem.find_all(["strong", "span"]):
                text = elem.get_text(strip=True)
                if text and (text.isdigit() or "k" in text.lower()):
                    return text
        return "0"

    def _get_watchers(self, soup):
        """获取关注者数"""
        watchers_elem = soup.find("a", href=lambda x: x and "/watchers" in x)
        if watchers_elem:
            for elem in watchers_elem.find_all(["strong", "span"]):
                text = elem.get_text(strip=True)
                if text and (text.isdigit() or "k" in text.lower()):
                    return text
        return "0"

    def _get_topics(self, soup):
        """获取主题标签"""
        topics = []
        topic_elems = soup.find_all("a", class_="topic-tag")
        for topic in topic_elems:
            topics.append(topic.text.strip())
        return topics

    def _get_last_updated(self, soup):
        """获取最后更新时间"""
        # 方法1: 查找relative-time元素
        time_elem = soup.find("relative-time")
        if time_elem:
            datetime_val = time_elem.get("datetime")
            if datetime_val:
                return datetime_val
            title_val = time_elem.get("title")
            if title_val:
                return title_val
            text_val = time_elem.text.strip()
            if text_val:
                return text_val

        # 方法2: 查找所有time元素
        time_elems = soup.find_all("time")
        for time_elem in time_elems:
            datetime_val = time_elem.get("datetime")
            if datetime_val:
                return datetime_val
            text_val = time_elem.text.strip()
            if text_val and ("ago" in text_val or "on" in text_val):
                return text_val

        # 方法3: 查找提交信息区域
        commit_area = soup.find("div", class_="Box-header")
        if commit_area:
            time_spans = commit_area.find_all("span")
            for span in time_spans:
                text = span.text.strip()
                if "ago" in text or "on" in text:
                    return text

        # 方法4: 查找包含时间的链接或文本
        for elem in soup.find_all(["a", "span", "div"]):
            text = elem.get_text(strip=True)
            if text and ("ago" in text or "committed" in text) and len(text) < 50:
                # 提取时间相关的文本
                import re

                time_pattern = r"\b\d+\s+(second|minute|hour|day|week|month|year)s?\s+ago\b"
                if re.search(time_pattern, text):
                    return text

        return "未知"

    def _get_license(self, soup):
        """获取许可证信息"""
        license_elem = soup.find(
            "a", href=lambda x: x and "/blob/main/LICENSE" in x or x and "/blob/master/LICENSE" in x
        )
        return license_elem.text.strip() if license_elem else "未知"


def debug_page_structure(url):
    """调试页面结构，帮助找到正确的选择器"""
    import requests
    from bs4 import BeautifulSoup

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

    response = session.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    print("=== 调试信息 ===")

    # 查找所有可能包含语言信息的元素
    print("\n1. 查找语言相关元素:")
    lang_candidates = soup.find_all(
        text=lambda text: text
        and any(lang in text for lang in ["Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "PHP"])
    )
    for i, candidate in enumerate(lang_candidates[:5]):
        print(f"   {i+1}. {candidate.strip()}")

    # 查找所有时间相关元素
    print("\n2. 查找时间相关元素:")
    time_elements = soup.find_all(["time", "relative-time"])
    for i, elem in enumerate(time_elements[:5]):
        print(f"   {i+1}. Tag: {elem.name}, Attrs: {elem.attrs}, Text: {elem.get_text(strip=True)}")

    # 查找包含"ago"的文本
    print("\n3. 查找包含'ago'的文本:")
    ago_texts = soup.find_all(text=lambda text: text and "ago" in text.lower())
    for i, text in enumerate(ago_texts[:5]):
        print(f"   {i+1}. {text.strip()}")


def main():
    """示例使用"""
    # GitHub API Token（可选，但推荐使用以获取更准确的信息）
    github_token = "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"

    # 创建爬虫实例
    spider = GitHubSpider(github_token=github_token)

    # 您可以在这里修改要爬取的GitHub URL
    test_url = "https://github.com/The-Pocket/PocketFlow"

    # 启用调试模式（设为False关闭调试）
    debug_mode = False

    if debug_mode:
        debug_page_structure(test_url)
        print("\n" + "=" * 50 + "\n")

    print(f"正在爬取: {test_url}")
    if github_token:
        print("使用GitHub API获取数据...")
    else:
        print("使用网页爬取获取数据...")

    result = spider.extract_repo_info(test_url)

    # 格式化输出
    print("\n=== GitHub仓库信息 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 如果需要保存到文件
    # with open('github_info.json', 'w', encoding='utf-8') as f:
    #     json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
