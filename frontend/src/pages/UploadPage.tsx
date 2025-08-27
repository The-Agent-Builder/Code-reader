import { useNavigate, useOutletContext } from "react-router-dom";
import UploadPageComponent from "../components/UploadPage";

interface OutletContext {
  totalAnalyzedProjects: number;
}

export default function UploadPage() {
  const navigate = useNavigate();
  const { totalAnalyzedProjects } = useOutletContext<OutletContext>();

  const handleNextStep = (files: FileList) => {
    // 将文件信息存储到sessionStorage，供配置页面使用
    // 注意：FileList不能直接序列化，这里我们保存文件的基本信息
    const filesInfo = Array.from(files).map((file) => ({
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified,
      webkitRelativePath: (file as any).webkitRelativePath || "",
    }));

    // 调试：打印原始文件信息
    console.log("UploadPage: 原始文件信息:", files);
    console.log("UploadPage: 序列化的文件信息:", filesInfo);

    sessionStorage.setItem("uploadedFiles", JSON.stringify(filesInfo));
    sessionStorage.setItem("uploadedFilesCount", files.length.toString());

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
