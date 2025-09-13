import { useNavigate, useOutletContext } from "react-router-dom";
import UploadPageComponent from "../components/UploadPage";

interface OutletContext {
  totalAnalyzedProjects: number;
}

export default function UploadPage() {
  const navigate = useNavigate();
  const { totalAnalyzedProjects } = useOutletContext<OutletContext>();

  const handleNextStep = async (files: FileList) => {
    // 读取文件内容并存储到sessionStorage，供配置页面使用
    const filesInfo = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        // 读取文件内容
        const content = await file.arrayBuffer();
        const base64Content = btoa(
          String.fromCharCode(...new Uint8Array(content))
        );

        filesInfo.push({
          name: file.name,
          size: file.size,
          type: file.type,
          lastModified: file.lastModified,
          webkitRelativePath: (file as any).webkitRelativePath || "",
          content: base64Content, // 添加base64编码的文件内容
        });
      } catch (error) {
        console.error(`读取文件失败 ${file.name}:`, error);
        // 如果读取失败，仍然保存文件信息但不包含内容
        filesInfo.push({
          name: file.name,
          size: file.size,
          type: file.type,
          lastModified: file.lastModified,
          webkitRelativePath: (file as any).webkitRelativePath || "",
          content: "", // 空内容
        });
      }
    }

    // 调试：打印原始文件信息
    console.log("UploadPage: 原始文件信息:", files);
    console.log(
      "UploadPage: 序列化的文件信息（含内容）:",
      filesInfo.map((f) => ({
        name: f.name,
        size: f.size,
        contentLength: f.content.length,
      }))
    );

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
