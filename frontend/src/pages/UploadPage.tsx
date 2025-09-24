import { useNavigate, useOutletContext } from "react-router-dom";
import UploadPageComponent from "../components/UploadPage";
import FileStorage from "../utils/fileStorage";

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
    // 只存储文件元信息到sessionStorage，避免存储配额超限
    const filesInfo: FileInfo[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      filesInfo.push({
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        webkitRelativePath: (file as any).webkitRelativePath || "",
      });
    }

    // 调试：打印文件信息
    console.log("UploadPage: 原始文件信息:", files);
    console.log("UploadPage: 文件元信息:", filesInfo);

    // 只存储文件元信息，不存储文件内容
    sessionStorage.setItem("uploadedFiles", JSON.stringify(filesInfo));
    sessionStorage.setItem("uploadedFilesCount", files.length.toString());

    // 使用FileStorage存储原始FileList
    const fileStorage = FileStorage.getInstance();
    fileStorage.setFiles(files);

    // 导航到配置页面
    navigate("/config");
  };

  return (
    <UploadPageComponent
      onNextStep={handleNextStep}
      totalAnalyzedProjects={totalAnalyzedProjects}
    />
  );
}
