import { useEffect, useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import AnalysisProgress from "../components/AnalysisProgress";

interface AnalysisConfiguration {
  mode: "overall" | "individual";
  selectedFiles: string[];
}

interface OutletContext {
  onAnalysisComplete: () => void;
}

export default function AnalysisPage() {
  const navigate = useNavigate();
  const { onAnalysisComplete } = useOutletContext<OutletContext>();
  const [analysisConfig, setAnalysisConfig] = useState<AnalysisConfiguration | null>(null);

  useEffect(() => {
    // 从sessionStorage获取分析配置
    const configStr = sessionStorage.getItem('analysisConfig');
    if (configStr) {
      setAnalysisConfig(JSON.parse(configStr));
    } else {
      // 如果没有配置，重定向到上传页面
      navigate('/upload');
    }
  }, [navigate]);

  const handleBackgroundMode = () => {
    navigate('/background');
  };

  if (!analysisConfig) {
    return <div>Loading...</div>;
  }

  return (
    <AnalysisProgress
      onComplete={onAnalysisComplete}
      onBackgroundMode={handleBackgroundMode}
      analysisConfig={analysisConfig}
    />
  );
}
