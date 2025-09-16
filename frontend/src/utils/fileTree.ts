// 文件树节点接口
export interface FileNode {
  name: string;
  type: "file" | "folder";
  path: string;
  children?: FileNode[];
  size?: number;
  extension?: string;
}

// 文件信息接口（来自API）
export interface FileInfo {
  id: number;
  task_id: number;
  file_path: string;
  file_type: string;
  file_size: number;
  analysis_status: string;
  created_at: string;
}

/**
 * 将文件路径列表转换为树形结构
 * @param files 文件信息列表
 * @returns 文件树根节点
 */
export function buildFileTree(files: FileInfo[]): FileNode {
  // 输入验证
  if (!files || !Array.isArray(files)) {
    console.error("buildFileTree: Invalid files input:", files);
    return {
      name: "root",
      type: "folder",
      path: "",
      children: [],
    };
  }

  const root: FileNode = {
    name: "root",
    type: "folder",
    path: "",
    children: [],
  };

  if (files.length === 0) {
    console.warn("buildFileTree: No files to process");
    return root;
  }

  // 按路径排序，确保文件夹在文件前面
  const sortedFiles = files.sort((a, b) => {
    if (!a.file_path || !b.file_path) {
      console.warn("buildFileTree: File with missing file_path:", a, b);
      return 0;
    }

    // 处理Windows和Unix路径分隔符
    const aPath = a.file_path.replace(/\\/g, "/");
    const bPath = b.file_path.replace(/\\/g, "/");

    const aIsFolder = aPath.includes("/");
    const bIsFolder = bPath.includes("/");

    if (aIsFolder && !bIsFolder) return -1;
    if (!aIsFolder && bIsFolder) return 1;
    return aPath.localeCompare(bPath);
  });

  console.log("buildFileTree: Processing", sortedFiles.length, "files");

  for (const file of sortedFiles) {
    try {
      insertFileIntoTree(root, file);
    } catch (error) {
      console.error("buildFileTree: Error processing file:", file, error);
    }
  }

  return root;
}

/**
 * 将单个文件插入到文件树中
 * @param root 根节点
 * @param file 文件信息
 */
function insertFileIntoTree(root: FileNode, file: FileInfo): void {
  if (!file || !file.file_path) {
    console.error("insertFileIntoTree: Invalid file:", file);
    return;
  }

  // 处理Windows和Unix路径分隔符
  const normalizedPath = file.file_path.replace(/\\/g, "/");
  const pathParts = normalizedPath.split("/").filter((part) => part.length > 0);

  if (pathParts.length === 0) {
    console.warn("insertFileIntoTree: Empty path parts for file:", file);
    return;
  }

  let currentNode = root;

  // 遍历路径的每一部分
  for (let i = 0; i < pathParts.length; i++) {
    const part = pathParts[i];
    const isLastPart = i === pathParts.length - 1;
    const currentPath = pathParts.slice(0, i + 1).join("/");

    // 查找是否已存在该节点
    let existingNode = currentNode.children?.find(
      (child) => child.name === part
    );

    if (!existingNode) {
      // 创建新节点
      const newNode: FileNode = {
        name: part,
        type: isLastPart ? "file" : "folder",
        path: currentPath,
        children: isLastPart ? undefined : [],
      };

      // 如果是文件，添加额外信息
      if (isLastPart) {
        newNode.size = file.file_size || 0;
        newNode.extension = getFileExtension(part);
      }

      // 确保父节点有children数组
      if (!currentNode.children) {
        currentNode.children = [];
      }

      currentNode.children.push(newNode);
      existingNode = newNode;
    }

    currentNode = existingNode;
  }
}

/**
 * 获取文件扩展名
 * @param filename 文件名
 * @returns 扩展名（不包含点）
 */
function getFileExtension(filename: string): string {
  const lastDotIndex = filename.lastIndexOf(".");
  return lastDotIndex > 0
    ? filename.substring(lastDotIndex + 1).toLowerCase()
    : "";
}

/**
 * 根据文件扩展名获取文件类型
 * @param extension 文件扩展名
 * @returns 文件类型描述
 */
export function getFileType(extension: string): string {
  const typeMap: Record<string, string> = {
    // 编程语言
    js: "JavaScript",
    ts: "TypeScript",
    jsx: "React JSX",
    tsx: "React TSX",
    py: "Python",
    java: "Java",
    cpp: "C++",
    c: "C",
    cs: "C#",
    php: "PHP",
    rb: "Ruby",
    go: "Go",
    rs: "Rust",
    swift: "Swift",
    kt: "Kotlin",

    // 标记语言
    html: "HTML",
    htm: "HTML",
    xml: "XML",
    md: "Markdown",
    rst: "reStructuredText",

    // 样式表
    css: "CSS",
    scss: "SCSS",
    sass: "Sass",
    less: "Less",

    // 配置文件
    json: "JSON",
    yaml: "YAML",
    yml: "YAML",
    toml: "TOML",
    ini: "INI",
    cfg: "Config",
    conf: "Config",

    // 文档
    txt: "Text",
    pdf: "PDF",
    doc: "Word",
    docx: "Word",

    // 其他
    sql: "SQL",
    sh: "Shell Script",
    bat: "Batch File",
    ps1: "PowerShell",
  };

  return typeMap[extension] || "Unknown";
}

/**
 * 排序文件树节点（文件夹在前，文件在后，按名称排序）
 * @param node 要排序的节点
 */
export function sortFileTree(node: FileNode): void {
  if (!node.children) return;

  // 递归排序子节点
  node.children.forEach(sortFileTree);

  // 排序当前节点的子节点
  node.children.sort((a, b) => {
    // 文件夹优先
    if (a.type === "folder" && b.type === "file") return -1;
    if (a.type === "file" && b.type === "folder") return 1;

    // 同类型按名称排序
    return a.name.localeCompare(b.name);
  });
}

/**
 * 标准化文件路径：URL解码 + 路径分隔符标准化
 * @param path 原始文件路径
 * @returns 标准化后的路径
 */
export function normalizePath(path: string): string {
  if (!path) return "";

  try {
    // 先进行URL解码，处理 %5C 等编码字符
    const decodedPath = decodeURIComponent(path);
    // 统一使用正斜杠，移除开头的斜杠
    return decodedPath.replace(/\\/g, "/").replace(/^\/+/, "");
  } catch (error) {
    // 如果URL解码失败，使用原始路径进行标准化
    console.warn("Failed to decode URL:", path, error);
    return path.replace(/\\/g, "/").replace(/^\/+/, "");
  }
}

/**
 * 在文件树中查找指定路径的文件是否存在
 * @param fileTree 文件树根节点
 * @param targetPath 目标文件路径（相对于项目根目录）
 * @returns 是否找到该文件
 */
export function findFileInTree(
  fileTree: FileNode | null,
  targetPath: string
): boolean {
  if (!fileTree || !targetPath) return false;

  // 标准化路径
  const normalizedPath = normalizePath(targetPath);

  // 判断是否只是文件名（不包含路径分隔符）
  const isFileNameOnly = !normalizedPath.includes("/");

  // 递归搜索函数
  function searchNode(node: FileNode): boolean {
    // 标准化当前节点路径
    const nodePath = node.path.replace(/\\/g, "/").replace(/^\/+/, "");

    if (node.type === "file") {
      if (isFileNameOnly) {
        // 如果只是文件名，检查文件名是否匹配
        return node.name === normalizedPath;
      } else {
        // 如果是完整路径，检查完整路径是否匹配
        return nodePath === normalizedPath;
      }
    }

    // 如果是文件夹，递归搜索子节点
    if (node.children) {
      return node.children.some((child) => searchNode(child));
    }

    return false;
  }

  // 从根节点开始搜索
  if (fileTree.children) {
    return fileTree.children.some((child) => searchNode(child));
  }

  return false;
}

/**
 * 获取到达指定文件路径需要展开的所有文件夹路径
 * @param fileTree 文件树根节点
 * @param targetPath 目标文件路径
 * @returns 需要展开的文件夹路径数组
 */
export function getPathsToExpand(
  fileTree: FileNode | null,
  targetPath: string
): string[] {
  if (!fileTree || !targetPath) return [];

  const normalizedPath = normalizePath(targetPath);
  const pathsToExpand: string[] = [];

  // 判断是否只是文件名（不包含路径分隔符）
  const isFileNameOnly = !normalizedPath.includes("/");

  function searchNode(node: FileNode, currentPath: string[] = []): boolean {
    const nodePath = node.path.replace(/\\/g, "/").replace(/^\/+/, "");

    // 如果找到目标文件
    if (node.type === "file") {
      let isMatch = false;
      if (isFileNameOnly) {
        // 如果只是文件名，检查文件名是否匹配
        isMatch = node.name === normalizedPath;
      } else {
        // 如果是完整路径，检查完整路径是否匹配
        isMatch = nodePath === normalizedPath;
      }

      if (isMatch) {
        // 添加所有父文件夹路径到展开列表
        pathsToExpand.push(...currentPath);
        return true;
      }
    }

    // 如果是文件夹，递归搜索
    if (node.type === "folder" && node.children) {
      const newPath = [...currentPath, node.path];
      if (node.children.some((child) => searchNode(child, newPath))) {
        return true;
      }
    }

    return false;
  }

  if (fileTree.children) {
    fileTree.children.some((child) => searchNode(child));
  }

  return pathsToExpand;
}

/**
 * 调试工具：打印文件树结构
 * @param fileTree 文件树根节点
 * @param indent 缩进级别
 */
export function debugPrintFileTree(
  fileTree: FileNode | null,
  indent: number = 0
): void {
  if (!fileTree) {
    console.log("File tree is null");
    return;
  }

  const indentStr = "  ".repeat(indent);
  const icon = fileTree.type === "folder" ? "📁" : "📄";
  console.log(
    `${indentStr}${icon} ${fileTree.name} (path: "${fileTree.path}")`
  );

  if (fileTree.children) {
    fileTree.children.forEach((child) => {
      debugPrintFileTree(child, indent + 1);
    });
  }
}

/**
 * 调试工具：查找所有匹配指定文件名的文件
 * @param fileTree 文件树根节点
 * @param fileName 要查找的文件名
 * @returns 匹配的文件节点数组
 */
export function findAllFilesByName(
  fileTree: FileNode | null,
  fileName: string
): FileNode[] {
  if (!fileTree || !fileName) return [];

  const matches: FileNode[] = [];

  function searchNode(node: FileNode): void {
    if (node.type === "file" && node.name === fileName) {
      matches.push(node);
    }

    if (node.children) {
      node.children.forEach((child) => searchNode(child));
    }
  }

  if (fileTree.children) {
    fileTree.children.forEach((child) => searchNode(child));
  }

  return matches;
}

/**
 * 根据文件名或路径查找文件的完整路径
 * @param fileTree 文件树根节点
 * @param targetPath 目标文件路径或文件名
 * @returns 找到的文件的完整路径，如果没找到返回null
 */
export function findFileFullPath(
  fileTree: FileNode | null,
  targetPath: string
): string | null {
  if (!fileTree || !targetPath) return null;

  const normalizedPath = normalizePath(targetPath);
  const isFileNameOnly = !normalizedPath.includes("/");

  function searchNode(node: FileNode): string | null {
    const nodePath = node.path.replace(/\\/g, "/").replace(/^\/+/, "");

    if (node.type === "file") {
      if (isFileNameOnly) {
        // 如果只是文件名，检查文件名是否匹配，返回完整路径
        if (node.name === normalizedPath) {
          return nodePath;
        }
      } else {
        // 如果是完整路径，检查完整路径是否匹配
        if (nodePath === normalizedPath) {
          return nodePath;
        }
      }
    }

    // 递归搜索子节点
    if (node.children) {
      for (const child of node.children) {
        const result = searchNode(child);
        if (result) return result;
      }
    }

    return null;
  }

  // 从根节点开始搜索
  if (fileTree.children) {
    for (const child of fileTree.children) {
      const result = searchNode(child);
      if (result) return result;
    }
  }

  return null;
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";

  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}
