import { useState, useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import TopNavigation from "./TopNavigation";
import { useProject } from "../contexts/ProjectContext";

interface ProjectVersion {
  id: string;
  name: string;
  date: string;
  isCurrent: boolean;
}

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { getProjectUrl } = useProject();
  const [currentVersionId, setCurrentVersionId] = useState<string>("v3");

  // 从当前路径中提取项目名称
  const getProjectNameFromPath = () => {
    const path = location.pathname;
    const match = path.match(/^\/result\/(.+)$/);
    return match ? match[1] : "my-awesome-project";
  };

  // 累计分析项目数状态 - 从较大的基数开始，显示平台活跃度
  const [totalAnalyzedProjects, setTotalAnalyzedProjects] =
    useState<number>(12847);

  // 模拟项目版本数据 - 保留最近3个版本
  const [projectVersions] = useState<ProjectVersion[]>([
    {
      id: "v3",
      name: "最新分析 v1.3",
      date: new Date().toISOString(),
      isCurrent: true,
    },
    {
      id: "v2",
      name: "历史版本 v1.2",
      date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1天前
      isCurrent: false,
    },
    {
      id: "v1",
      name: "初始版本 v1.1",
      date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3天前
      isCurrent: false,
    },
  ]);

  // 实时更新分析项目数 - 模拟平台活跃度
  useEffect(() => {
    const updateInterval = setInterval(() => {
      // 随机决定是否在这个周期增加计数（模拟真实的分析活动）
      const shouldUpdate = Math.random() < 0.15; // 15% 的概率更新
      if (shouldUpdate) {
        setTotalAnalyzedProjects(
          (prev) => prev + Math.floor(Math.random() * 3) + 1
        ); // 每次增加 1-3
      }
    }, 8000 + Math.random() * 12000); // 8-20秒间隔，更自然

    return () => clearInterval(updateInterval);
  }, []);

  // 根据路径获取当前页面状态
  const getCurrentPage = () => {
    const path = location.pathname;
    if (path === "/upload" || path === "/") {
      return "upload";
    } else if (path === "/analysis") {
      return "analyzing";
    } else if (path.startsWith("/result/")) {
      return "deepwiki";
    } else if (path === "/background") {
      return "background";
    } else if (path === "/profile") {
      return "profile";
    } else if (path === "/chat") {
      return "chat";
    } else {
      return "upload";
    }
  };

  const handleNavigate = (page: string, projectName?: string) => {
    switch (page) {
      case "upload":
        navigate("/upload");
        break;
      case "analyzing":
        navigate("/analysis");
        break;
      case "deepwiki":
        navigate(getProjectUrl(projectName));
        break;
      case "background":
        navigate("/background");
        break;
      case "profile":
        navigate("/profile");
        break;
      case "chat":
        navigate("/chat");
        break;
      default:
        navigate("/upload");
    }
  };

  const handleVersionChange = (versionId: string) => {
    setCurrentVersionId(versionId);
    // 这里可以根据版本ID加载不同的数据
    console.log("切换到版本:", versionId);
  };

  const handleAnalysisComplete = () => {
    navigate(getProjectUrl());
    // 分析完成后创建新版本，并增加全局计数
    setCurrentVersionId("v3");
    setTotalAnalyzedProjects((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen w-full">
      {/* Global Top Navigation */}
      <TopNavigation
        currentPage={getCurrentPage()}
        onNavigate={handleNavigate}
        projectName={getProjectNameFromPath()}
        showProfileBadge={getCurrentPage() === "background"}
        projectVersions={projectVersions}
        currentVersionId={currentVersionId}
        onVersionChange={handleVersionChange}
      />

      {/* Page Content */}
      <main className="h-[calc(100vh-73px)] w-full">
        <Outlet
          context={{
            totalAnalyzedProjects,
            onAnalysisComplete: handleAnalysisComplete,
            currentVersionId,
          }}
        />
      </main>
    </div>
  );
}
