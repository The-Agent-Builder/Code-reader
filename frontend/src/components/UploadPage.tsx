import { useState, useCallback, useEffect } from "react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Upload, Folder, TrendingUp, Users, Shield } from "lucide-react";

interface UploadPageProps {
  onNextStep: (files: FileList) => void;
  totalAnalyzedProjects: number;
}

export default function UploadPage({
  onNextStep,
  totalAnalyzedProjects,
}: UploadPageProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [animatingNumber, setAnimatingNumber] = useState(totalAnalyzedProjects);

  // 数字动画效果 - 当totalAnalyzedProjects变化时平滑过渡
  useEffect(() => {
    if (totalAnalyzedProjects !== animatingNumber) {
      const difference = totalAnalyzedProjects - animatingNumber;
      const steps = 10;
      const stepSize = difference / steps;
      let currentStep = 0;

      const animationInterval = setInterval(() => {
        currentStep++;
        if (currentStep >= steps) {
          setAnimatingNumber(totalAnalyzedProjects);
          clearInterval(animationInterval);
        } else {
          setAnimatingNumber((prev) => Math.round(prev + stepSize));
        }
      }, 50);

      return () => clearInterval(animationInterval);
    }
  }, [totalAnalyzedProjects]); // 移除 animatingNumber 依赖，避免无限循环

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(e.dataTransfer.files);
    }
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        setSelectedFiles(e.target.files);
      }
    },
    []
  );

  const formatNumber = (num: number) => {
    if (num >= 10000) {
      return `${(num / 1000).toFixed(0)}K`;
    }
    return num.toLocaleString();
  };

  const handleNextStep = () => {
    if (selectedFiles) {
      onNextStep(selectedFiles);
    }
  };

  const handleSelectFolderClick = () => {
    const fileInput = document.getElementById(
      "file-upload"
    ) as HTMLInputElement;
    if (fileInput) {
      fileInput.click();
    }
  };

  return (
    <div className="h-full flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-2xl w-full space-y-8">
        <div className="text-center space-y-4">
          <p className="text-lg text-gray-600">
            让 AI 帮您快速理解任何代码库的架构和逻辑
          </p>

          {/* 平台统计信息卡片 */}
          <div className="flex flex-wrap justify-center gap-6 mt-6">
            <div className="bg-white/80 backdrop-blur-sm rounded-lg px-6 py-4 border border-blue-200/50 shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                </div>
                <div className="text-left">
                  <div className="text-2xl font-bold text-blue-700 transition-all duration-300">
                    {formatNumber(animatingNumber)}+
                  </div>
                  <div className="text-sm text-blue-600">已分析项目</div>
                </div>
              </div>
            </div>

            <div className="bg-white/80 backdrop-blur-sm rounded-lg px-6 py-4 border border-green-200/50 shadow-sm">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <Users className="h-5 w-5 text-green-600" />
                </div>
                <div className="text-left">
                  <div className="text-2xl font-bold text-green-700">5K+</div>
                  <div className="text-sm text-green-600">总用户</div>
                </div>
              </div>
            </div>
          </div>

          {/* 实时活动指示 */}
          <div className="flex justify-center mt-4">
            <Badge
              variant="secondary"
              className="animate-pulse bg-blue-100 text-blue-700 border border-blue-200"
            >
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-ping"></div>
              实时分析进行中
            </Badge>
          </div>
        </div>

        <div
          className={`
            relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200
            ${
              dragActive
                ? "border-blue-400 bg-blue-50"
                : selectedFiles
                ? "border-green-400 bg-green-50"
                : "border-gray-300 bg-white hover:border-gray-400"
            }
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            id="file-upload"
            type="file"
            multiple
            webkitdirectory="true"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            onChange={handleFileSelect}
          />

          <div className="space-y-4">
            {selectedFiles ? (
              <>
                <Folder className="mx-auto h-16 w-16 text-green-500" />
                <div>
                  <h3 className="text-lg font-medium text-green-700">
                    已选择 {selectedFiles.length} 个文件
                  </h3>
                  <p className="text-sm text-green-600">
                    点击下一步选择分析模式和文件
                  </p>
                </div>
              </>
            ) : (
              <>
                <Upload className="mx-auto h-16 w-16 text-gray-400" />
                <div>
                  <h3 className="text-lg font-medium text-gray-700">
                    拖拽您的代码库文件夹到此处
                  </h3>
                  <p className="text-sm text-gray-500">或点击选择本地文件夹</p>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex justify-center space-x-4">
          <Button
            variant="outline"
            onClick={handleSelectFolderClick}
            className="cursor-pointer"
          >
            <Folder className="mr-2 h-4 w-4" />
            选择本地文件夹
          </Button>

          <Button
            onClick={handleNextStep}
            disabled={!selectedFiles}
            className="px-8"
          >
            下一步
          </Button>
        </div>

        <div className="text-center text-xs text-gray-500 max-w-md mx-auto">
          <div className="flex items-center justify-center space-x-2 mb-2">
            <Shield className="h-4 w-4 text-blue-500" />
            <p>🔒 代码分析使用本地模型运行，不会出域，确保您的代码安全</p>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            已有{" "}
            <span className="text-blue-600 font-medium">
              {formatNumber(animatingNumber)}
            </span>{" "}
            个项目通过我们的平台获得深度分析
          </p>
        </div>
      </div>
    </div>
  );
}
