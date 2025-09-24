import { useNavigate, useOutletContext } from "react-router-dom";
import UploadPageComponent from "../components/UploadPage";
import FileStorage from "../utils/fileStorage";
import { applyAllFilters } from "../utils/fileFilter";

interface OutletContext {
  totalAnalyzedProjects: number;
}

interface FileInfo {
  name: string;
  size: number;
  type: string;
  lastModified: number;
  webkitRelativePath: string;
  // 移除content字段，避免存储大量数据到sessionStorage
}

export default function UploadPage() {
  const navigate = useNavigate();
  const { totalAnalyzedProjects } = useOutletContext<OutletContext>();

  const handleNextStep = async (files: FileList) => {
    console.log("UploadPage: 开始处理文件，原始文件数量:", files.length);

    try {
      // 应用文件过滤规则
      const filteredFiles = await applyAllFilters(files);
      console.log("UploadPage: 过滤后文件数量:", filteredFiles.length);

      // 创建新的 FileList
      const dataTransfer = new DataTransfer();
      filteredFiles.forEach(file => {
        dataTransfer.items.add(file);
      });
      const filteredFileList = dataTransfer.files;

      // 存储文件元信息到sessionStorage
      const filesInfo: FileInfo[] = [];
      for (let i = 0; i < filteredFileList.length; i++) {
        const file = filteredFileList[i];
        filesInfo.push({
          name: file.name,
          size: file.size,
          type: file.type,
          lastModified: file.lastModified,
          webkitRelativePath: (file as any).webkitRelativePath || "",
        });
      }

      // 调试：打印文件信息
      console.log("UploadPage: 过滤后的文件信息:", filteredFileList);
      console.log("UploadPage: 文件元信息:", filesInfo);

      // 存储文件元信息
      sessionStorage.setItem("uploadedFiles", JSON.stringify(filesInfo));
      sessionStorage.setItem("uploadedFilesCount", filteredFileList.length.toString());

      // 使用FileStorage存储过滤后的FileList
      const fileStorage = FileStorage.getInstance();
      fileStorage.setFiles(filteredFileList);

      // 导航到配置页面
      navigate("/config");
    } catch (error) {
      console.error("文件过滤失败:", error);
      // 如果过滤失败，使用原始文件列表
      const fileStorage = FileStorage.getInstance();
      fileStorage.setFiles(files);
      navigate("/config");
    }
  };

  return (
    <UploadPageComponent
      onNextStep={handleNextStep}
      totalAnalyzedProjects={totalAnalyzedProjects}
    />
  );
}
