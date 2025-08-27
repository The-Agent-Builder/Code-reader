"""
测试 LocalFolderNode 节点
"""

import sys
import os
from pathlib import Path
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.nodes.local_folder_node import LocalFolderNode
from src.utils.error_handler import GitCloneError


class TestLocalFolderNode:
    """LocalFolderNode 测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.node = LocalFolderNode()
        # 使用项目根目录的相对路径
        project_root = Path(__file__).parent.parent
        self.test_repo_path = str(project_root / "data" / "repos" / "GTPlanner")

    def test_prep_with_valid_path(self):
        """测试 prep 方法 - 有效路径"""
        shared = {"local_folder_path": self.test_repo_path}

        result = self.node.prep(shared)

        assert result == self.test_repo_path
        assert shared["current_stage"] == "local_folder_processing"

    def test_prep_with_empty_path(self):
        """测试 prep 方法 - 空路径"""
        shared = {}

        with pytest.raises(GitCloneError, match="Local folder path is required"):
            self.node.prep(shared)

    def test_prep_with_none_path(self):
        """测试 prep 方法 - None 路径"""
        shared = {"local_folder_path": None}

        with pytest.raises(GitCloneError, match="Local folder path is required"):
            self.node.prep(shared)

    def test_exec_with_existing_directory(self):
        """测试 exec 方法 - 存在的目录"""
        if not Path(self.test_repo_path).exists():
            pytest.skip(f"测试目录不存在: {self.test_repo_path}")

        result = self.node.exec(self.test_repo_path)

        assert isinstance(result, Path)
        assert result.exists()
        assert result.is_dir()
        assert str(result) == str(Path(self.test_repo_path))

    def test_exec_with_nonexistent_directory(self):
        """测试 exec 方法 - 不存在的目录"""
        nonexistent_path = "/path/that/does/not/exist"

        with pytest.raises(GitCloneError, match="Local folder path does not exist"):
            self.node.exec(nonexistent_path)

    def test_exec_with_file_instead_of_directory(self):
        """测试 exec 方法 - 文件而非目录"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            with pytest.raises(GitCloneError, match="Path is not a directory"):
                self.node.exec(temp_file_path)
        finally:
            os.unlink(temp_file_path)

    def test_post_with_valid_path(self):
        """测试 post 方法 - 有效路径"""
        if not Path(self.test_repo_path).exists():
            pytest.skip(f"测试目录不存在: {self.test_repo_path}")

        shared = {}
        prep_res = self.test_repo_path
        exec_res = Path(self.test_repo_path)

        result = self.node.post(shared, prep_res, exec_res)

        assert result == "default"
        assert "local_path" in shared
        assert "repo_info" in shared
        assert "repo_url" in shared

        # 验证 repo_info 结构
        repo_info = shared["repo_info"]
        assert repo_info["name"] == "GTPlanner"
        assert repo_info["full_name"] == "local/GTPlanner"
        assert repo_info["source"] == "local_folder"
        assert "language" in repo_info
        assert "size" in repo_info

    def test_detect_primary_language_python(self):
        """测试语言检测 - Python 项目"""
        # 创建临时目录结构
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建 Python 文件
            (temp_path / "main.py").write_text("print('hello')")
            (temp_path / "utils.py").write_text("def func(): pass")
            (temp_path / "test.js").write_text("console.log('hello')")

            language = self.node._detect_primary_language(temp_path)
            assert language == "Python"

    def test_detect_primary_language_javascript(self):
        """测试语言检测 - JavaScript 项目"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建更多 JavaScript 文件
            (temp_path / "app.js").write_text("console.log('app')")
            (temp_path / "utils.js").write_text("function test() {}")
            (temp_path / "index.js").write_text("const x = 1")
            (temp_path / "main.py").write_text("print('hello')")

            language = self.node._detect_primary_language(temp_path)
            assert language == "JavaScript"

    def test_detect_primary_language_unknown(self):
        """测试语言检测 - 未知语言"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建非代码文件
            (temp_path / "readme.txt").write_text("readme")
            (temp_path / "data.csv").write_text("a,b,c")

            language = self.node._detect_primary_language(temp_path)
            assert language == "Unknown"

    def test_calculate_folder_size(self):
        """测试文件夹大小计算"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 创建测试文件
            (temp_path / "file1.txt").write_text("hello world")  # 11 bytes
            (temp_path / "file2.txt").write_text("test")         # 4 bytes

            size = self.node._calculate_folder_size(temp_path)
            assert size == 15  # 11 + 4 bytes

    def test_full_workflow(self):
        """测试完整工作流程"""
        if not Path(self.test_repo_path).exists():
            pytest.skip(f"测试目录不存在: {self.test_repo_path}")

        shared = {"local_folder_path": self.test_repo_path}

        # 执行完整流程
        prep_result = self.node.prep(shared)
        exec_result = self.node.exec(prep_result)
        post_result = self.node.post(shared, prep_result, exec_result)

        # 验证结果
        assert post_result == "default"
        assert shared["local_path"] == Path(self.test_repo_path)
        assert shared["current_stage"] == "local_folder_processing"

        # 验证 repo_info
        repo_info = shared["repo_info"]
        assert repo_info["name"] == "GTPlanner"
        assert repo_info["source"] == "local_folder"
        assert isinstance(repo_info["size"], int)
        assert repo_info["size"] >= 0


def test_real_repository():
    """测试真实仓库 - GTPlanner"""
    # 使用项目根目录的相对路径
    project_root = Path(__file__).parent.parent
    test_repo_path = str(project_root / "data" / "repos" / "GTPlanner")

    if not Path(test_repo_path).exists():
        pytest.skip(f"测试目录不存在: {test_repo_path}")

    node = LocalFolderNode()
    shared = {"local_folder_path": test_repo_path}

    print(f"\n🧪 测试真实仓库: {test_repo_path}")

    try:
        # 执行完整流程
        prep_result = node.prep(shared)
        print(f"✅ prep 阶段完成: {prep_result}")

        exec_result = node.exec(prep_result)
        print(f"✅ exec 阶段完成: {exec_result}")

        post_result = node.post(shared, prep_result, exec_result)
        print(f"✅ post 阶段完成: {post_result}")

        # 打印详细信息
        repo_info = shared["repo_info"]
        print(f"\n📊 仓库信息:")
        print(f"  名称: {repo_info['name']}")
        print(f"  完整名称: {repo_info['full_name']}")
        print(f"  主要语言: {repo_info['language']}")
        print(f"  大小: {repo_info['size']:,} bytes")
        print(f"  路径: {repo_info['html_url']}")

        print(f"\n✅ LocalFolderNode 测试成功!")

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    # 直接运行测试
    test_real_repository()