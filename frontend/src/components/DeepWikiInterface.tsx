import React, { useState, useEffect, useCallback } from "react";
import { Button } from "./ui/button";
import { Sidebar } from "./DeepWikiSidebar";
import { MainContent } from "./DeepWikiMainContent";
import { FileExplorer } from "./FileExplorer";
import CodeViewer from "./CodeViewer";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { api } from "../services/api";
import {
    buildFileTree,
    sortFileTree,
    FileNode,
    findFileInTree,
    getPathsToExpand,
    normalizePath,
    debugPrintFileTree,
    findAllFilesByName,
    findFileFullPath,
} from "../utils/fileTree";
import { useProject } from "../contexts/ProjectContext";
import { preprocessMermaidInMarkdown, hasMermaidBlocks } from "../utils/mermaidPreprocessor";

interface DeepWikiInterfaceProps {
    onBackToUpload: () => void;
    onGoToProfile: () => void;
    currentVersionId?: string;
    fullNameHash?: string; // 改为fullNameHash，表示这是仓库的full_name哈希值
}

type ViewMode = "documentation" | "code";

export default function DeepWikiInterface({
    onBackToUpload,
    onGoToProfile,
    currentVersionId,
    fullNameHash,
}: DeepWikiInterfaceProps) {
    const { setCurrentRepository } = useProject();
    const [activeSection, setActiveSection] = useState("overview");
    
    // 使用 useCallback 稳定 setActiveSection，避免不必要的子组件重新渲染
    const handleSectionChange = useCallback((section: string) => {
        setActiveSection(section);
    }, []);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [isFileExplorerVisible, setIsFileExplorerVisible] = useState(true);
    const [viewMode, setViewMode] = useState<ViewMode>("documentation");

    // 新增：文件高亮相关状态
    const [highlightedFile, setHighlightedFile] = useState<string | null>(null);
    const [expandedPaths, setExpandedPaths] = useState<string[]>([]);

    // 新增状态
    const [fileTree, setFileTree] = useState<FileNode | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [repositoryInfo, setRepositoryInfo] = useState<any>(null);
    const [fileDataMap, setFileDataMap] = useState<Map<string, any>>(new Map());
    const [selectedFileAnalysisId, setSelectedFileAnalysisId] = useState<
        number | undefined
    >(undefined);
    const [taskStatistics, setTaskStatistics] = useState<{
        code_lines: number;
        total_files: number;
        module_count: number;
    } | null>(null);
    const [currentTaskId, setCurrentTaskId] = useState<number | null>(null);
    const [processedReadmeContent, setProcessedReadmeContent] = useState<string>("");
    const [isProcessingMermaid, setIsProcessingMermaid] = useState(false);

    // 使用 useCallback 优化，避免每次渲染都创建新函数
    const handleFileSelect = useCallback((filePath: string) => {
        setSelectedFile(filePath);
        setViewMode("code");

        // 从文件数据映射中获取对应的file_analysis_id
        const fileData = fileDataMap.get(filePath);

        if (fileData && fileData.id) {
            setSelectedFileAnalysisId(fileData.id);
        } else {
            setSelectedFileAnalysisId(undefined);
        }
    }, [fileDataMap]);

    // 新增：处理文件高亮定位 - 使用 useCallback 优化
    const handleFileHighlight = useCallback((filePath: string) => {
        // 标准化文件路径：URL解码 + 路径分隔符标准化
        const normalizedPath = normalizePath(filePath);

        // 调试：打印文件树结构
        debugPrintFileTree(fileTree);

        // 调试：查找所有匹配的文件
        const isFileNameOnly = !normalizedPath.includes("/");
        if (isFileNameOnly) {
            const matches = findAllFilesByName(fileTree, normalizedPath);
        }

        // 检查文件是否存在于文件树中
        const fileExists = findFileInTree(fileTree, normalizedPath);

        if (!fileExists) {
            return;
        }

        // 获取文件的完整路径（对于只有文件名的情况很重要）
        const fullPath = findFileFullPath(fileTree, normalizedPath);

        if (!fullPath) {
            return;
        }

        // 确保文件浏览器可见
        setIsFileExplorerVisible(true);

        // 设置高亮文件（使用完整路径）
        setHighlightedFile(fullPath);

        // 获取需要展开的路径（使用完整路径）
        const pathsToExpand = getPathsToExpand(fileTree, fullPath);
        setExpandedPaths(pathsToExpand);


        // 保持高亮状态，不自动清除
        // setTimeout(() => {
        //   setHighlightedFile(null);
        // }, 3000);
    }, [fileTree]);

    const handleBackToDocumentation = () => {
        setViewMode("documentation");
        setSelectedFile(null);
    };

    // 数据加载函数 - 新的流程：通过full_name获取仓库信息
    const loadProjectData = async (fullNameHash: string) => {
        if (!fullNameHash) return;

        setIsLoading(true);
        setError(null);

        try {
            // 1. 通过full_name获取仓库信息
            const repoResponse = await api.getRepositoryByFullName(
                fullNameHash
            );

            if (repoResponse.status !== "success" || !repoResponse.repository) {
                throw new Error(
                    `Repository with full_name "${fullNameHash}" not found`
                );
            }

            const repository = repoResponse.repository;
            setRepositoryInfo(repository);
            // 同时设置到全局Context中，供TopNavigation使用
            setCurrentRepository(repository);

            // 2. 获取该仓库的分析任务列表
            const tasksResponse = await api.getAnalysisTasksByRepositoryId(
                repository.id
            );

            if (
                tasksResponse.status !== "success" ||
                !tasksResponse.tasks ||
                tasksResponse.tasks.length === 0
            ) {
                setIsLoading(false);
                return;
            }

            // 3. 找到最新的任务（按start_time排序，取最前面的）
            const sortedTasks = tasksResponse.tasks.sort(
                (a, b) =>
                    new Date(a.start_time).getTime() -
                    new Date(b.start_time).getTime()
            );
            const latestTask = sortedTasks[0]; // 取排序最前面的任务


            // 4. 设置当前任务ID
            setCurrentTaskId(latestTask.id);

            // 5. 提取任务统计信息
            const statistics = {
                code_lines: (latestTask as any).code_lines || 0,
                total_files: latestTask.total_files || 0,
                module_count: (latestTask as any).module_count || 0,
            };
            setTaskStatistics(statistics);

            // 4. 获取该任务的文件列表
            const filesResponse = await api.getFilesByTaskId(latestTask.id);

            if (filesResponse.status === "success") {
                if (
                    filesResponse.files &&
                    Array.isArray(filesResponse.files) &&
                    filesResponse.files.length > 0
                ) {
                    // 5. 构建文件数据映射
                    const dataMap = new Map();
                    filesResponse.files.forEach((file: any) => {
                        // 统一路径格式：将反斜杠转换为正斜杠，与文件树保持一致
                        const normalizedPath = file.file_path.replace(
                            /\\/g,
                            "/"
                        );
                        dataMap.set(normalizedPath, file);
                    });
                    setFileDataMap(dataMap);

                    // 6. 构建文件树
                    const tree = buildFileTree(filesResponse.files);
                    sortFileTree(tree);
                    setFileTree(tree);

                    // 7. 获取README内容并进行mermaid预处理
                    try {
                        const readmeResponse = await api.getTaskReadmeByTaskId(latestTask.id);
                        
                        if (readmeResponse.status === "success" && readmeResponse.readme) {
                            const rawContent = readmeResponse.readme.content;

                            // 检查是否包含mermaid代码块
                            if (hasMermaidBlocks(rawContent)) {
                                setIsProcessingMermaid(true);
                                
                                try {
                                    const processedContent = await preprocessMermaidInMarkdown(rawContent);
                                    setProcessedReadmeContent(processedContent);
                                } catch (mermaidError) {
                                    // 如果mermaid预处理失败，使用原始内容
                                    setProcessedReadmeContent(rawContent);
                                } finally {
                                    setIsProcessingMermaid(false);
                                }
                            } else {
                                // 没有mermaid代码块，直接使用原始内容
                                setProcessedReadmeContent(rawContent);
                            }
                        } else {
                            setProcessedReadmeContent("");
                        }
                    } catch (readmeError) {
                        setProcessedReadmeContent("");
                    }
                } else {
                    setFileTree(null);
                    setFileDataMap(new Map());
                }
            } else {
                throw new Error(
                    filesResponse.message || "Failed to fetch files"
                );
            }
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to load project data"
            );
        } finally {
            setIsLoading(false);
        }
    };

    // 当fullNameHash改变时加载数据
    useEffect(() => {
        if (fullNameHash && fullNameHash !== "my-awesome-project") {
            loadProjectData(fullNameHash);
        }
    }, [fullNameHash]);

    // 组件卸载时清理Context状态
    useEffect(() => {
        return () => {
            setCurrentRepository(null);
        };
    }, [setCurrentRepository]);

    return (
        <div className="h-full flex flex-col bg-white">
            {/* Main Layout */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left Sidebar - DeepWiki Navigation (only show in documentation mode) */}
                {viewMode === "documentation" && (
                    <aside className="w-64 border-r border-gray-200 bg-gray-50 overflow-y-auto">
                        <Sidebar
                            activeSection={activeSection}
                            onSectionChange={handleSectionChange}
                            taskId={currentTaskId}
                        />
                    </aside>
                )}

                {/* Main Content Area */}
                <main
                    className={`flex-1 overflow-y-auto ${
                        isFileExplorerVisible ? "mr-80" : ""
                    }`}
                >
                    {viewMode === "documentation" ? (
                        <MainContent
                            activeSection={activeSection}
                            onSectionChange={handleSectionChange}
                            onFileSelect={handleFileSelect}
                            onFileHighlight={handleFileHighlight}
                            fileTree={fileTree}
                            projectName={repositoryInfo?.name || fullNameHash}
                            taskStatistics={taskStatistics}
                            taskId={currentTaskId}
                            processedReadmeContent={processedReadmeContent}
                            isProcessingMermaid={isProcessingMermaid}
                        />
                    ) : (
                        selectedFile && (
                            <CodeViewer
                                filePath={selectedFile}
                                fileAnalysisId={selectedFileAnalysisId}
                                taskId={currentTaskId}
                                onBack={handleBackToDocumentation}
                            />
                        )
                    )}
                </main>

                {/* Right Sidebar - File Explorer */}
                <aside
                    className={`
            w-80 border-l border-gray-200 bg-gray-50 flex flex-col transition-all duration-300
            ${isFileExplorerVisible ? "translate-x-0" : "translate-x-full"}
            fixed right-0 top-[73px] bottom-0 z-10
          `}
                >
                    <div className="flex items-center justify-between p-4 border-b border-gray-200">
                        <div>
                            <h3 className="font-medium text-gray-900">
                                源代码浏览器
                            </h3>
                            {fullNameHash &&
                                fullNameHash !== "my-awesome-project" && (
                                    <p className="text-xs text-gray-500 mt-1">
                                        {repositoryInfo
                                            ? `${repositoryInfo.name}`
                                            : fullNameHash}
                                    </p>
                                )}
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                                setIsFileExplorerVisible(!isFileExplorerVisible)
                            }
                        >
                            {isFileExplorerVisible ? (
                                <ChevronRight className="h-4 w-4" />
                            ) : (
                                <ChevronLeft className="h-4 w-4" />
                            )}
                        </Button>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        <FileExplorer
                            selectedFile={selectedFile}
                            onFileSelect={handleFileSelect}
                            fileTree={fileTree}
                            isLoading={isLoading}
                            error={error}
                            highlightedFile={highlightedFile}
                            expandedPaths={expandedPaths}
                        />
                    </div>
                </aside>

                {/* Toggle button when file explorer is hidden */}
                {!isFileExplorerVisible && (
                    <Button
                        variant="outline"
                        size="sm"
                        className="fixed right-4 top-[85px] z-20"
                        onClick={() => setIsFileExplorerVisible(true)}
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                )}
            </div>
        </div>
    );
}
