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
