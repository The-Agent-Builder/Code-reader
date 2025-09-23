import { useState, useEffect } from 'react';
import { FileProcessor } from '../utils/fileProcessor';

interface MemoryInfo {
  used: number;
  total: number;
  percentage: number;
}

export default function MemoryMonitor() {
  const [memoryInfo, setMemoryInfo] = useState<MemoryInfo | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const updateMemoryInfo = () => {
      const usage = FileProcessor.getMemoryUsage();
      if (usage) {
        setMemoryInfo({
          used: usage.used,
          total: usage.total,
          percentage: Math.round(usage.used / usage.total * 100)
        });
      }
    };

    // 初始更新
    updateMemoryInfo();

    // 定期更新
    const interval = setInterval(updateMemoryInfo, 2000);

    return () => clearInterval(interval);
  }, []);

  if (!memoryInfo) return null;

  const getColorClass = (percentage: number) => {
    if (percentage < 50) return 'text-green-600 bg-green-100';
    if (percentage < 80) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {!isVisible ? (
        <button
          onClick={() => setIsVisible(true)}
          className="bg-gray-800 text-white px-3 py-2 rounded-lg text-sm hover:bg-gray-700"
        >
          内存监控
        </button>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 min-w-[200px]">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-medium text-gray-900">内存使用</h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          
          <div className="space-y-2">
            <div className={`px-2 py-1 rounded text-xs ${getColorClass(memoryInfo.percentage)}`}>
              {memoryInfo.percentage}% 使用中
            </div>
            
            <div className="text-xs text-gray-600">
              <div>已用: {FileProcessor.formatFileSize(memoryInfo.used)}</div>
              <div>总计: {FileProcessor.formatFileSize(memoryInfo.total)}</div>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  memoryInfo.percentage < 50 ? 'bg-green-500' :
                  memoryInfo.percentage < 80 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${memoryInfo.percentage}%` }}
              />
            </div>
            
            <button
              onClick={() => {
                FileProcessor.forceGarbageCollection();
                setTimeout(() => {
                  const usage = FileProcessor.getMemoryUsage();
                  if (usage) {
                    setMemoryInfo({
                      used: usage.used,
                      total: usage.total,
                      percentage: Math.round(usage.used / usage.total * 100)
                    });
                  }
                }, 100);
              }}
              className="w-full bg-blue-500 text-white text-xs py-1 px-2 rounded hover:bg-blue-600"
            >
              清理内存
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
