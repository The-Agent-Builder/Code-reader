import { useState } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { ArrowLeft, Clock, FileText, Brain, CheckCircle, AlertCircle, Trash2 } from 'lucide-react';

interface PersonalSpaceProps {
  onBack: () => void;
}

interface AnalysisTask {
  id: string;
  projectName: string;
  status: 'queued' | 'analyzing' | 'completed' | 'failed';
  progress: number;
  queuePosition?: number;
  estimatedTime?: number;
  startTime: Date;
  email?: string;
  fileCount: number;
  currentStep?: string;
}

export default function PersonalSpace({ onBack }: PersonalSpaceProps) {
  // 模拟用户的分析任务数据
  const [tasks] = useState<AnalysisTask[]>([
    {
      id: '1',
      projectName: 'my-awesome-project',
      status: 'completed',
      progress: 100,
      startTime: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2小时前
      fileCount: 156,
      email: 'user@example.com'
    },
    {
      id: '2',
      projectName: 'backend-service',
      status: 'analyzing',
      progress: 65,
      currentStep: '分析数据模型',
      startTime: new Date(Date.now() - 30 * 60 * 1000), // 30分钟前
      fileCount: 89,
      email: 'user@example.com'
    },
    {
      id: '3',
      projectName: 'frontend-app',
      status: 'queued',
      progress: 0,
      queuePosition: 5,
      estimatedTime: 25,
      startTime: new Date(Date.now() - 5 * 60 * 1000), // 5分钟前
      fileCount: 234,
      email: 'user@example.com'
    },
    {
      id: '4',
      projectName: 'microservice-utils',
      status: 'failed',
      progress: 30,
      startTime: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4小时前
      fileCount: 67
    }
  ]);

  const getStatusIcon = (status: AnalysisTask['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'analyzing':
        return <Brain className="h-5 w-5 text-blue-600 animate-pulse" />;
      case 'queued':
        return <Clock className="h-5 w-5 text-orange-600" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
    }
  };

  const getStatusBadge = (status: AnalysisTask['status']) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-700">已完成</Badge>;
      case 'analyzing':
        return <Badge className="bg-blue-100 text-blue-700">分析中</Badge>;
      case 'queued':
        return <Badge className="bg-orange-100 text-orange-700">排队中</Badge>;
      case 'failed':
        return <Badge variant="destructive">分析失败</Badge>;
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return '刚刚';
    if (diffInMinutes < 60) return `${diffInMinutes} 分钟前`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} 小时前`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} 天前`;
  };

  const handleDeleteTask = (taskId: string) => {
    // 这里可以添加删除任务的逻辑
    console.log('删除任务:', taskId);
  };

  const handleViewResult = (taskId: string) => {
    // 这里可以添加查看结果的逻辑
    console.log('查看结果:', taskId);
    onBack(); // 返回到DeepWiki界面
  };

  return (
    <div className="h-full bg-gray-50">
      {/* Main Content */}
      <div className="w-full p-6">
        <div className="space-y-6">
          {/* 统计概览 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">总任务数</p>
                  <p className="text-2xl font-bold text-gray-900">{tasks.length}</p>
                </div>
                <FileText className="h-8 w-8 text-gray-400" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">已完成</p>
                  <p className="text-2xl font-bold text-green-600">
                    {tasks.filter(t => t.status === 'completed').length}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-400" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">分析中</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {tasks.filter(t => t.status === 'analyzing').length}
                  </p>
                </div>
                <Brain className="h-8 w-8 text-blue-400" />
              </div>
            </Card>
            
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">排队中</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {tasks.filter(t => t.status === 'queued').length}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-orange-400" />
              </div>
            </Card>
          </div>

          {/* 任务列表 */}
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">分析任务</h2>
            <div className="space-y-4">
              {tasks.map((task) => (
                <Card key={task.id} className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-4 flex-1">
                      <div className="mt-1">
                        {getStatusIcon(task.status)}
                      </div>
                      
                      <div className="flex-1 space-y-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="font-medium text-gray-900">{task.projectName}</h3>
                            <p className="text-sm text-gray-500">
                              {task.fileCount} 个文件 • {formatTimeAgo(task.startTime)}
                            </p>
                          </div>
                          <div className="flex items-center space-x-3">
                            {getStatusBadge(task.status)}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteTask(task.id)}
                            >
                              <Trash2 className="h-4 w-4 text-gray-400" />
                            </Button>
                          </div>
                        </div>

                        {/* 进度信息 */}
                        {task.status === 'analyzing' && (
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">{task.currentStep}</span>
                              <span className="text-gray-600">{task.progress}%</span>
                            </div>
                            <Progress value={task.progress} className="h-2" />
                          </div>
                        )}

                        {/* 队列信息 */}
                        {task.status === 'queued' && (
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span>队列位置: #{task.queuePosition}</span>
                            <span>预估时间: {task.estimatedTime} 分钟</span>
                            {task.email && (
                              <span>邮箱通知: {task.email}</span>
                            )}
                          </div>
                        )}

                        {/* 完成状态 */}
                        {task.status === 'completed' && (
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-green-600">分析完成，可以查看结果</span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleViewResult(task.id)}
                            >
                              查看结果
                            </Button>
                          </div>
                        )}

                        {/* 失败状态 */}
                        {task.status === 'failed' && (
                          <div className="space-y-2">
                            <p className="text-sm text-red-600">
                              分析失败：代码库结构不支持或文件格式错误
                            </p>
                            <Button variant="outline" size="sm">
                              重新分析
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {tasks.length === 0 && (
            <Card className="p-12 text-center">
              <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">还没有分析任务</h3>
              <p className="text-gray-600 mb-4">上传您的第一个代码库开始分析</p>
              <Button onClick={onBack}>
                开始分析
              </Button>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}