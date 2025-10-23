import { useState, useEffect } from "react";
import TopNavigation from "./components/TopNavigation";
import UploadPage from "./components/UploadPage";
import AnalysisProgress from "./components/AnalysisProgress";
import DeepWikiInterface from "./components/DeepWikiInterface";
import PersonalSpace from "./components/PersonalSpace";
import ChatInterface from "./components/ChatInterface";

type AppState =
  | "upload"
  | "analyzing"
  | "deepwiki"
  | "background"
  | "profile"
  | "chat";

interface ProjectVersion {
  id: string;
  name: string;
  date: string;
  isCurrent: boolean;
}

interface AnalysisConfiguration {
  mode: "overall" | "individual";
  selectedFiles: string[];
}

export default function App() {
  const [appState, setAppState] = useState<AppState>("upload");
  const [currentVersionId, setCurrentVersionId] = useState<string>("v3");
  const [analysisConfig, setAnalysisConfig] =
    useState<AnalysisConfiguration | null>(null);

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


  const handleStartAnalysis = (config: AnalysisConfiguration) => {
    setAnalysisConfig(config);
    setAppState("analyzing");
  };

  const handleAnalysisComplete = () => {
    setAppState("deepwiki");
    // 分析完成后创建新版本，并增加全局计数
    setCurrentVersionId("v3");
    setTotalAnalyzedProjects((prev) => prev + 1);
  };

  const handleBackToUpload = () => {
    setAppState("upload");
  };

  const handleBackgroundMode = () => {
    setAppState("background");
  };

  const handleGoToProfile = () => {
    setAppState("profile");
  };

  const handleBackToDeepWiki = () => {
    setAppState("deepwiki");
  };

  const handleNavigate = (page: AppState) => {
    setAppState(page);
  };

  const handleVersionChange = (versionId: string) => {
    setCurrentVersionId(versionId);
    // 这里可以根据版本ID加载不同的数据
    console.log("切换到版本:", versionId);
  };

  return (
    <div className="min-h-screen w-full">
      {/* Global Top Navigation */}
      <TopNavigation
        currentPage={appState}
        onNavigate={handleNavigate}
        projectName="my-awesome-project"
        showProfileBadge={appState === "background"}
        projectVersions={projectVersions}
        currentVersionId={currentVersionId}
        onVersionChange={handleVersionChange}
      />

      {/* Page Content */}
      <main className="h-[calc(100vh-73px)] w-full">
        {appState === "upload" && (
          <UploadPage
            onStartAnalysis={handleStartAnalysis}
            totalAnalyzedProjects={totalAnalyzedProjects}
          />
        )}

        {appState === "analyzing" && analysisConfig && (
          <AnalysisProgress
            onComplete={handleAnalysisComplete}
            onBackgroundMode={handleBackgroundMode}
            analysisConfig={analysisConfig}
          />
        )}

        {appState === "background" && (
          <div className="h-full flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
            <div className="max-w-md w-full text-center space-y-6">
              <div className="space-y-4">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                  <svg
                    className="w-8 h-8 text-blue-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900">
                  分析正在后台进行
                </h2>
                <p className="text-gray-600">
                  我们会在分析完成后通过邮箱通知您。您现在可以安全地关闭此页面。
                </p>
              </div>

              <div className="space-y-3">
                <button
                  onClick={handleAnalysisComplete}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors"
                >
                  模拟分析完成（演示用）
                </button>

                <button
                  onClick={handleBackToUpload}
                  className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-lg transition-colors"
                >
                  返回首页
                </button>
              </div>

              <div className="text-xs text-gray-500">
                <p>采用本地AI模型分析，数据不出域，安全无忧</p>
              </div>
            </div>
          </div>
        )}

        {appState === "deepwiki" && (
          <DeepWikiInterface
            onBackToUpload={handleBackToUpload}
            onGoToProfile={handleGoToProfile}
            currentVersionId={currentVersionId}
          />
        )}

        {appState === "profile" && (
          <PersonalSpace onBack={handleBackToDeepWiki} />
        )}

        {appState === "chat" && (
          <ChatInterface
            onBack={handleBackToDeepWiki}
            currentVersionId={currentVersionId}
          />
        )}
      </main>
    </div>
  );
}
