"""
统一的文件过滤器
用于后端的文件过滤逻辑，与前端保持一致
"""

import os
import re
from pathlib import Path
from typing import Set, List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 默认忽略的目录
DEFAULT_IGNORE_DIRS = {
    # 版本控制
    ".git", ".svn", ".hg",
    
    # Python
    "__pycache__", ".pytest_cache", ".mypy_cache", ".dmypy.json", ".pyre",
    ".venv", "venv", "env", ".env", ".tox", ".nox", ".eggs", "*.egg-info",
    ".installed.cfg", "htmlcov", ".hypothesis", ".coverage",
    
    # Node.js
    "node_modules", ".npm", ".yarn", "bower_components", "jspm_packages",
    ".rpt2_cache", ".rts2_cache_cjs", ".rts2_cache_es", ".rts2_cache_umd",
    ".nyc_output",
    
    # 构建输出
    "dist", "build", "out", "target", "bin", "obj",
    
    # 框架特定
    ".next", ".nuxt", ".vuepress", ".docusaurus", ".parcel-cache", ".cache",
    
    # IDE和编辑器
    ".vscode", ".idea", ".vs", ".eclipse", ".settings",
    
    # 临时文件
    "tmp", "temp", "logs", ".ipynb_checkpoints",
    
    # 其他
    "coverage", ".sass-cache", ".gradle", ".m2",
}

# 默认忽略的文件
DEFAULT_IGNORE_FILES = {
    # 环境配置
    ".env", ".env.example", ".env.local", ".env.development", ".env.test",
    ".env.production", ".env.staging",
    
    # 锁文件
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Pipfile.lock",
    "poetry.lock", "uv.lock", "Cargo.lock", "composer.lock", "Gemfile.lock",
    
    # 版本控制
    ".gitignore", ".gitattributes", ".gitmodules", ".svnignore",
    
    # 系统文件
    ".DS_Store", ".DS_Store?", "._*", ".Spotlight-V100", ".Trashes",
    "ehthumbs.db", "Thumbs.db", "desktop.ini",
    
    # 日志文件
    "npm-debug.log", "yarn-debug.log", "yarn-error.log", "lerna-debug.log",
    "debug.log", "error.log", "access.log",
    
    # 缓存和临时文件
    ".eslintcache", ".tsbuildinfo", ".coverage", "coverage.xml", "nosetests.xml",
    ".manifest", ".spec", "pip-log.txt", "pip-delete-this-directory.txt",
    ".yarn-integrity",
    
    # 文档和配置
    "LICENSE", "CHANGELOG.md", "CHANGELOG.txt", "HISTORY.md", "HISTORY.txt",
    "AUTHORS", "CONTRIBUTORS", "MAINTAINERS",
}

# 默认忽略的文件扩展名
DEFAULT_IGNORE_EXTENSIONS = {
    # 图片
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".webp", ".tiff", ".tif",
    
    # 音频
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
    
    # 视频
    ".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm", ".m4v",
    
    # 压缩包
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tar.gz", ".tar.bz2",
    
    # 办公文档
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp",
    
    # 字体
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    
    # 二进制
    ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
    
    # 编译产物
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe", ".o", ".obj", ".class",
    
    # 临时文件
    ".tmp", ".temp", ".bak", ".backup", ".swp", ".swo", ".log", ".cache",
}

# 支持的代码文件扩展名
SUPPORTED_CODE_EXTENSIONS = {
    # 主流编程语言
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp",
    ".cs", ".go", ".rs", ".php", ".rb", ".swift", ".kt", ".scala", ".r",
    ".m", ".mm", ".pl", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
    
    # 配置和标记语言
    ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".properties", ".env", ".dockerfile",
    
    # 文档
    ".md", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc",
    
    # Web相关
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte",
    
    # 数据库
    ".sql", ".graphql", ".gql",
    
    # 其他
    ".ipynb", ".proto", ".thrift", ".avro",
}


class FileFilter:
    """统一的文件过滤器"""
    
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path
        self.gitignore_rules = []
        if repo_path:
            self._load_gitignore()
    
    def _load_gitignore(self):
        """加载.gitignore文件"""
        if not self.repo_path:
            return
            
        gitignore_path = self.repo_path / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._parse_gitignore(content)
                logger.info(f"Loaded .gitignore with {len(self.gitignore_rules)} rules")
            except Exception as e:
                logger.warning(f"Failed to load .gitignore: {e}")
    
    def _parse_gitignore(self, content: str):
        """解析.gitignore内容"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            self.gitignore_rules.append(line)
    
    def should_ignore_file(self, file_path: Path) -> bool:
        """检查文件是否应该被忽略"""
        file_name = file_path.name
        file_path_str = str(file_path).replace('\\', '/')
        
        # 检查默认忽略文件
        if file_name in DEFAULT_IGNORE_FILES:
            return True
        
        # 检查文件扩展名
        suffix = file_path.suffix.lower()
        if suffix in DEFAULT_IGNORE_EXTENSIONS:
            return True
        
        # 检查路径中是否包含忽略的目录
        path_parts = file_path_str.split('/')
        for part in path_parts:
            if part in DEFAULT_IGNORE_DIRS:
                return True
        
        # 检查隐藏文件
        if file_name.startswith('.') and file_name != '.gitignore':
            return True
        
        # 检查.gitignore规则
        if self._matches_gitignore(file_path_str):
            return True
        
        return False
    
    def should_ignore_directory(self, dir_path: Path) -> bool:
        """检查目录是否应该被忽略"""
        dir_name = dir_path.name
        dir_path_str = str(dir_path).replace('\\', '/')
        
        # 检查默认忽略目录
        if dir_name in DEFAULT_IGNORE_DIRS:
            return True
        
        # 检查路径中是否包含忽略的目录
        path_parts = dir_path_str.split('/')
        for part in path_parts:
            if part in DEFAULT_IGNORE_DIRS:
                return True
        
        # 检查隐藏目录
        if dir_name.startswith('.') and dir_name != '.github':
            return True
        
        # 检查.gitignore规则
        if self._matches_gitignore(dir_path_str + '/'):
            return True
        
        return False
    
    def _matches_gitignore(self, path: str) -> bool:
        """检查路径是否匹配.gitignore规则"""
        ignored = False

        for rule in self.gitignore_rules:
            if rule.startswith('!'):
                # 否定规则
                negation_rule = rule[1:]
                if self._match_pattern(path, negation_rule):
                    ignored = False  # 否定规则，不忽略
            else:
                # 普通规则
                if self._match_pattern(path, rule):
                    ignored = True  # 普通规则，忽略

        return ignored

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """检查路径是否匹配模式"""
        # 转换为正则表达式
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')

        # 处理目录模式
        if pattern.endswith('/'):
            regex_pattern = regex_pattern[:-1] + '($|/)'

        # 处理开头的斜杠
        if pattern.startswith('/'):
            regex_pattern = '^' + regex_pattern[1:]
        else:
            # 可以匹配路径中的任何部分
            regex_pattern = '(^|/)' + regex_pattern

        try:
            return bool(re.search(regex_pattern, path))
        except re.error:
            return False
    
    def scan_directory(self, directory: Path, extensions: Optional[Set[str]] = None) -> List[Path]:
        """扫描目录并返回过滤后的文件列表"""
        if not directory.exists():
            return []
        
        files = []
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # 检查是否应该忽略
                if self.should_ignore_file(file_path):
                    continue
                
                # 检查扩展名
                if extensions and file_path.suffix.lower() not in extensions:
                    continue
                
                files.append(file_path)
        
        return files
    
    def filter_files(self, file_paths: List[Path], extensions: Optional[Set[str]] = None) -> List[Path]:
        """过滤文件列表"""
        filtered = []
        for file_path in file_paths:
            if self.should_ignore_file(file_path):
                continue
            
            if extensions and file_path.suffix.lower() not in extensions:
                continue
            
            filtered.append(file_path)
        
        return filtered
    
    def is_supported_code_file(self, file_path: Path) -> bool:
        """检查是否是支持的代码文件"""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        return suffix in SUPPORTED_CODE_EXTENSIONS or name in {"dockerfile", "makefile"}
