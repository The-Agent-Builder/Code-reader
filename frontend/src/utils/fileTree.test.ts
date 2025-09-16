/**
 * 测试文件树工具函数
 */

import {
  findFileInTree,
  getPathsToExpand,
  FileNode,
  normalizePath,
  findFileFullPath,
} from "./fileTree";

// 模拟文件树数据
const mockFileTree: FileNode = {
  name: "root",
  type: "folder",
  path: "",
  children: [
    {
      name: "cookbook",
      type: "folder",
      path: "cookbook",
      children: [
        {
          name: "pocketflow-batch",
          type: "folder",
          path: "cookbook/pocketflow-batch",
          children: [
            {
              name: "translations",
              type: "folder",
              path: "cookbook/pocketflow-batch/translations",
              children: [
                {
                  name: "README_CHINESE.md",
                  type: "file",
                  path: "cookbook/pocketflow-batch/translations/README_CHINESE.md",
                },
              ],
            },
          ],
        },
        {
          name: "pocketflow-fastapi-websocket",
          type: "folder",
          path: "cookbook/pocketflow-fastapi-websocket",
          children: [
            {
              name: "requirements.txt",
              type: "file",
              path: "cookbook/pocketflow-fastapi-websocket/requirements.txt",
            },
          ],
        },
      ],
    },
    {
      name: "src",
      type: "folder",
      path: "src",
      children: [
        {
          name: "main.py",
          type: "file",
          path: "src/main.py",
        },
      ],
    },
    // 添加根目录文件用于测试
    {
      name: "README.md",
      type: "file",
      path: "README.md",
    },
    {
      name: "package.json",
      type: "file",
      path: "package.json",
    },
  ],
};

// 测试用例
console.log("=== 文件查找测试 ===");

// 测试1: 查找存在的文件
const test1 = findFileInTree(
  mockFileTree,
  "cookbook/pocketflow-batch/translations/README_CHINESE.md"
);
console.log("测试1 - 查找存在的文件:", test1); // 应该返回 true

// 测试2: 查找存在的文件（Windows路径）
const test2 = findFileInTree(
  mockFileTree,
  "cookbook\\pocketflow-fastapi-websocket\\requirements.txt"
);
console.log("测试2 - 查找存在的文件(Windows路径):", test2); // 应该返回 true

// 测试3: 查找不存在的文件
const test3 = findFileInTree(mockFileTree, "cookbook/nonexistent/file.txt");
console.log("测试3 - 查找不存在的文件:", test3); // 应该返回 false

// 测试4: 查找根目录文件
const test4 = findFileInTree(mockFileTree, "src/main.py");
console.log("测试4 - 查找根目录文件:", test4); // 应该返回 true

// 测试5: URL编码路径测试
console.log("\n=== URL编码路径测试 ===");
const encodedPath =
  "cookbook%5Cpocketflow-batch%5Ctranslations%5CREADME_CHINESE.md";
console.log("编码路径:", encodedPath);
console.log("使用normalizePath标准化:", normalizePath(encodedPath));

// 测试6: 使用标准化路径查找文件
const test6 = findFileInTree(mockFileTree, encodedPath);
console.log("测试6 - 使用URL编码路径查找文件:", test6); // 应该返回 true

console.log("\n=== 文件名查找测试 ===");

// 测试7: 只使用文件名查找（应该在整个树中搜索）
const test7 = findFileInTree(mockFileTree, "README.md");
console.log("测试7 - 只使用文件名查找根目录文件:", test7); // 应该返回 true

// 测试8: 只使用文件名查找子目录中的文件
const test8 = findFileInTree(mockFileTree, "main.py");
console.log("测试8 - 只使用文件名查找子目录文件:", test8); // 应该返回 true

// 测试9: 只使用文件名查找深层目录中的文件
const test9 = findFileInTree(mockFileTree, "README_CHINESE.md");
console.log("测试9 - 只使用文件名查找深层目录文件:", test9); // 应该返回 true

// 测试10: 只使用文件名查找不存在的文件
const test10 = findFileInTree(mockFileTree, "nonexistent.txt");
console.log("测试10 - 只使用文件名查找不存在文件:", test10); // 应该返回 false

console.log("\n=== 完整路径查找测试 ===");

// 测试11: 获取文件名对应的完整路径
const fullPath1 = findFileFullPath(mockFileTree, "README.md");
console.log("测试11 - README.md的完整路径:", fullPath1); // 应该返回 "README.md"

// 测试12: 获取子目录文件的完整路径
const fullPath2 = findFileFullPath(mockFileTree, "main.py");
console.log("测试12 - main.py的完整路径:", fullPath2); // 应该返回 "src/main.py"

// 测试13: 获取深层目录文件的完整路径
const fullPath3 = findFileFullPath(mockFileTree, "README_CHINESE.md");
console.log("测试13 - README_CHINESE.md的完整路径:", fullPath3); // 应该返回完整路径

// 测试14: 使用完整路径查找（应该返回相同路径）
const fullPath4 = findFileFullPath(mockFileTree, "src/main.py");
console.log("测试14 - 使用完整路径查找:", fullPath4); // 应该返回 "src/main.py"

console.log("\n=== 路径展开测试 ===");

// 测试5: 获取需要展开的路径
const test5 = getPathsToExpand(
  mockFileTree,
  "cookbook/pocketflow-batch/translations/README_CHINESE.md"
);
console.log("测试5 - 获取展开路径:", test5);
// 应该返回 ["cookbook", "cookbook/pocketflow-batch", "cookbook/pocketflow-batch/translations"]

// 测试6: 获取简单路径的展开
const test6 = getPathsToExpand(mockFileTree, "src/main.py");
console.log("测试6 - 获取简单路径展开:", test6);
// 应该返回 ["src"]

export { mockFileTree };
