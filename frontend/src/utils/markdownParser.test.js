/**
 * 测试markdown解析逻辑
 * 这个文件用于验证改进后的标题解析是否正确工作
 */

// 模拟测试用的markdown内容
const testMarkdownContent = `
# Wiki Documentation for https://github.com/The-Pocket/PocketFlow

Generated on: 2025-09-12 19:20:03

## Table of Contents

- [项目介绍](#introduction)
- [安装指南](#installation)
- [快速开始](#quickstart)

<a id='introduction'></a>

## 项目介绍

### Related Pages

Related topics: [核心抽象层](#core-abstraction), [安装指南](#installation)

\`\`\`python
# 这不应该被识别为标题
def example_function():
    pass
\`\`\`

## 安装指南

这是安装指南的内容。

### 系统要求

这是三级标题，不应该在导航中显示。

## 快速开始

这是快速开始的内容。

# ############### 这不应该被识别为标题

# 这是另一个有效的一级标题

## 这是对应的二级标题

# https://example.com 这不应该被识别为标题

## 正常的二级标题
`;

// 预期的解析结果
const expectedSections = [
  {
    id: "wiki-documentation-for-httpsgithubcomthe-pocketpocketflow",
    title: "Wiki Documentation for https://github.com/The-Pocket/PocketFlow",
    level: 1,
    children: [
      {
        id: "table-of-contents",
        title: "Table of Contents",
        level: 2,
      },
      {
        id: "项目介绍",
        title: "项目介绍",
        level: 2,
      },
      {
        id: "安装指南",
        title: "安装指南",
        level: 2,
      },
      {
        id: "快速开始",
        title: "快速开始",
        level: 2,
      },
    ],
  },
  {
    id: "这是另一个有效的一级标题",
    title: "这是另一个有效的一级标题",
    level: 1,
    children: [
      {
        id: "这是对应的二级标题",
        title: "这是对应的二级标题",
        level: 2,
      },
      {
        id: "正常的二级标题",
        title: "正常的二级标题",
        level: 2,
      },
    ],
  },
];

console.log("测试用例准备完成");
console.log("测试markdown内容长度:", testMarkdownContent.length);
console.log("预期解析出的一级标题数量:", expectedSections.length);

// 这个文件可以用于手动测试解析逻辑
// 在浏览器控制台中运行相关函数来验证结果
