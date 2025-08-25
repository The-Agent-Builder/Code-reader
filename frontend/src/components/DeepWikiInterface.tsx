import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Sidebar } from "./DeepWikiSidebar";
import { MainContent } from "./DeepWikiMainContent";
import { FileExplorer } from "./FileExplorer";
import CodeViewer from "./CodeViewer";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { api } from "../services/api";
import { buildFileTree, sortFileTree, FileNode } from "../utils/fileTree";

interface DeepWikiInterfaceProps {
  onBackToUpload: () => void;
  onGoToProfile: () => void;
  currentVersionId?: string;
  projectName?: string;
}

type ViewMode = "documentation" | "code";

export default function DeepWikiInterface({
  onBackToUpload,
  onGoToProfile,
  currentVersionId,
  projectName,
}: DeepWikiInterfaceProps) {
  const [activeSection, setActiveSection] = useState("overview");
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [isFileExplorerVisible, setIsFileExplorerVisible] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("documentation");

  // 新增状态
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [repositoryInfo, setRepositoryInfo] = useState<any>(null);
  const [fileDataMap, setFileDataMap] = useState<Map<string, any>>(new Map());
  const [selectedFileAnalysisId, setSelectedFileAnalysisId] = useState<
    number | undefined
  >(undefined);

  const handleFileSelect = (filePath: string) => {
    console.log("File selected:", filePath);
    console.log("Available files in map:", Array.from(fileDataMap.keys()));

    setSelectedFile(filePath);
    setViewMode("code");

    // 从文件数据映射中获取对应的file_analysis_id
    const fileData = fileDataMap.get(filePath);
    console.log("File data found:", fileData);

    if (fileData && fileData.id) {
      setSelectedFileAnalysisId(fileData.id);
      console.log(
        "Selected file analysis ID:",
        fileData.id,
        "for file:",
        filePath
      );
    } else {
      setSelectedFileAnalysisId(undefined);
      console.warn("No file analysis ID found for file:", filePath);
      console.warn("File data map contents:", fileDataMap);
    }
  };

  const handleBackToDocumentation = () => {
    setViewMode("documentation");
    setSelectedFile(null);
  };

  // 数据加载函数
  const loadProjectData = async (repoName: string) => {
    if (!repoName) return;

    setIsLoading(true);
    setError(null);

    try {
      // 1. 获取仓库信息和任务列表
      console.log("Loading repository data for:", repoName);
      const repoResponse = await api.getRepositoryByName(repoName, true, true);
      console.log("Repository API response:", repoResponse);

      if (repoResponse.status !== "success") {
        throw new Error(`Repository "${repoName}" not found`);
      }

      // 处理精确匹配和模糊匹配的不同响应格式
      let repository;
      if (repoResponse.repository) {
        // 精确匹配返回单个repository对象
        repository = repoResponse.repository;
      } else if (
        repoResponse.repositories &&
        repoResponse.repositories.length > 0
      ) {
        // 模糊匹配返回repositories数组
        repository = repoResponse.repositories[0];
      } else {
        throw new Error(`Repository "${repoName}" not found`);
      }

      console.log("Repository data:", repository);
      setRepositoryInfo(repository);

      // 2. 获取最新任务的文件列表
      if (repository.tasks && repository.tasks.length > 0) {
        console.log("All tasks:", repository.tasks);

        // 找到最新的任务（按start_time排序，后端已经按升序排列，所以取最后一个）
        // 但我们也可以手动确认找到最新的
        const latestTask = repository.tasks.reduce((latest, current) => {
          const latestTime = new Date(latest.start_time).getTime();
          const currentTime = new Date(current.start_time).getTime();
          return currentTime > latestTime ? current : latest;
        });

        console.log("Latest task found:", latestTask);
        console.log("Loading files for task ID:", latestTask.id);

        const filesResponse = await api.getFilesByTaskId(latestTask.id);
        console.log("Files API response:", filesResponse);

        if (filesResponse.status === "success") {
          if (
            filesResponse.files &&
            Array.isArray(filesResponse.files) &&
            filesResponse.files.length > 0
          ) {
            // 3. 构建文件数据映射
            const dataMap = new Map();
            filesResponse.files.forEach((file: any) => {
              // 统一路径格式：将反斜杠转换为正斜杠，与文件树保持一致
              const normalizedPath = file.file_path.replace(/\\/g, "/");
              dataMap.set(normalizedPath, file);
            });
            setFileDataMap(dataMap);
            console.log("File data map built:", dataMap);

            // 4. 构建文件树
            console.log("Building file tree from files:", filesResponse.files);
            const tree = buildFileTree(filesResponse.files);
            sortFileTree(tree);
            setFileTree(tree);
            console.log("File tree built:", tree);
          } else {
            console.warn("No files found for task:", latestTask.id);
            setFileTree(null);
            setFileDataMap(new Map());
          }
        } else {
          console.error("Files API returned error:", filesResponse);
          throw new Error(filesResponse.message || "Failed to fetch files");
        }
      } else {
        console.warn("No tasks found for repository:", repoName);
        setFileTree(null);
      }
    } catch (err) {
      console.error("Error loading project data:", err);
      setError(
        err instanceof Error ? err.message : "Failed to load project data"
      );
    } finally {
      setIsLoading(false);
    }
  };

  // 当projectName改变时加载数据
  useEffect(() => {
    if (projectName && projectName !== "my-awesome-project") {
      loadProjectData(projectName);
    }
  }, [projectName]);

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - DeepWiki Navigation (only show in documentation mode) */}
        {viewMode === "documentation" && (
          <aside className="w-64 border-r border-gray-200 bg-gray-50 overflow-y-auto">
            <Sidebar
              activeSection={activeSection}
              onSectionChange={setActiveSection}
            />
          </aside>
        )}

        {/* Main Content Area */}
        <main
          className={`flex-1 overflow-hidden ${
            isFileExplorerVisible ? "mr-80" : ""
          }`}
        >
          {viewMode === "documentation" ? (
            <MainContent
              activeSection={activeSection}
              onFileSelect={handleFileSelect}
              projectName={projectName}
            />
          ) : (
            selectedFile && (
              <CodeViewer
                filePath={selectedFile}
                fileAnalysisId={selectedFileAnalysisId}
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
              <h3 className="font-medium text-gray-900">源代码浏览器</h3>
              {projectName && projectName !== "my-awesome-project" && (
                <p className="text-xs text-gray-500 mt-1">
                  {repositoryInfo
                    ? `${repositoryInfo.name} (${
                        repositoryInfo.total_tasks || 0
                      } tasks)`
                    : projectName}
                </p>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsFileExplorerVisible(!isFileExplorerVisible)}
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
