import { useNavigate, useOutletContext } from "react-router-dom";
import UploadPageComponent from "../components/UploadPage";
import { FileProcessor, FileUploadManager } from "../utils/fileProcessor";

interface OutletContext {
    totalAnalyzedProjects: number;
}

// 全局文件管理器，避免重复处理
let globalFileManager: FileUploadManager | null = null;

export default function UploadPage() {
    const navigate = useNavigate();
    const { totalAnalyzedProjects } = useOutletContext<OutletContext>();

    const handleNextStep = async (files: FileList) => {
        try {
            // 检查文件是否可以安全处理
            const { canProcess, reason } = FileProcessor.canProcessFiles(files);
            if (!canProcess) {
                alert(`无法处理文件: ${reason}`);
                return;
            }

            // 创建文件管理器
            globalFileManager = new FileUploadManager();
            await globalFileManager.addFiles(files);

            // 只存储文件元信息，不存储内容
            const filesInfo = FileProcessor.extractFileInfo(files);

            // 调试：打印文件信息
            console.log("UploadPage: 文件信息:", filesInfo);
            console.log(
                "UploadPage: 总文件大小:",
                FileProcessor.formatFileSize(
                    filesInfo.reduce((sum, f) => sum + f.size, 0)
                )
            );

            // 存储轻量级文件信息
            sessionStorage.setItem("uploadedFiles", JSON.stringify(filesInfo));
            sessionStorage.setItem(
                "uploadedFilesCount",
                files.length.toString()
            );

            // 将FileList存储在全局变量中，供配置页面使用
            (window as any).__uploadedFileList = files;

            // 监控内存使用
            const memoryUsage = FileProcessor.getMemoryUsage();
            if (memoryUsage) {
                console.log("内存使用情况:", {
                    used: FileProcessor.formatFileSize(memoryUsage.used),
                    total: FileProcessor.formatFileSize(memoryUsage.total),
                    percentage:
                        Math.round(
                            (memoryUsage.used / memoryUsage.total) * 100
                        ) + "%",
                });
            }

            // 导航到配置页面
            navigate("/config");
        } catch (error) {
            console.error("处理文件失败:", error);
            alert(
                `处理文件失败: ${
                    error instanceof Error ? error.message : "未知错误"
                }`
            );
        }
    };

    return (
        <UploadPageComponent
            onNextStep={handleNextStep}
            totalAnalyzedProjects={totalAnalyzedProjects}
        />
    );
}
