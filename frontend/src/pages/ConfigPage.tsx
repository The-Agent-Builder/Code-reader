import { useEffect, useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import AnalysisConfig from "../components/AnalysisConfig";

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
  content: string; // base64编码的文件内容
}

export default function ConfigPage() {
  const navigate = useNavigate();
  const { onAnalysisComplete } = useOutletContext<OutletContext>();
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 从sessionStorage获取上传的文件信息
    const filesData = sessionStorage.getItem("uploadedFiles");
    if (!filesData) {
      // 如果没有文件数据，重定向到上传页面
      navigate("/upload");
      return;
    }

    try {
      const filesInfo: FileInfo[] = JSON.parse(filesData);

      // 调试：打印文件信息
      console.log("ConfigPage: 从sessionStorage读取的文件信息:", filesInfo);

      // 重新构建FileList
      // 注意：这是一个模拟实现，因为我们无法完全重建原始的File对象
      // 在实际应用中，你可能需要保持文件在内存中或使用其他状态管理方案
      const dataTransfer = new DataTransfer();

      // 为每个文件信息创建一个包含实际内容的File对象
      filesInfo.forEach((fileInfo) => {
        // 从base64解码文件内容
        let fileContent: Uint8Array;
        try {
          if (fileInfo.content) {
            const binaryString = atob(fileInfo.content);
            fileContent = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              fileContent[i] = binaryString.charCodeAt(i);
            }
          } else {
            fileContent = new Uint8Array(0); // 空内容
          }
        } catch (error) {
          console.error(`解码文件内容失败 ${fileInfo.name}:`, error);
          fileContent = new Uint8Array(0); // 解码失败时使用空内容
        }

        // 创建包含实际内容的Blob和File对象
        const blob = new Blob([fileContent], { type: fileInfo.type });
        const file = new File([blob], fileInfo.name, {
          type: fileInfo.type,
          lastModified: fileInfo.lastModified,
        });

        // 注意：不再需要手动设置size属性，因为File对象会自动从Blob获取正确的大小

        // 设置webkitRelativePath（如果支持的话）
        if (fileInfo.webkitRelativePath) {
          Object.defineProperty(file, "webkitRelativePath", {
            value: fileInfo.webkitRelativePath,
            writable: false,
          });
        }

        dataTransfer.items.add(file);
      });

      setSelectedFiles(dataTransfer.files);

      // 调试：验证重建的FileList
      console.log("ConfigPage: 重建的FileList:", dataTransfer.files);
      Array.from(dataTransfer.files).forEach((file, index) => {
        console.log(`文件 ${index}:`, {
          name: file.name,
          size: file.size,
          type: file.type,
          webkitRelativePath: (file as any).webkitRelativePath,
          hasContent: file.size > 0, // 检查是否有内容
        });
      });

      setIsLoading(false);
    } catch (error) {
      console.error("解析文件数据失败:", error);
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
