/**
 * 统一的文件过滤配置
 * 用于前端和后端的文件过滤逻辑
 */

// 默认忽略的目录
export const DEFAULT_IGNORE_DIRS = new Set([
  // 版本控制
  ".git",
  ".svn",
  ".hg",
  
  // Python
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  ".dmypy.json",
  ".pyre",
  ".venv",
  "venv",
  "env",
  ".env",
  ".tox",
  ".nox",
  ".eggs",
  "*.egg-info",
  ".installed.cfg",
  "htmlcov",
  ".hypothesis",
  ".coverage",
  
  // Node.js
  "node_modules",
  ".npm",
  ".yarn",
  "bower_components",
  "jspm_packages",
  ".rpt2_cache",
  ".rts2_cache_cjs",
  ".rts2_cache_es",
  ".rts2_cache_umd",
  ".nyc_output",
  
  // 构建输出
  "dist",
  "build",
  "out",
  "target", // Rust/Java
  "bin",
  "obj",
  
  // 框架特定
  ".next",
  ".nuxt",
  ".vuepress",
  ".docusaurus",
  ".parcel-cache",
  ".cache",
  
  // IDE和编辑器
  ".vscode",
  ".idea",
  ".vs",
  ".eclipse",
  ".settings",
  
  // 临时文件
  "tmp",
  "temp",
  "logs",
  ".ipynb_checkpoints",
  
  // 其他
  "coverage",
  ".sass-cache",
  ".gradle",
  ".m2",
]);

// 默认忽略的文件
export const DEFAULT_IGNORE_FILES = new Set([
  // 环境配置
  ".env",
  ".env.example",
  ".env.local",
  ".env.development",
  ".env.test",
  ".env.production",
  ".env.staging",
  
  // 锁文件
  "package-lock.json",
  "yarn.lock",
  "pnpm-lock.yaml",
  "Pipfile.lock",
  "poetry.lock",
  "uv.lock", // 新增 uv.lock
  "Cargo.lock",
  "composer.lock",
  "Gemfile.lock",
  
  // 版本控制
  ".gitignore",
  ".gitattributes",
  ".gitmodules",
  ".svnignore",
  
  // 系统文件
  ".DS_Store",
  ".DS_Store?",
  "._*",
  ".Spotlight-V100",
  ".Trashes",
  "ehthumbs.db",
  "Thumbs.db",
  "desktop.ini",
  
  // 日志文件
  "npm-debug.log",
  "yarn-debug.log",
  "yarn-error.log",
  "lerna-debug.log",
  "debug.log",
  "error.log",
  "access.log",
  
  // 缓存和临时文件
  ".eslintcache",
  ".tsbuildinfo",
  ".coverage",
  "coverage.xml",
  "nosetests.xml",
  ".manifest",
  ".spec",
  "pip-log.txt",
  "pip-delete-this-directory.txt",
  ".yarn-integrity",
  
  // 编译产物
  "*.pyc",
  "*.pyo",
  "*.pyd",
  "*.so",
  "*.dll",
  "*.dylib",
  "*.exe",
  "*.o",
  "*.obj",
  "*.class",
  
  // 文档和配置
  "LICENSE",
  "CHANGELOG.md",
  "CHANGELOG.txt",
  "HISTORY.md",
  "HISTORY.txt",
  "AUTHORS",
  "CONTRIBUTORS",
  "MAINTAINERS",
]);

// 默认忽略的文件扩展名
export const DEFAULT_IGNORE_EXTENSIONS = new Set([
  // 图片
  ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".webp", ".tiff", ".tif",
  
  // 音频
  ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
  
  // 视频
  ".mp4", ".avi", ".mov", ".wmv", ".flv", ".mkv", ".webm", ".m4v",
  
  // 压缩包
  ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tar.gz", ".tar.bz2",
  
  // 办公文档
  ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp",
  
  // 字体
  ".woff", ".woff2", ".ttf", ".eot", ".otf",
  
  // 二进制
  ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
  
  // 临时文件
  ".tmp", ".temp", ".bak", ".backup", ".swp", ".swo", ".log", ".cache",
]);

// 支持的代码文件扩展名
export const SUPPORTED_CODE_EXTENSIONS = new Set([
  // 主流编程语言
  ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp",
  ".cs", ".go", ".rs", ".php", ".rb", ".swift", ".kt", ".scala", ".r",
  ".m", ".mm", ".pl", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd",
  
  // 配置和标记语言
  ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
  ".properties", ".env", ".dockerfile", "Dockerfile",
  
  // 文档
  ".md", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc",
  
  // Web相关
  ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte",
  
  // 数据库
  ".sql", ".graphql", ".gql",
  
  // 其他
  // ".ipynb", ".proto", ".thrift", ".avro",
]);

/**
 * 检查文件是否应该被忽略
 */
export function shouldIgnoreFile(fileName: string, filePath: string): boolean {
  // 检查文件名
  if (DEFAULT_IGNORE_FILES.has(fileName)) {
    return true;
  }
  
  // 检查文件扩展名
  const extension = fileName.toLowerCase().split('.').pop();
  if (extension && DEFAULT_IGNORE_EXTENSIONS.has(`.${extension}`)) {
    return true;
  }
  
  // 检查路径中是否包含忽略的目录
  const pathParts = filePath.split('/');
  for (const part of pathParts) {
    if (DEFAULT_IGNORE_DIRS.has(part)) {
      return true;
    }
  }
  
  // 检查特殊模式
  if (fileName.startsWith('.') && fileName !== '.gitignore') {
    // 大多数隐藏文件都应该忽略，除了.gitignore
    return true;
  }
  
  return false;
}

/**
 * 检查目录是否应该被忽略
 */
export function shouldIgnoreDirectory(dirName: string, dirPath: string): boolean {
  // 检查目录名
  if (DEFAULT_IGNORE_DIRS.has(dirName)) {
    return true;
  }
  
  // 检查路径中是否包含忽略的目录
  const pathParts = dirPath.split('/');
  for (const part of pathParts) {
    if (DEFAULT_IGNORE_DIRS.has(part)) {
      return true;
    }
  }
  
  // 检查隐藏目录
  if (dirName.startsWith('.') && dirName !== '.github') {
    // 大多数隐藏目录都应该忽略，除了.github
    return true;
  }
  
  return false;
}

/**
 * 检查文件是否是支持的代码文件
 */
export function isSupportedCodeFile(fileName: string): boolean {
  const extension = fileName.toLowerCase().split('.').pop();
  if (!extension) return false;
  
  return SUPPORTED_CODE_EXTENSIONS.has(`.${extension}`) || 
         SUPPORTED_CODE_EXTENSIONS.has(fileName.toLowerCase());
}
