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
        // 优先从全局变量获取FileList
        const globalFileList = (window as any).__uploadedFileList as FileList;
        if (globalFileList) {
            console.log("ConfigPage: 从全局变量获取FileList:", globalFileList);
            setSelectedFiles(globalFileList);
            setIsLoading(false);
            return;
        }

        // 从sessionStorage获取文件信息作为备选方案
        const filesData = sessionStorage.getItem("uploadedFiles");
        if (!filesData) {
            // 如果没有文件数据，重定向到上传页面
            navigate("/upload");
            return;
        }

        try {
            const filesInfo: FileInfo[] = JSON.parse(filesData);

            // 调试：打印文件信息
            console.log(
                "ConfigPage: 从sessionStorage读取的文件信息:",
                filesInfo
            );

            // 创建轻量级的File对象（不包含实际内容）
            const dataTransfer = new DataTransfer();

            filesInfo.forEach((fileInfo) => {
                // 创建空的File对象，只保留元信息
                const emptyBlob = new Blob([], { type: fileInfo.type });
                const file = new File([emptyBlob], fileInfo.name, {
                    type: fileInfo.type,
                    lastModified: fileInfo.lastModified,
                });

                // 手动设置size属性以保持原始大小信息
                Object.defineProperty(file, "size", {
                    value: fileInfo.size,
                    writable: false,
                    configurable: false,
                });

                // 设置webkitRelativePath
                if (fileInfo.webkitRelativePath) {
                    Object.defineProperty(file, "webkitRelativePath", {
                        value: fileInfo.webkitRelativePath,
                        writable: false,
                        configurable: false,
                    });
                }

                dataTransfer.items.add(file);
            });

            setSelectedFiles(dataTransfer.files);

            // 调试：验证重建的FileList
            console.log("ConfigPage: 重建的FileList:", dataTransfer.files);
            console.log("ConfigPage: 文件总数:", dataTransfer.files.length);

            setIsLoading(false);
        } catch (error) {
            console.error("解析文件数据失败:", error);
            alert("文件数据解析失败，请重新上传文件");
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
