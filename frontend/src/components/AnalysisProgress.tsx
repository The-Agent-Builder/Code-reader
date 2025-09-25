import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Progress } from "./ui/progress";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card } from "./ui/card";
import {
  Brain,
  Search,
  FileText,
  Database,
  Network,
  Clock,
  Mail,
  Users,
  X,
  CheckCircle2,
  ArrowRight,
  Timer,
  AlertCircle,
} from "lucide-react";
import { api } from "../services/api";

interface AnalysisConfiguration {
  mode: "overall" | "individual";
  selectedFiles: string[];
}

interface AnalysisProgressProps {
  onComplete: () => void;
  onBackgroundMode?: () => void;
  analysisConfig: AnalysisConfiguration;
}

const analysisSteps = [
  { icon: Search, label: "扫描代码文件", duration: 3000 },
  { icon: Database, label: "知识库创建", duration: 2000 },
  { icon: Brain, label: "分析数据模型", duration: 2500 },
  { icon: FileText, label: "生成文档结构", duration: 2000 },
];

export default function AnalysisProgress({
  onComplete,
  onBackgroundMode,
  analysisConfig,
}: AnalysisProgressProps) {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [email, setEmail] = useState("");
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [emailSubmitted, setEmailSubmitted] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);

  // 跟踪每个步骤的完成状态
  const [completedSteps, setCompletedSteps] = useState<boolean[]>(
    new Array(analysisSteps.length).fill(false)
  );

  // 统计信息状态
  const [totalCodeLines, setTotalCodeLines] = useState(0);
  const [successfulFiles, setSuccessfulFiles] = useState(0);
  const [failedFiles, setFailedFiles] = useState(0);
  const [moduleCount, setModuleCount] = useState(0);

  // 使用ref保存统计数据，确保在异步函数中能获取到最新值
  const statsRef = useRef({
    totalCodeLines: 0,
    successfulFiles: 0,
    failedFiles: 0,
    moduleCount: 0,
  });

  // 队列状态相关
  const [isInQueue, setIsInQueue] = useState(false);
  const [queueInfo, setQueueInfo] = useState({
    total_pending: 0,
    running_tasks: 0,
    estimated_wait_time_minutes: 0,
    has_queue: false,
    pending_task_ids: [] as number[],
  });
  const [queueCheckInterval, setQueueCheckInterval] =
    useState<NodeJS.Timeout | null>(null);

  // 任务和文件信息
  const [taskId, setTaskId] = useState<number | null>(null);
  const [fileList, setFileList] = useState<string[]>([]);
  const [md5DirectoryName, setMd5DirectoryName] = useState<string | null>(null);

  // 知识库创建相关状态
  const [vectorizationProgress, setVectorizationProgress] = useState({
    currentBatch: 0,
    totalBatches: 0,
    processedFiles: 0,
    totalFiles: 0,
    currentFile: "",
    indexName: "",
  });

  // 模拟队列数据（保留作为备用）
  const [queueData] = useState({
    position: Math.floor(Math.random() * 8) + 3, // 随机生成3-10的队列位置
    estimatedTime: Math.floor(Math.random() * 25) + 15, // 随机生成15-40分钟的预估时间
    totalInQueue: Math.floor(Math.random() * 20) + 15, // 随机生成15-35的总队列人数
  });

  // 检查队列状态
  const checkQueueStatus = async () => {
    try {
      const response = await api.getQueueStatus();
      if (response.status === "success") {
        setQueueInfo(response.queue_info);

        // 检查当前任务是否在队列中
        const isTaskInQueue =
          taskId && response.queue_info.pending_task_ids.includes(taskId);
        setIsInQueue(isTaskInQueue || false);
      }
    } catch (error) {
      console.error("检查队列状态失败:", error);
    }
  };

  // 检查并更新任务状态为running
  const checkAndUpdateTaskStatus = async (): Promise<boolean> => {
    if (!taskId) {
      console.error("任务ID不存在，无法更新任务状态");
      return false;
    }

    try {
      // 先检查队列状态
      const queueResponse = await api.getQueueStatus();
      if (queueResponse.status === "success") {
        const { pending_task_ids, running_tasks } = queueResponse.queue_info;

        // 检查当前任务是否排在队列第一位，并且没有正在运行的任务
        const isFirstInQueue =
          pending_task_ids.length > 0 && pending_task_ids[0] === taskId;
        const noRunningTasks = running_tasks === 0;

        if (isFirstInQueue && noRunningTasks) {
          console.log("满足条件，将任务状态更新为running");

          // 更新任务状态为running
          const updateResponse = await api.updateAnalysisTask(taskId, {
            status: "running",
          });

          if (updateResponse.status === "success") {
            console.log("任务状态已更新为running");
            return true;
          } else {
            console.error("更新任务状态失败:", updateResponse.message);
            return false;
          }
        } else {
          console.log(
            `队列条件不满足: 当前任务ID=${taskId}, 队列第一位=${pending_task_ids[0]}, 正在运行的任务数=${running_tasks}`
          );
          return false;
        }
      }
      return false;
    } catch (error) {
      console.error("检查并更新任务状态失败:", error);
      return false;
    }
  };

  // 初始化时获取任务信息和检查队列状态
  useEffect(() => {
    console.log("🔍 初始化分析进度组件，检查任务信息...");

    // 从 sessionStorage 获取任务信息
    const taskInfo = sessionStorage.getItem("currentTaskInfo");
    console.log("📋 从sessionStorage获取的任务信息:", taskInfo);

    if (taskInfo) {
      try {
        const parsedTaskInfo = JSON.parse(taskInfo);
        console.log("✅ 解析任务信息成功:", parsedTaskInfo);

        setTaskId(parsedTaskInfo.taskId);
        setMd5DirectoryName(parsedTaskInfo.md5DirectoryName);
        setFileList(
          parsedTaskInfo.fileList || analysisConfig.selectedFiles || []
        );

        console.log("🆔 设置任务ID:", parsedTaskInfo.taskId);
        console.log(
          "📁 设置文件列表长度:",
          (parsedTaskInfo.fileList || analysisConfig.selectedFiles || []).length
        );
      } catch (error) {
        console.error("❌ 解析任务信息失败:", error);
        setFileList(analysisConfig.selectedFiles || []);
      }
    } else {
      console.warn("⚠️ 未找到任务信息，使用配置中的文件列表");
      // 如果没有任务信息，使用配置中的文件列表
      setFileList(analysisConfig.selectedFiles || []);
    }

    checkQueueStatus();
  }, []);

  // 如果在队列中，定期检查状态
  useEffect(() => {
    if (isInQueue) {
      const interval = setInterval(checkQueueStatus, 10000); // 每10秒检查一次
      setQueueCheckInterval(interval);
      return () => {
        clearInterval(interval);
        setQueueCheckInterval(null);
      };
    } else {
      if (queueCheckInterval) {
        clearInterval(queueCheckInterval);
        setQueueCheckInterval(null);
      }
    }
  }, [isInQueue]);

  // 辅助函数：根据文件扩展名获取编程语言
  const getLanguageFromExtension = (filePath: string): string => {
    const extension = filePath.split(".").pop()?.toLowerCase();
    const languageMap: { [key: string]: string } = {
      py: "python",
      js: "javascript",
      ts: "typescript",
      tsx: "typescript",
      jsx: "javascript",
      java: "java",
      cpp: "cpp",
      c: "c",
      cs: "csharp",
      php: "php",
      rb: "ruby",
      go: "go",
      rs: "rust",
      kt: "kotlin",
      swift: "swift",
      md: "markdown",
      txt: "text",
      json: "json",
      xml: "xml",
      html: "html",
      css: "css",
      scss: "scss",
      sass: "sass",
      yml: "yaml",
      yaml: "yaml",
      toml: "toml",
      ini: "ini",
      cfg: "config",
      conf: "config",
      sh: "shell",
      bat: "batch",
      ps1: "powershell",
      sql: "sql",
      r: "r",
      scala: "scala",
      clj: "clojure",
      hs: "haskell",
      elm: "elm",
      dart: "dart",
      vue: "vue",
      svelte: "svelte",
    };
    return languageMap[extension || ""] || "text";
  };

  // 辅助函数：判断是否应该跳过的文件类型
  const shouldSkipFile = (filePath: string): boolean => {
    const extension = filePath.split(".").pop()?.toLowerCase();
    const skipExtensions = [
      "jpg",
      "jpeg",
      "png",
      "gif",
      "bmp",
      "svg",
      "ico",
      "webp", // 图片
      "zip",
      "rar",
      "7z",
      "tar",
      "gz",
      "bz2",
      "xz", // 压缩包
      "pdf",
      "doc",
      "docx",
      "xls",
      "xlsx",
      "ppt",
      "pptx", // 办公文档
      "mp3",
      "mp4",
      "avi",
      "mov",
      "wmv",
      "flv",
      "mkv", // 媒体文件
      "exe",
      "dll",
      "so",
      "dylib",
      "bin", // 二进制文件
      "woff",
      "woff2",
      "ttf",
      "eot", // 字体文件
      "lock",
      "log",
      "tmp",
      "cache", // 临时文件
    ];
    return skipExtensions.includes(extension || "");
  };

  // 辅助函数：计算代码行数
  const countCodeLines = (content: string): number => {
    return content.split("\n").filter((line) => line.trim().length > 0).length;
  };

  // 辅助函数：生成基于文件类型的模拟内容
  const generateMockFileContent = (
    filePath: string,
    language: string
  ): string => {
    const fileName = filePath.split("/").pop() || filePath;

    switch (language) {
      case "python":
        return `#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
${fileName} - Python模块
"""

import os
import sys
import re
from datetime import datetime
from typing import List, Dict, Optional

class ${fileName.replace(".py", "").replace(/[^a-zA-Z0-9]/g, "")}:
    """${fileName} 类"""

    def __init__(self):
        self.name = "${fileName}"
        self.created_at = datetime.now()

    def process(self, data: Dict) -> Optional[List]:
        """处理数据"""
        if not data:
            return None

        result = []
        for key, value in data.items():
            if isinstance(value, str):
                result.append(value.strip())

        return result

if __name__ == "__main__":
    instance = ${fileName.replace(".py", "").replace(/[^a-zA-Z0-9]/g, "")}()
    print(f"Running {instance.name}")`;

      case "javascript":
        return `/**
 * ${fileName} - JavaScript模块
 */

const fs = require('fs');
const path = require('path');
const util = require('util');

class ${fileName.replace(".js", "").replace(/[^a-zA-Z0-9]/g, "")} {
    constructor() {
        this.name = '${fileName}';
        this.version = '1.0.0';
    }

    async process(data) {
        if (!data) {
            throw new Error('Data is required');
        }

        const result = Object.keys(data).map(key => {
            return {
                key,
                value: data[key],
                processed: true
            };
        });

        return result;
    }

    static getInstance() {
        if (!this.instance) {
            this.instance = new ${fileName
              .replace(".js", "")
              .replace(/[^a-zA-Z0-9]/g, "")}();
        }
        return this.instance;
    }
}

module.exports = ${fileName.replace(".js", "").replace(/[^a-zA-Z0-9]/g, "")};`;

      case "typescript":
        return `/**
 * ${fileName} - TypeScript模块
 */

import { readFile, writeFile } from 'fs/promises';
import { join } from 'path';

interface DataItem {
    id: string;
    name: string;
    value: any;
}

interface ProcessResult {
    success: boolean;
    data: DataItem[];
    timestamp: Date;
}

export class ${fileName
          .replace(/\.(ts|tsx)$/, "")
          .replace(/[^a-zA-Z0-9]/g, "")} {
    private readonly name: string;
    private readonly version: string;

    constructor() {
        this.name = '${fileName}';
        this.version = '1.0.0';
    }

    public async process(items: DataItem[]): Promise<ProcessResult> {
        if (!items || items.length === 0) {
            throw new Error('Items array is required');
        }

        const processedData = items.map(item => ({
            ...item,
            processed: true,
            timestamp: new Date()
        }));

        return {
            success: true,
            data: processedData,
            timestamp: new Date()
        };
    }

    public getName(): string {
        return this.name;
    }
}

export default ${fileName
          .replace(/\.(ts|tsx)$/, "")
          .replace(/[^a-zA-Z0-9]/g, "")};`;

      case "markdown":
        return `# ${fileName}

## 概述

这是 ${fileName} 文档文件。

## 功能特性

- 功能1：数据处理
- 功能2：文件操作
- 功能3：配置管理

## 使用方法

\`\`\`bash
# 安装依赖
npm install

# 运行项目
npm start
\`\`\`

## API 文档

### 方法列表

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| process | data: Object | Promise<Array> | 处理数据 |
| validate | input: string | boolean | 验证输入 |

## 配置说明

配置文件位于 \`config/\` 目录下。

## 更新日志

- v1.0.0: 初始版本
- v1.1.0: 添加新功能
`;

      case "json":
        return `{
  "name": "${fileName.replace(".json", "")}",
  "version": "1.0.0",
  "description": "${fileName} 配置文件",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest",
    "build": "webpack --mode production"
  },
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21",
    "moment": "^2.29.0"
  },
  "devDependencies": {
    "jest": "^28.0.0",
    "webpack": "^5.70.0"
  },
  "keywords": [
    "config",
    "settings",
    "application"
  ],
  "author": "Developer",
  "license": "MIT"
}`;

      default:
        return `# ${fileName}
# 这是 ${fileName} 文件
# 文件类型: ${language}

# 配置项
name = "${fileName}"
version = "1.0.0"
description = "${fileName} 配置文件"

# 基本设置
debug = true
port = 3000
host = "localhost"

# 数据库配置
database_url = "sqlite:///app.db"
max_connections = 10

# 日志配置
log_level = "info"
log_file = "app.log"
`;
    }
  };

  // 辅助函数：提取依赖信息
  const extractDependencies = (content: string, language: string): string => {
    const dependencies: Set<string> = new Set();

    switch (language) {
      case "python":
        // Python import 语句
        const pythonImports = content.match(
          /^(?:from\s+(\S+)\s+)?import\s+([^\n#]+)/gm
        );
        pythonImports?.forEach((match) => {
          const parts = match
            .replace(/^(from\s+|import\s+)/, "")
            .split(/[\s,]+/);
          parts.forEach((part) => {
            const cleanPart = part.trim().split(".")[0];
            if (cleanPart && !cleanPart.startsWith(".")) {
              dependencies.add(cleanPart);
            }
          });
        });
        break;

      case "javascript":
      case "typescript":
        // JavaScript/TypeScript import/require 语句
        const jsImports = content.match(
          /(?:import.*?from\s+['"`]([^'"`]+)['"`]|require\s*\(\s*['"`]([^'"`]+)['"`]\s*\))/g
        );
        jsImports?.forEach((match) => {
          const moduleMatch = match.match(/['"`]([^'"`]+)['"`]/);
          if (moduleMatch) {
            const moduleName = moduleMatch[1].split("/")[0];
            if (!moduleName.startsWith(".")) {
              dependencies.add(moduleName);
            }
          }
        });
        break;

      case "java":
        // Java import 语句
        const javaImports = content.match(/^import\s+([^;]+);/gm);
        javaImports?.forEach((match) => {
          const packageName = match
            .replace("import ", "")
            .replace(";", "")
            .trim();
          const rootPackage = packageName.split(".")[0];
          if (rootPackage !== "java" && rootPackage !== "javax") {
            dependencies.add(rootPackage);
          }
        });
        break;

      default:
        // 对于其他语言或文档类型，返回空
        break;
    }

    return Array.from(dependencies).join("|");
  };

  // 执行具体的分析步骤API调用
  const executeAnalysisStep = async (stepIndex: number): Promise<boolean> => {
    try {
      console.log(
        `=== 开始执行步骤 ${stepIndex}: ${analysisSteps[stepIndex].label} ===`
      );

      switch (stepIndex) {
        case 0: // 扫描代码文件
          console.log("开始扫描代码文件...");
          if (!taskId) {
            console.error("任务ID不存在，无法执行文件分析");
            return false;
          }

          // 重置统计信息
          let tempTotalCodeLines = 0;
          let tempSuccessfulFiles = 0;
          let tempFailedFiles = 0;

          // 对每个文件创建分析记录
          for (const filePath of fileList) {
            try {
              // 跳过不需要分析的文件类型
              if (shouldSkipFile(filePath)) {
                console.log(`跳过文件: ${filePath} (不支持的文件类型)`);
                continue;
              }

              // 生成基于文件类型的模拟内容
              const language = getLanguageFromExtension(filePath);
              const mockFileContent = generateMockFileContent(
                filePath,
                language
              );

              const codeLines = countCodeLines(mockFileContent);
              const dependencies = extractDependencies(
                mockFileContent,
                language
              );

              const fileAnalysisData = {
                task_id: taskId,
                file_path: filePath,
                language: language,
                analysis_version: "1.0",
                status: "pending",
                code_lines: codeLines,
                code_content: mockFileContent,
                file_analysis: "",
                dependencies: dependencies,
                error_message: "",
              };

              await api.createFileAnalysis(fileAnalysisData);
              console.log(`文件 ${filePath} 分析完成`);

              // 统计成功文件和代码行数
              tempSuccessfulFiles++;
              tempTotalCodeLines += codeLines;
            } catch (error) {
              console.error(`文件 ${filePath} 分析失败:`, error);
              // 统计失败文件
              tempFailedFiles++;
              // 继续处理其他文件，不中断整个流程
            }
          }

          // 更新统计信息状态和ref
          setTotalCodeLines(tempTotalCodeLines);
          setSuccessfulFiles(tempSuccessfulFiles);
          setFailedFiles(tempFailedFiles);

          // 同时更新ref，确保异步函数中能获取到最新值
          statsRef.current = {
            totalCodeLines: tempTotalCodeLines,
            successfulFiles: tempSuccessfulFiles,
            failedFiles: tempFailedFiles,
            moduleCount: statsRef.current.moduleCount, // 保持之前的模块数量
          };

          console.log(
            `扫描代码文件完成 - 成功: ${tempSuccessfulFiles}, 失败: ${tempFailedFiles}, 总代码行数: ${tempTotalCodeLines}`
          );
          console.log("📊 更新后的统计ref:", statsRef.current);

          console.log("扫描代码文件完成");
          return true;

        case 1: // 知识库创建
          console.log("开始知识库创建...");
          if (!taskId) {
            console.error("任务ID不存在，无法创建知识库");
            return false;
          }

          try {
            // 初始化知识库创建进度状态
            setVectorizationProgress({
              currentBatch: 0,
              totalBatches: 1,
              processedFiles: 0,
              totalFiles: 0,
              currentFile: "正在启动知识库创建...",
              indexName: "",
            });

            // 调用后端知识库创建flow，等待完成
            console.log("触发知识库创建flow，等待完成...");

            // 更新进度状态
            setVectorizationProgress((prev) => ({
              ...prev,
              currentFile: "知识库创建中，请稍候...",
            }));

            const flowResult = await api.createKnowledgeBaseFlow(taskId);

            if (flowResult.status !== "success") {
              console.error("知识库创建失败:", flowResult.message);
              setVectorizationProgress((prev) => ({
                ...prev,
                currentFile: `错误: ${flowResult.message}`,
              }));
              return false;
            }

            console.log("知识库创建完成:", flowResult);

            // 更新进度状态为完成
            setVectorizationProgress((prev) => ({
              ...prev,
              currentBatch: 1,
              processedFiles: 1,
              totalFiles: 1,
              currentFile: "知识库创建完成",
              indexName: flowResult.vectorstore_index || "",
            }));

            console.log("知识库创建步骤完成，准备继续下一步");
            return true;
          } catch (error) {
            console.error("知识库创建过程中出错:", error);
            setVectorizationProgress((prev) => ({
              ...prev,
              currentFile: `错误: ${error}`,
            }));
            return false;
          }

	        case 2: // 分析数据模型
	          console.log("开始分析数据模型...");
	          if (!taskId) {
	            console.error("任务ID不存在，无法执行分析数据模型");
	            return false;
	          }

	          try {
	            const dmResult = await api.analyzeDataModelFlow(taskId);

	            if (dmResult.status !== "success") {
	              console.error("分析数据模型失败:", dmResult.message);
	              return false;
	            }

	            // 根据后端返回更新统计信息（若可用）
	            if (typeof dmResult.successful_files === "number") {
	              statsRef.current = {
	                ...statsRef.current,
	                successfulFiles: dmResult.successful_files ?? statsRef.current.successfulFiles,
	                failedFiles: dmResult.failed_files ?? statsRef.current.failedFiles,
	              };
	              setSuccessfulFiles(statsRef.current.successfulFiles);
	              setFailedFiles(statsRef.current.failedFiles);
	            }

	            console.log("分析数据模型步骤完成");
	            return true;
	          } catch (error) {
	            console.error("分析数据模型过程中出错:", error);
	            return false;
	          }

        case 3: // 生成文档结构
          console.log("开始生成文档结构...");
          if (!taskId) {
            console.error("任务ID不存在，无法生成文档结构");
            return false;
          }

          try {
            // 1. 获取仓库的本地路径
            console.log("获取仓库本地路径...");
            const taskInfo = sessionStorage.getItem("currentTaskInfo");
            if (!taskInfo) {
              console.error("无法获取任务信息");
              return false;
            }

            const parsedTaskInfo = JSON.parse(taskInfo);
            const repositoryId = parsedTaskInfo.repositoryId;
            if (!repositoryId) {
              console.error("无法获取仓库ID");
              return false;
            }

            // 从后端API获取仓库信息
            console.log(`获取仓库 ${repositoryId} 的信息...`);
            const repoResult = await api.getRepositoryById(repositoryId);
            if (repoResult.status !== "success" || !repoResult.repository) {
              console.error("获取仓库信息失败:", repoResult.message);
              return false;
            }

            // 优先使用后端转换的绝对路径，如果没有则使用原始路径
            const localPath =
              repoResult.repository.absolute_local_path ||
              repoResult.repository.local_path;
            console.log(`仓库本地路径: ${localPath}`);

            // 2. 调用外部README API生成文档结构
            console.log("调用外部README API生成文档结构...");
            const generateResult = await api.generateDocumentStructure(
              localPath
            );

            if (
              generateResult.status !== "success" ||
              !generateResult.task_id
            ) {
              console.error(
                "文档结构生成任务创建失败:",
                generateResult.message
              );
              return false;
            }

            const readmeApiTaskId = generateResult.task_id;
            console.log(`文档结构生成任务已创建，任务ID: ${readmeApiTaskId}`);

            // 3. 轮询检查生成状态
            console.log("开始轮询检查文档生成状态...");
            let completed = false;
            let attempts = 0;
            const maxAttempts = 60; // 最多轮询60次（5分钟）
            const pollInterval = 5000; // 每5秒检查一次

            while (!completed && attempts < maxAttempts) {
              attempts++;
              console.log(`第 ${attempts} 次检查文档生成状态...`);

              const statusResult = await api.checkDocumentGenerationStatus(
                readmeApiTaskId
              );

              if (statusResult.status === "completed") {
                console.log("文档结构生成完成!");

                // 4. 获取生成的文档内容
                if (statusResult.result && statusResult.result.markdown) {
                  const markdownContent = statusResult.result.markdown;
                  console.log(
                    "获取到生成的文档内容，长度:",
                    markdownContent.length
                  );

                  // 5. 保存到本项目数据库
                  console.log("保存文档到数据库...");
                  const saveResult = await api.createTaskReadme(
                    taskId,
                    markdownContent
                  );

                  if (saveResult.status === "success") {
                    console.log("文档结构生成并保存成功");
                    completed = true;
                  } else {
                    console.error("保存文档到数据库失败:", saveResult.message);
                    return false;
                  }
                } else {
                  console.error("生成的文档内容为空");
                  return false;
                }
              } else if (
                statusResult.status === "failed" ||
                statusResult.error
              ) {
                console.error(
                  "文档生成失败:",
                  statusResult.error || statusResult.message
                );
                return false;
              } else {
                // 仍在进行中，显示进度
                const progress = statusResult.progress || 0;
                const currentStage = statusResult.current_stage || "处理中";
                console.log(`文档生成进度: ${progress}% - ${currentStage}`);

                // 等待下次检查
                await new Promise((resolve) =>
                  setTimeout(resolve, pollInterval)
                );
              }
            }

            if (!completed) {
              console.error("文档生成超时");
              return false;
            }

            console.log("生成文档结构完成");
            return true;
          } catch (error) {
            console.error("生成文档结构过程中出错:", error);
            return false;
          }

        default:
          return false;
      }
    } catch (error) {
      console.error(`步骤 ${stepIndex} 执行失败:`, error);
      return false;
    }
  };

  useEffect(() => {
    console.log("=== useEffect 被触发 ===", { isInQueue, taskId });

    // 如果在队列中，不开始分析步骤
    if (isInQueue) {
      console.log("任务在队列中，跳过分析步骤");
      return;
    }

    console.log("=== 开始重置分析状态并启动分析流程 ===");

    // 重置步骤完成状态
    setCompletedSteps(new Array(analysisSteps.length).fill(false));
    setCurrentStep(0);
    setProgress(0);
    setIsCompleted(false);

    // 重置统计信息
    setTotalCodeLines(0);
    setSuccessfulFiles(0);
    setFailedFiles(0);
    setModuleCount(0);

    // 同时重置ref
    statsRef.current = {
      totalCodeLines: 0,
      successfulFiles: 0,
      failedFiles: 0,
      moduleCount: 0,
    };

    let isCancelled = false;

    const runAnalysis = async () => {
      // 首先检查并更新任务状态
      const canStart = await checkAndUpdateTaskStatus();
      if (!canStart) {
        console.log("任务无法开始，可能需要排队等待");
        // 重新检查队列状态
        await checkQueueStatus();
        return;
      }

      const totalSteps = analysisSteps.length;

      for (let stepIndex = 0; stepIndex < totalSteps; stepIndex++) {
        if (isCancelled) {
          console.log(`=== 流程被取消，在步骤 ${stepIndex} 处中断 ===`);
          break;
        }

        console.log(
          `=== 开始执行步骤 ${stepIndex}: ${analysisSteps[stepIndex].label} ===`
        );
        setCurrentStep(stepIndex);
        const stepProgressStart = (stepIndex / totalSteps) * 100;
        const stepProgressEnd = ((stepIndex + 1) / totalSteps) * 100;

        // 设置步骤开始时的进度
        setProgress(stepProgressStart);

        // 开始执行当前步骤
        console.log(
          `即将调用 executeAnalysisStep(${stepIndex}): ${analysisSteps[stepIndex].label}`
        );
        const stepSuccess = await executeAnalysisStep(stepIndex);
        console.log(
          `=== 步骤 ${stepIndex} 执行结果: ${
            stepSuccess ? "✅ 成功" : "❌ 失败"
          } ===`
        );

        if (!stepSuccess) {
          console.error(
            `步骤 ${stepIndex} 执行失败: ${analysisSteps[stepIndex].label}`
          );
          // 更新任务状态为failed
          if (taskId) {
            try {
              await api.updateAnalysisTask(taskId, { status: "failed" });
            } catch (error) {
              console.error("更新任务状态为failed失败:", error);
            }
          }
          console.error("分析流程因步骤失败而中断");
          break;
        }

        console.log(
          `步骤 ${stepIndex} 执行成功: ${analysisSteps[stepIndex].label}`
        );

        // 标记当前步骤为完成
        setCompletedSteps((prev) => {
          const newCompleted = [...prev];
          newCompleted[stepIndex] = true;
          return newCompleted;
        });

        // 更新进度到当前步骤完成
        setProgress(stepProgressEnd);

        // 延迟让用户看到步骤完成状态（打勾效果）
        console.log(`=== 步骤 ${stepIndex} 完成，显示打勾状态，等待1.5秒 ===`);
        await new Promise((resolve) => setTimeout(resolve, 1500)); // 增加延迟时间让用户看到打勾
        console.log(`=== 步骤 ${stepIndex} 延迟结束，准备下一步 ===`);
      }

      console.log(
        `=== FOR循环结束 - 所有步骤执行完成，isCancelled: ${isCancelled} ===`
      );

      if (!isCancelled) {
        console.log("=== 所有步骤正常完成，设置分析完成状态 ===");
        console.trace("setIsCompleted(true) 调用堆栈:");
        setProgress(100);
        setIsCompleted(true);

        // 更新任务状态为completed，包含所有统计信息
        // 使用ref中的最新统计数据，避免闭包问题
        const currentStats = statsRef.current;

        if (taskId && taskId > 0) {
          try {
            const updateData = {
              status: "completed",
              end_time: new Date().toISOString(),
              successful_files: currentStats.successfulFiles,
              failed_files: currentStats.failedFiles,
              code_lines: currentStats.totalCodeLines,
              module_count: currentStats.moduleCount,
            };

            console.log("🎯 准备更新任务完成状态");
            console.log("📊 统计信息 (来自ref):", updateData);
            console.log("📊 当前state值:", {
              successfulFiles,
              failedFiles,
              totalCodeLines,
              moduleCount,
            });
            console.log("📊 当前ref值:", currentStats);
            console.log("🆔 任务ID:", taskId);

            const result = await api.updateAnalysisTask(taskId, updateData);

            console.log("✅ 任务状态已成功更新为completed");
            console.log("📋 更新结果:", result);
          } catch (error) {
            console.error("❌ 更新任务状态为completed失败:");
            console.error("🔍 错误详情:", error);
            console.error("📝 尝试更新的数据 (来自ref):", {
              taskId,
              status: "completed",
              end_time: new Date().toISOString(),
              successful_files: currentStats.successfulFiles,
              failed_files: currentStats.failedFiles,
              code_lines: currentStats.totalCodeLines,
              module_count: currentStats.moduleCount,
            });

            // 即使更新失败，也不影响UI显示完成状态
            console.warn("⚠️ 任务状态更新失败，但分析流程已完成");
          }
        } else {
          console.error("❌ 无法更新任务状态：taskId 为空");
          console.log("🔍 当前状态:", {
            taskId,
            successfulFiles,
            failedFiles,
            totalCodeLines,
            moduleCount,
          });

          // 检查sessionStorage中的任务信息
          const taskInfo = sessionStorage.getItem("currentTaskInfo");
          console.log("🔍 sessionStorage中的任务信息:", taskInfo);

          if (taskInfo) {
            try {
              const parsedTaskInfo = JSON.parse(taskInfo);
              console.log("🔍 解析后的任务信息:", parsedTaskInfo);
              console.log("🔍 任务ID字段:", parsedTaskInfo.taskId);
            } catch (error) {
              console.error("❌ 解析sessionStorage任务信息失败:", error);
            }
          }
        }
      }
    };

    // 延迟开始分析，让用户看到初始状态
    const timer = setTimeout(() => {
      runAnalysis();
    }, 1000);

    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [isInQueue, taskId]); // 依赖 isInQueue 和 taskId，当状态改变时重新执行

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setEmailSubmitted(true);
      // 这里可以添加实际的邮箱通知逻辑
      console.log("Email submitted:", email);

      // 开始3秒倒计时
      setCountdown(3);
      const countdownInterval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            if (onBackgroundMode) {
              onBackgroundMode();
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return `约 ${minutes} 分钟`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `约 ${hours} 小时 ${mins} 分钟`;
  };

  // 处理分析完成后的跳转
  const handleAnalysisComplete = () => {
    console.log("分析完成，准备跳转。MD5目录名:", md5DirectoryName);
    if (md5DirectoryName) {
      // 如果有MD5目录名，直接跳转到结果页面
      console.log(`跳转到结果页面: /result/${md5DirectoryName}`);
      navigate(`/result/${md5DirectoryName}`);
    } else {
      // 如果没有MD5，调用原来的完成回调
      console.log("没有MD5信息，使用原来的完成回调");
      onComplete();
    }
  };

  return (
    <div className="h-full flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full space-y-8">
        {/* 分析配置信息卡片 */}
        <Card className="p-6">
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Brain className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">分析配置</h3>
                <p className="text-sm text-gray-600">
                  {analysisConfig.mode === "overall"
                    ? "代码整体分析"
                    : "代码逐个解析"}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">分析模式</span>
                <span className="font-medium">
                  {analysisConfig.mode === "overall" ? "整体架构" : "逐个解析"}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">文件数量</span>
                <span className="font-medium">
                  {analysisConfig.selectedFiles.length} 个
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* 队列状态卡片 - 只在有队列且未完成时显示 */}
        {!isCompleted && isInQueue && (
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Timer className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">任务队列中</h3>
                  <p className="text-sm text-gray-600">
                    {queueInfo.running_tasks > 0
                      ? `当前有 ${queueInfo.running_tasks} 个任务正在处理中`
                      : "系统正在处理其他任务"}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="space-y-1">
                  <div className="text-2xl font-bold text-blue-600">
                    #
                    {taskId && queueInfo.pending_task_ids.includes(taskId)
                      ? queueInfo.pending_task_ids.indexOf(taskId) + 1
                      : queueInfo.total_pending}
                  </div>
                  <div className="text-xs text-gray-500">排队位置</div>
                </div>
                <div className="space-y-1">
                  <div className="text-2xl font-bold text-green-600">
                    {taskId && queueInfo.pending_task_ids.includes(taskId)
                      ? Math.max(
                          0,
                          queueInfo.pending_task_ids.indexOf(taskId) * 15
                        )
                      : queueInfo.estimated_wait_time_minutes}
                    分
                  </div>
                  <div className="text-xs text-gray-500">预估时间</div>
                </div>
                <div className="space-y-1">
                  <div className="text-2xl font-bold text-purple-600">
                    {queueInfo.total_pending}
                  </div>
                  <div className="text-xs text-gray-500">排队任务</div>
                </div>
              </div>

              <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="text-yellow-800 font-medium">
                      {taskId &&
                      queueInfo.pending_task_ids.includes(taskId) &&
                      queueInfo.pending_task_ids.indexOf(taskId) === 0
                        ? "您的任务即将开始"
                        : queueInfo.total_pending > 5
                        ? "分析队列较长"
                        : "正在排队等待"}
                    </p>
                    <p className="text-yellow-700">
                      {taskId &&
                      queueInfo.pending_task_ids.includes(taskId) &&
                      queueInfo.pending_task_ids.indexOf(taskId) === 0
                        ? "系统正在检查运行条件，请稍候..."
                        : `预计需要等待约 ${
                            taskId &&
                            queueInfo.pending_task_ids.includes(taskId)
                              ? Math.max(
                                  0,
                                  queueInfo.pending_task_ids.indexOf(taskId) *
                                    15
                                )
                              : queueInfo.estimated_wait_time_minutes
                          } 分钟，您可以留下邮箱后离开`}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* 主要内容区 */}
        <div className="text-center space-y-6">
          {/* 分析完成状态 */}
          {isCompleted ? (
            <div className="space-y-6">
              <Card className="p-6 bg-green-50 border-green-200">
                <div className="flex flex-col items-center space-y-4">
                  <div className="p-3 bg-green-100 rounded-full">
                    <CheckCircle2 className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="text-center">
                    <h3 className="text-xl font-bold text-green-800 mb-2">
                      分析完成！
                    </h3>
                    <p className="text-green-700 mb-4">
                      您的代码分析已经完成，现在可以查看详细的分析结果了。
                    </p>

                    {/* 分析统计信息 */}
                    <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                      <div className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="text-green-600 font-medium">
                          成功分析文件
                        </div>
                        <div className="text-2xl font-bold text-green-800">
                          {successfulFiles}
                        </div>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="text-green-600 font-medium">
                          代码总行数
                        </div>
                        <div className="text-2xl font-bold text-green-800">
                          {totalCodeLines.toLocaleString()}
                        </div>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="text-green-600 font-medium">
                          分析模块数
                        </div>
                        <div className="text-2xl font-bold text-green-800">
                          {moduleCount}
                        </div>
                      </div>
                      <div className="bg-white rounded-lg p-3 border border-green-200">
                        <div className="text-green-600 font-medium">
                          失败文件数
                        </div>
                        <div className="text-2xl font-bold text-red-600">
                          {failedFiles}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>

              <Button
                onClick={handleAnalysisComplete}
                className="w-full py-3 text-lg"
                size="lg"
              >
                <ArrowRight className="h-5 w-5 mr-2" />
                查看分析结果
              </Button>
            </div>
          ) : (
            <div>
              <div className="space-y-4">
                <p className="text-gray-600">分析完成后我们会通过邮箱通知您</p>
              </div>

              {/* 邮箱通知区域 */}
              {!emailSubmitted ? (
                <div className="space-y-4">
                  {!showEmailForm ? (
                    <Button
                      onClick={() => setShowEmailForm(true)}
                      className="w-full"
                      variant="outline"
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      留下邮箱，完成后通知我
                    </Button>
                  ) : (
                    <Card className="p-4">
                      <form onSubmit={handleEmailSubmit} className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium text-gray-900">
                            邮箱通知
                          </h4>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowEmailForm(false)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>

                        <div className="space-y-3">
                          <Input
                            type="email"
                            placeholder="输入您的邮箱地址"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="w-full"
                          />
                          <p className="text-xs text-gray-500">
                            我们会在分析完成后第一时间通知您，不会发送其他邮件
                          </p>
                        </div>

                        <Button type="submit" className="w-full">
                          <Mail className="h-4 w-4 mr-2" />
                          确认并后台运行
                        </Button>
                      </form>
                    </Card>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <Card className="p-4 bg-green-50 border-green-200">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-green-100 rounded-full">
                        <Mail className="h-4 w-4 text-green-600" />
                      </div>
                      <div className="text-left">
                        <p className="font-medium text-green-800">
                          邮箱通知已设置
                        </p>
                        <p className="text-sm text-green-600">
                          将发送到: {email}
                        </p>
                      </div>
                    </div>
                  </Card>

                  {countdown > 0 && (
                    <Card className="p-4 bg-blue-50 border-blue-200">
                      <div className="text-center">
                        <p className="text-sm text-blue-800 mb-2">
                          正在切换到后台运行模式...
                        </p>
                        <div className="flex items-center justify-center space-x-2">
                          <div className="w-8 h-8 bg-blue-200 rounded-full flex items-center justify-center">
                            <span className="text-lg font-bold text-blue-700">
                              {countdown}
                            </span>
                          </div>
                          <span className="text-sm text-blue-600">
                            秒后自动跳转
                          </span>
                        </div>
                      </div>
                    </Card>
                  )}
                </div>
              )}

              {/* 进度条和步骤显示 - 只在未完成且不在队列中时显示 */}
              {!isCompleted && !isInQueue && (
                <div className="space-y-6">
                  <Progress value={progress} className="h-2" />

                  {/* 向量化进度详情 - 只在知识库创建步骤时显示 */}
                  {currentStep === 1 &&
                    vectorizationProgress.totalFiles > 0 && (
                      <Card className="p-4 bg-blue-50 border-blue-200">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="font-medium text-blue-800">
                              知识库创建进度
                            </h4>
                            <span className="text-sm text-blue-600">
                              {vectorizationProgress.currentBatch}/
                              {vectorizationProgress.totalBatches} 批次
                            </span>
                          </div>

                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-blue-700">已处理文档</span>
                              <span className="font-medium text-blue-800">
                                {vectorizationProgress.processedFiles}/
                                {vectorizationProgress.totalFiles}
                              </span>
                            </div>

                            <Progress
                              value={
                                (vectorizationProgress.processedFiles /
                                  vectorizationProgress.totalFiles) *
                                100
                              }
                              className="h-1"
                            />

                            {vectorizationProgress.currentFile && (
                              <div className="text-xs text-blue-600 truncate">
                                当前处理: {vectorizationProgress.currentFile}
                              </div>
                            )}

                            {vectorizationProgress.indexName && (
                              <div className="text-xs text-blue-600">
                                索引名称: {vectorizationProgress.indexName}
                              </div>
                            )}
                          </div>
                        </div>
                      </Card>
                    )}

                  <div className="space-y-4">
                    {analysisSteps.map((step, index) => {
                      const Icon = step.icon;
                      const isActive =
                        index === currentStep && !completedSteps[index];
                      const isStepCompleted = completedSteps[index];

                      return (
                        <div
                          key={index}
                          className={`
                            flex items-center space-x-3 p-3 rounded-lg transition-all duration-300
                            ${
                              isActive
                                ? "bg-blue-100 text-blue-700"
                                : isStepCompleted
                                ? "bg-green-100 text-green-700"
                                : "bg-gray-50 text-gray-500"
                            }
                          `}
                        >
                          <Icon
                            className={`
                              h-5 w-5
                              ${isActive ? "animate-pulse" : ""}
                            `}
                          />
                          <span className="flex-1 text-left">
                            {step.label}
                            {/* 在知识库创建步骤显示额外信息 */}
                            {index === 1 &&
                              isActive &&
                              vectorizationProgress.totalFiles > 0 && (
                                <span className="block text-xs mt-1 opacity-75">
                                  正在处理 {vectorizationProgress.totalFiles}{" "}
                                  个文档...
                                </span>
                              )}
                          </span>
                          {isStepCompleted && (
                            <span className="text-green-600">✓</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 排队状态下的提示信息 */}
              {!isCompleted && isInQueue && (
                <div className="space-y-4">
                  <Card className="p-6 bg-blue-50 border-blue-200">
                    <div className="text-center space-y-3">
                      <div className="p-3 bg-blue-100 rounded-full inline-block">
                        <Timer className="h-6 w-6 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-blue-800 mb-2">
                          任务已加入队列
                        </h3>
                        <p className="text-blue-700">
                          您的分析任务正在排队等待处理，系统会按照提交顺序依次执行分析任务。
                        </p>
                        <p className="text-sm text-blue-600 mt-2">
                          请耐心等待或留下邮箱地址，我们会在分析完成后通知您。
                        </p>
                      </div>
                    </div>
                  </Card>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
