import { useState, useEffect } from "react";
import { Progress } from "./ui/progress";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card } from "./ui/card";
import {
  Brain,
  Search,
  FileText,
  Network,
  Clock,
  Mail,
  Users,
  X,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";

interface AnalysisConfiguration {
  mode: "overall" | "individual";
  selectedFiles: string[];
}

interface AnalysisProgressProps {
  onComplete: () => void;
  onBackgroundMode?: () => void;
  analysisConfig: AnalysisConfiguration;
}

const analysisSteps = [
  { icon: Search, label: "扫描代码文件", duration: 1000 },
  { icon: Brain, label: "分析数据模型", duration: 1500 },
  { icon: Network, label: "构建调用图谱", duration: 2000 },
  { icon: FileText, label: "生成文档结构", duration: 1200 },
];

export default function AnalysisProgress({
  onComplete,
  onBackgroundMode,
  analysisConfig,
}: AnalysisProgressProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [email, setEmail] = useState("");
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [emailSubmitted, setEmailSubmitted] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);

  // 模拟队列数据
  const [queueData] = useState({
    position: Math.floor(Math.random() * 8) + 3, // 随机生成3-10的队列位置
    estimatedTime: Math.floor(Math.random() * 25) + 15, // 随机生成15-40分钟的预估时间
    totalInQueue: Math.floor(Math.random() * 20) + 15, // 随机生成15-35的总队列人数
  });

  useEffect(() => {
    let totalDuration = 0;
    let stepProgress = 0;

    const runStep = (stepIndex: number) => {
      if (stepIndex >= analysisSteps.length) {
        setProgress(100);
        setIsCompleted(true);
        return;
      }

      setCurrentStep(stepIndex);
      const step = analysisSteps[stepIndex];
      const stepStart = stepProgress;
      const stepEnd = stepProgress + (step.duration / 5700) * 100; // Total 5.7s

      const startTime = Date.now();
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const stepProgressPercent = Math.min(elapsed / step.duration, 1);
        const currentProgress =
          stepStart + (stepEnd - stepStart) * stepProgressPercent;

        setProgress(currentProgress);

        if (stepProgressPercent < 1) {
          requestAnimationFrame(animate);
        } else {
          stepProgress = stepEnd;
          setTimeout(() => runStep(stepIndex + 1), 200);
        }
      };

      requestAnimationFrame(animate);
    };

    const timer = setTimeout(() => runStep(0), 500);
    return () => clearTimeout(timer);
  }, [onComplete]);

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setEmailSubmitted(true);
      // 这里可以添加实际的邮箱通知逻辑
      console.log("Email submitted:", email);

      // 开始3秒倒计时
      setCountdown(3);
      const countdownInterval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(countdownInterval);
            if (onBackgroundMode) {
              onBackgroundMode();
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) {
      return `约 ${minutes} 分钟`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `约 ${hours} 小时 ${mins} 分钟`;
  };

  return (
    <div className="h-full flex flex-col items-center justify-center p-8 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-md w-full space-y-8">
        {/* 分析配置信息卡片 */}
        <Card className="p-6">
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Brain className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">分析配置</h3>
                <p className="text-sm text-gray-600">
                  {analysisConfig.mode === "overall"
                    ? "代码整体分析"
                    : "代码逐个解析"}
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">分析模式</span>
                <span className="font-medium">
                  {analysisConfig.mode === "overall" ? "整体架构" : "逐个解析"}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">文件数量</span>
                <span className="font-medium">
                  {analysisConfig.selectedFiles.length} 个
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* 队列状态卡片 - 只在未完成时显示 */}
        {!isCompleted && (
          <Card className="p-6">
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Clock className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">分析队列状态</h3>
                  <p className="text-sm text-gray-600">当前系统较为繁忙</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="space-y-1">
                  <div className="text-2xl font-bold text-blue-600">
                    #{queueData.position}
                  </div>
                  <div className="text-xs text-gray-500">队列位置</div>
                </div>
                <div className="space-y-1">
                  <div className="text-2xl font-bold text-green-600">
                    {queueData.estimatedTime}分
                  </div>
                  <div className="text-xs text-gray-500">预估时间</div>
                </div>
                <div className="space-y-1">
                  <div className="text-2xl font-bold text-purple-600">
                    {queueData.totalInQueue}
                  </div>
                  <div className="text-xs text-gray-500">排队人数</div>
                </div>
              </div>

              <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <div className="flex items-start space-x-2">
                  <Users className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm">
                    <p className="text-yellow-800 font-medium">分析队列较长</p>
                    <p className="text-yellow-700">
                      预计需要等待 {formatTime(queueData.estimatedTime)}
                      ，您可以留下邮箱后离开
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* 主要内容区 */}
        <div className="text-center space-y-6">
          {/* 分析完成状态 */}
          {isCompleted ? (
            <div className="space-y-6">
              <Card className="p-6 bg-green-50 border-green-200">
                <div className="flex flex-col items-center space-y-4">
                  <div className="p-3 bg-green-100 rounded-full">
                    <CheckCircle2 className="h-8 w-8 text-green-600" />
                  </div>
                  <div className="text-center">
                    <h3 className="text-xl font-bold text-green-800 mb-2">
                      分析完成！
                    </h3>
                    <p className="text-green-700">
                      您的代码分析已经完成，现在可以查看详细的分析结果了。
                    </p>
                  </div>
                </div>
              </Card>

              <Button
                onClick={onComplete}
                className="w-full py-3 text-lg"
                size="lg"
              >
                <ArrowRight className="h-5 w-5 mr-2" />
                查看分析结果
              </Button>
            </div>
          ) : (
            <div>
              <div className="space-y-4">
                <p className="text-gray-600">分析完成后我们会通过邮箱通知您</p>
              </div>

              {/* 邮箱通知区域 */}
              {!emailSubmitted ? (
                <div className="space-y-4">
                  {!showEmailForm ? (
                    <Button
                      onClick={() => setShowEmailForm(true)}
                      className="w-full"
                      variant="outline"
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      留下邮箱，完成后通知我
                    </Button>
                  ) : (
                    <Card className="p-4">
                      <form onSubmit={handleEmailSubmit} className="space-y-4">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium text-gray-900">
                            邮箱通知
                          </h4>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowEmailForm(false)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>

                        <div className="space-y-3">
                          <Input
                            type="email"
                            placeholder="输入您的邮箱地址"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            className="w-full"
                          />
                          <p className="text-xs text-gray-500">
                            我们会在分析完成后第一时间通知您，不会发送其他邮件
                          </p>
                        </div>

                        <Button type="submit" className="w-full">
                          <Mail className="h-4 w-4 mr-2" />
                          确认并后台运行
                        </Button>
                      </form>
                    </Card>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  <Card className="p-4 bg-green-50 border-green-200">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-green-100 rounded-full">
                        <Mail className="h-4 w-4 text-green-600" />
                      </div>
                      <div className="text-left">
                        <p className="font-medium text-green-800">
                          邮箱通知已设置
                        </p>
                        <p className="text-sm text-green-600">
                          将发送到: {email}
                        </p>
                      </div>
                    </div>
                  </Card>

                  {countdown > 0 && (
                    <Card className="p-4 bg-blue-50 border-blue-200">
                      <div className="text-center">
                        <p className="text-sm text-blue-800 mb-2">
                          正在切换到后台运行模式...
                        </p>
                        <div className="flex items-center justify-center space-x-2">
                          <div className="w-8 h-8 bg-blue-200 rounded-full flex items-center justify-center">
                            <span className="text-lg font-bold text-blue-700">
                              {countdown}
                            </span>
                          </div>
                          <span className="text-sm text-blue-600">
                            秒后自动跳转
                          </span>
                        </div>
                      </div>
                    </Card>
                  )}
                </div>
              )}

              {/* 进度条和步骤显示 - 只在未完成时显示 */}
              {!isCompleted && (
                <div className="space-y-6">
                  <Progress value={progress} className="h-2" />

                  <div className="space-y-4">
                    {analysisSteps.map((step, index) => {
                      const Icon = step.icon;
                      const isActive = index === currentStep;
                      const isStepCompleted =
                        index < currentStep ||
                        (index === currentStep && progress === 100);

                      return (
                        <div
                          key={index}
                          className={`
                            flex items-center space-x-3 p-3 rounded-lg transition-all duration-300
                            ${
                              isActive
                                ? "bg-blue-100 text-blue-700"
                                : isStepCompleted
                                ? "bg-green-100 text-green-700"
                                : "bg-gray-50 text-gray-500"
                            }
                          `}
                        >
                          <Icon
                            className={`
                              h-5 w-5
                              ${isActive ? "animate-pulse" : ""}
                            `}
                          />
                          <span className="flex-1 text-left">{step.label}</span>
                          {isStepCompleted && (
                            <span className="text-green-600">✓</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
