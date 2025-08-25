import { useNavigate, useOutletContext } from "react-router-dom";
import UploadPageComponent from "../components/UploadPage";

interface AnalysisConfiguration {
  mode: "overall" | "individual";
  selectedFiles: string[];
}

interface OutletContext {
  totalAnalyzedProjects: number;
}

export default function UploadPage() {
  const navigate = useNavigate();
  const { totalAnalyzedProjects } = useOutletContext<OutletContext>();

  const handleStartAnalysis = (config: AnalysisConfiguration) => {
    // 将配置信息存储到sessionStorage或状态管理中
    sessionStorage.setItem('analysisConfig', JSON.stringify(config));
    navigate('/analysis');
  };

  return (
    <UploadPageComponent
      onStartAnalysis={handleStartAnalysis}
      totalAnalyzedProjects={totalAnalyzedProjects}
    />
  );
}
