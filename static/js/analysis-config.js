/**
 * 分析配置页面的JavaScript逻辑
 */

class AnalysisConfig {
  constructor() {
    this.fileTree = null;
    this.selectedFiles = new Set();
    this.lastClickedNode = null;
    this.analysisMode = "overall";

    this.init();
  }

  init() {
    this.bindEvents();
    this.loadFileData();
  }

  bindEvents() {
    // 返回按钮
    document.getElementById("backBtn").addEventListener("click", () => {
      window.location.href = "/";
    });

    // 全选/取消全选
    document
      .getElementById("toggleSelectAllBtn")
      .addEventListener("click", () => {
        this.toggleSelectAll();
      });

    // 开始分析
    document
      .getElementById("startAnalysisBtn")
      .addEventListener("click", () => {
        this.startAnalysis();
      });

    // 分析模式切换
    document.querySelectorAll('input[name="analysisMode"]').forEach((radio) => {
      radio.addEventListener("change", (e) => {
        this.analysisMode = e.target.value;
      });
    });
  }

  loadFileData() {
    // 从sessionStorage获取文件数据
    const fileData = sessionStorage.getItem("selectedFiles");
    if (!fileData) {
      // 如果没有数据，使用示例数据进行演示
      const sampleFiles = [
        { path: "src/main.js", size: 2048, name: "main.js" },
        { path: "src/components/Header.vue", size: 1536, name: "Header.vue" },
        { path: "src/components/Footer.vue", size: 1024, name: "Footer.vue" },
        { path: "src/utils/helpers.js", size: 3072, name: "helpers.js" },
        { path: "package.json", size: 512, name: "package.json" },
        { path: "README.md", size: 1024, name: "README.md" },
        { path: "docs/api.md", size: 2048, name: "api.md" },
        {
          path: "config/webpack.config.js",
          size: 4096,
          name: "webpack.config.js",
        },
        { path: "styles/main.css", size: 1536, name: "main.css" },
        { path: "tests/unit.test.js", size: 2048, name: "unit.test.js" },
      ];
      this.buildFileTree(sampleFiles);
      return;
    }

    try {
      const files = JSON.parse(fileData);
      this.buildFileTree(files);
    } catch (error) {
      console.error("解析文件数据失败:", error);
      alert("文件数据格式错误，请重新选择文件");
      window.location.href = "/";
    }
  }

  buildFileTree(files) {
    document.getElementById("loadingOverlay").classList.remove("hidden");

    // 使用setTimeout让UI有时间显示loading
    setTimeout(() => {
      try {
        this.fileTree = this.createFileTreeStructure(files);
        this.renderFileTree();
        this.updateStats();
        document.getElementById("loadingOverlay").classList.add("hidden");
      } catch (error) {
        console.error("构建文件树失败:", error);
        document.getElementById("loadingOverlay").classList.add("hidden");
        alert("构建文件树失败，请重新选择文件");
      }
    }, 100);
  }

  createFileTreeStructure(files) {
    const root = {
      name: "root",
      path: "",
      type: "folder",
      selected: true,
      expanded: true,
      children: [],
    };

    const folderMap = new Map();
    folderMap.set("", root);

    // 处理每个文件
    files.forEach((file) => {
      const pathParts = file.path.split("/");
      const fileName = pathParts[pathParts.length - 1];
      const extension = fileName.includes(".")
        ? fileName.split(".").pop().toLowerCase()
        : "";

      // 创建所有父文件夹
      let currentPath = "";
      for (let i = 0; i < pathParts.length - 1; i++) {
        const folderName = pathParts[i];
        const parentPath = currentPath;
        currentPath = currentPath ? `${currentPath}/${folderName}` : folderName;

        if (!folderMap.has(currentPath)) {
          const folderNode = {
            name: folderName,
            path: currentPath,
            type: "folder",
            selected: true,
            expanded: true,
            children: [],
          };

          folderMap.set(currentPath, folderNode);
          const parent = folderMap.get(parentPath);
          if (parent) {
            parent.children.push(folderNode);
          }
        }
      }

      // 创建文件节点
      const fileNode = {
        name: fileName,
        path: file.path,
        type: "file",
        size: file.size || 0,
        extension,
        selected: true,
      };

      // 添加到父文件夹
      const parentPath = pathParts.slice(0, -1).join("/");
      const parent = folderMap.get(parentPath);
      if (parent) {
        parent.children.push(fileNode);
      }

      // 添加到选中文件集合
      this.selectedFiles.add(file.path);
    });

    // 排序所有文件夹的children
    this.sortTreeChildren(root);
    return root;
  }

  sortTreeChildren(node) {
    if (node.children) {
      node.children.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === "folder" ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
      node.children.forEach((child) => this.sortTreeChildren(child));
    }
  }

  renderFileTree() {
    const container = document.getElementById("fileTree");
    container.innerHTML = "";

    if (this.fileTree.children) {
      this.fileTree.children.forEach((child) => {
        container.appendChild(this.createNodeElement(child, 0));
      });
    }
  }

  createNodeElement(node, depth) {
    const div = document.createElement("div");
    div.className = "select-none";

    const nodeDiv = document.createElement("div");
    nodeDiv.className = `flex items-center space-x-3 p-2 rounded-md hover:bg-accent cursor-pointer transition-colors ${
      node.selected ? "bg-accent" : ""
    }`;
    nodeDiv.style.paddingLeft = `${depth * 20 + 12}px`;

    // 展开/折叠按钮
    if (node.type === "folder" && node.children && node.children.length > 0) {
      const expandBtn = document.createElement("button");
      expandBtn.className = "p-1 hover:bg-gray-200 rounded";
      expandBtn.innerHTML = node.expanded
        ? '<i data-lucide="chevron-down" class="h-3 w-3 text-gray-500"></i>'
        : '<i data-lucide="chevron-right" class="h-3 w-3 text-gray-500"></i>';

      expandBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        this.toggleNodeExpansion(node);
      });

      nodeDiv.appendChild(expandBtn);
    } else {
      // 占位空间
      const spacer = document.createElement("div");
      spacer.className = "w-5 h-5";
      nodeDiv.appendChild(spacer);
    }

    // 主要内容区域
    const contentDiv = document.createElement("div");
    contentDiv.className = "flex items-center space-x-3 flex-1 min-w-0";

    // 复选框
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = node.selected;
    checkbox.className =
      "w-4 h-4 rounded border-border text-primary focus:ring-primary focus:ring-2";

    checkbox.addEventListener("change", (e) => {
      e.stopPropagation();
      this.toggleNodeSelection(node, e.shiftKey);
    });

    contentDiv.appendChild(checkbox);

    // 图标和名称
    const iconNameDiv = document.createElement("div");
    iconNameDiv.className = "flex items-center space-x-3 flex-1 min-w-0";

    // 图标
    const iconDiv = document.createElement("div");
    iconDiv.className = "flex-shrink-0";
    iconDiv.innerHTML = this.getNodeIcon(node);
    iconNameDiv.appendChild(iconDiv);

    // 名称和信息
    const nameDiv = document.createElement("div");
    nameDiv.className = "flex-1 min-w-0";

    const nameP = document.createElement("p");
    nameP.className = "text-sm font-medium text-foreground truncate";
    nameP.textContent = node.name;
    nameDiv.appendChild(nameP);

    if (node.type === "file") {
      const sizeP = document.createElement("p");
      sizeP.className = "text-xs text-muted-foreground";
      sizeP.textContent = this.formatFileSize(node.size);
      nameDiv.appendChild(sizeP);
    }

    iconNameDiv.appendChild(nameDiv);
    contentDiv.appendChild(iconNameDiv);

    // 选中状态图标
    if (node.selected) {
      const checkIcon = document.createElement("i");
      checkIcon.setAttribute("data-lucide", "check-circle-2");
      checkIcon.className = "h-4 w-4 text-primary flex-shrink-0";
      contentDiv.appendChild(checkIcon);
    }

    nodeDiv.appendChild(contentDiv);
    div.appendChild(nodeDiv);

    // 子节点
    if (node.type === "folder" && node.expanded && node.children) {
      const childrenDiv = document.createElement("div");
      node.children.forEach((child) => {
        childrenDiv.appendChild(this.createNodeElement(child, depth + 1));
      });
      div.appendChild(childrenDiv);
    }

    return div;
  }

  getNodeIcon(node) {
    if (node.type === "folder") {
      return node.expanded
        ? '<i data-lucide="folder-open" class="h-4 w-4 text-chart-1"></i>'
        : '<i data-lucide="folder" class="h-4 w-4 text-chart-1"></i>';
    }

    // 根据文件扩展名返回不同图标
    const ext = node.extension;
    if (
      [
        "js",
        "ts",
        "jsx",
        "tsx",
        "py",
        "java",
        "cpp",
        "c",
        "go",
        "rs",
        "php",
        "rb",
        "cs",
        "swift",
        "kt",
      ].includes(ext)
    ) {
      return '<i data-lucide="file-code" class="h-4 w-4 text-chart-1"></i>';
    }
    if (["html", "htm", "vue"].includes(ext)) {
      return '<i data-lucide="globe" class="h-4 w-4 text-chart-4"></i>';
    }
    if (["css", "scss", "sass", "less"].includes(ext)) {
      return '<i data-lucide="palette" class="h-4 w-4 text-chart-5"></i>';
    }
    if (["json", "yml", "yaml", "xml", "ini", "conf", "config"].includes(ext)) {
      return '<i data-lucide="file-text" class="h-4 w-4 text-chart-2"></i>';
    }
    if (["md", "txt", "rst"].includes(ext)) {
      return '<i data-lucide="file-text" class="h-4 w-4 text-chart-3"></i>';
    }

    return '<i data-lucide="file" class="h-4 w-4 text-muted-foreground"></i>';
  }

  formatFileSize(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  toggleNodeExpansion(node) {
    node.expanded = !node.expanded;
    this.renderFileTree();
    // 重新初始化图标
    lucide.createIcons();
  }

  toggleNodeSelection(node, isShiftClick = false) {
    if (node.type === "file") {
      if (node.selected) {
        this.selectedFiles.delete(node.path);
      } else {
        this.selectedFiles.add(node.path);
      }
      node.selected = !node.selected;
    } else {
      // 文件夹选择：切换所有子文件
      this.toggleFolderSelection(node, !node.selected);
    }

    this.updateFolderStates(this.fileTree);
    this.renderFileTree();
    this.updateStats();
    lucide.createIcons();
  }

  toggleFolderSelection(node, selected) {
    if (node.type === "file") {
      if (selected) {
        this.selectedFiles.add(node.path);
      } else {
        this.selectedFiles.delete(node.path);
      }
      node.selected = selected;
    } else if (node.children) {
      node.children.forEach((child) => {
        this.toggleFolderSelection(child, selected);
      });
    }
  }

  updateFolderStates(node) {
    if (node.type === "folder" && node.children) {
      const childStates = node.children.map((child) => {
        this.updateFolderStates(child);
        return child.selected;
      });

      const allSelected = childStates.every((state) => state);
      const noneSelected = childStates.every((state) => !state);

      if (allSelected) {
        node.selected = true;
      } else if (noneSelected) {
        node.selected = false;
      } else {
        node.selected = true; // 部分选择状态
      }
    }
  }

  toggleSelectAll() {
    const stats = this.getFileStats();
    const newSelected = stats.selected !== stats.total;

    this.toggleFolderSelection(this.fileTree, newSelected);
    this.renderFileTree();
    this.updateStats();
    lucide.createIcons();
  }

  getFileStats() {
    const stats = {
      code: 0,
      config: 0,
      docs: 0,
      total: 0,
      selected: 0,
      totalSize: 0,
    };

    const traverse = (node) => {
      if (node.type === "file") {
        stats.total++;
        if (node.selected) {
          stats.selected++;
          stats.totalSize += node.size || 0;
        }

        const ext = node.extension;
        const codeExtensions = [
          "js",
          "ts",
          "jsx",
          "tsx",
          "py",
          "java",
          "cpp",
          "c",
          "go",
          "rs",
          "php",
          "rb",
          "cs",
          "swift",
          "kt",
          "vue",
        ];
        const configExtensions = [
          "json",
          "yml",
          "yaml",
          "xml",
          "ini",
          "conf",
          "config",
        ];
        const docExtensions = ["md", "txt", "rst", "adoc"];

        if (codeExtensions.includes(ext)) {
          stats.code++;
        } else if (configExtensions.includes(ext)) {
          stats.config++;
        } else if (docExtensions.includes(ext)) {
          stats.docs++;
        }
      } else if (node.children) {
        node.children.forEach(traverse);
      }
    };

    traverse(this.fileTree);
    return stats;
  }

  updateStats() {
    const stats = this.getFileStats();

    document.getElementById("codeCount").textContent = stats.code;
    document.getElementById("configCount").textContent = stats.config;
    document.getElementById("docsCount").textContent = stats.docs;
    document.getElementById("totalSize").textContent = this.formatFileSize(
      stats.totalSize
    );
    document.getElementById("selectedCount").textContent = stats.selected;
    document.getElementById("totalCount").textContent = stats.total;
    document.getElementById("selectedBadgeCount").textContent = stats.selected;

    // 更新按钮状态
    const startBtn = document.getElementById("startAnalysisBtn");
    const toggleBtn = document.getElementById("toggleSelectAllBtn");

    startBtn.disabled = stats.selected === 0;
    startBtn.innerHTML = `<i data-lucide="search" class="h-4 w-4 mr-2"></i>开始分析 (${stats.selected})`;

    toggleBtn.textContent =
      stats.selected === stats.total ? "取消全选" : "全选";

    // 重新初始化图标
    lucide.createIcons();
  }

  startAnalysis() {
    const selectedFilePaths = Array.from(this.selectedFiles);

    if (selectedFilePaths.length === 0) {
      alert("请至少选择一个文件进行分析");
      return;
    }

    // 保存配置到sessionStorage
    const config = {
      mode: this.analysisMode,
      selectedFiles: selectedFilePaths,
    };

    sessionStorage.setItem("analysisConfig", JSON.stringify(config));

    // 跳转到分析页面
    window.location.href = "/analysis/progress";
  }
}

// 页面加载完成后初始化
document.addEventListener("DOMContentLoaded", () => {
  new AnalysisConfig();
});
