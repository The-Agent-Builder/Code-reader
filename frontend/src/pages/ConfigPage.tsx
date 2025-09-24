import { useEffect, useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import AnalysisConfig from "../components/AnalysisConfig";
import FileStorage from "../utils/fileStorage";

interface AnalysisConfiguration {
  mode: "overall" | "individual";
  selectedFiles: string[];
}

interface OutletContext {
  onAnalysisComplete: () => void;
}

interface FileInfo {
  name: string;
  size: number;
  type: string;
  lastModified: number;
  webkitRelativePath: string;
  // 移除content字段，改为从window对象获取原始FileList
}

export default function ConfigPage() {
  const navigate = useNavigate();
  const { onAnalysisComplete } = useOutletContext<OutletContext>();
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 使用FileStorage获取文件
    const fileStorage = FileStorage.getInstance();
    const uploadedFileList = fileStorage.getFiles();

    if (!uploadedFileList) {
      // 如果没有文件数据，重定向到上传页面
      navigate("/upload");
      return;
    }

    try {
      // 直接使用原始的FileList
      setSelectedFiles(uploadedFileList);

      // 调试：打印文件信息
      console.log("ConfigPage: 使用FileStorage获取的FileList:", uploadedFileList);
      Array.from(uploadedFileList).forEach((file, index) => {
        console.log(`文件 ${index}:`, {
          name: file.name,
          size: file.size,
          type: file.type,
          webkitRelativePath: (file as any).webkitRelativePath,
        });
      });

      setIsLoading(false);
    } catch (error) {
      console.error("获取文件数据失败:", error);
      navigate("/upload");
    }
  }, [navigate]);

  const handleStartAnalysis = (
    config: AnalysisConfiguration & {
      repositoryId?: number;
      repositoryName?: string;
    }
  ) => {
    // 将配置信息存储到sessionStorage
    sessionStorage.setItem("analysisConfig", JSON.stringify(config));
    navigate("/analysis");
  };

  const handleBack = () => {
    navigate("/upload");
  };

  // 如果正在加载或没有文件数据，显示加载状态
  if (isLoading || !selectedFiles) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">正在加载文件信息...</p>
        </div>
      </div>
    );
  }

  return (
    <AnalysisConfig
      selectedFiles={selectedFiles}
      onStartAnalysis={handleStartAnalysis}
      onBack={handleBack}
    />
  );
}
