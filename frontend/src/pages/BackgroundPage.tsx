import { useNavigate, useOutletContext } from "react-router-dom";

interface OutletContext {
  onAnalysisComplete: () => void;
}

export default function BackgroundPage() {
  const navigate = useNavigate();
  const { onAnalysisComplete } = useOutletContext<OutletContext>();

  const handleBackToUpload = () => {
    navigate('/upload');
  };

  return (
    <div className="h-full flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="space-y-4">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
            <svg
              className="w-8 h-8 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">
            分析正在后台进行
          </h2>
          <p className="text-gray-600">
            我们会在分析完成后通过邮箱通知您。您现在可以安全地关闭此页面。
          </p>
        </div>

        <div className="space-y-3">
          <button
            onClick={onAnalysisComplete}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors"
          >
            模拟分析完成（演示用）
          </button>

          <button
            onClick={handleBackToUpload}
            className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-lg transition-colors"
          >
            返回首页
          </button>
        </div>

        <div className="text-xs text-gray-500">
          <p>采用本地AI模型分析，数据不出域，安全无忧</p>
        </div>
      </div>
    </div>
  );
}
