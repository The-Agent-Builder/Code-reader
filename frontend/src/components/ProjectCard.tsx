import { useNavigate } from "react-router-dom";
import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader } from "./ui/card";
import {
    Folder,
    Calendar,
    Clock,
    CheckCircle,
    XCircle,
    AlertCircle,
    User,
} from "lucide-react";
import { RepositoryListItem } from "../services/api";

interface ProjectCardProps {
    repository: RepositoryListItem;
}

export default function ProjectCard({ repository }: ProjectCardProps) {
    const navigate = useNavigate();

    const handleClick = () => {
        navigate(`/result/${repository.id}`);
    };

    const getStatusBadge = () => {
        if (repository.status === 1) {
            return (
                <Badge
                    variant="default"
                    className="bg-green-100 text-green-800 hover:bg-green-100"
                >
                    <CheckCircle className="w-3 h-3 mr-1" />
                    正常
                </Badge>
            );
        } else {
            return (
                <Badge
                    variant="destructive"
                    className="bg-red-100 text-red-800 hover:bg-red-100"
                >
                    <XCircle className="w-3 h-3 mr-1" />
                    已删除
                </Badge>
            );
        }
    };

    const getTaskStatusInfo = () => {
        if (!repository.tasks || repository.tasks.length === 0) {
            return null;
        }

        const latestTask = repository.tasks[0]; // 假设任务按时间排序
        const statusMap = {
            pending: { text: "等待中", color: "text-yellow-600", icon: Clock },
            running: { text: "分析中", color: "text-blue-600", icon: Clock },
            completed: {
                text: "已完成",
                color: "text-green-600",
                icon: CheckCircle,
            },
            failed: { text: "失败", color: "text-red-600", icon: XCircle },
        };

        const status =
            statusMap[latestTask.status as keyof typeof statusMap] ||
            statusMap.pending;
        const StatusIcon = status.icon;

        return (
            <div className={`flex items-center text-sm ${status.color}`}>
                <StatusIcon className="w-4 h-4 mr-1" />
                最新任务: {status.text}
            </div>
        );
    };

    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString("zh-CN", {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return dateString;
        }
    };

    return (
        <Card
            className="cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] border border-gray-200 hover:border-blue-300"
            onClick={handleClick}
        >
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <Folder className="w-5 h-5 text-blue-600 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                            <h3
                                className="font-semibold text-gray-900 truncate"
                                title={repository.name}
                            >
                                {repository.name}
                            </h3>
                        </div>
                    </div>
                    {getStatusBadge()}
                </div>
            </CardHeader>

            <CardContent className="pt-0">
                <div className="space-y-3">
                    {/* 任务状态信息 */}
                    {getTaskStatusInfo()}

                    {/* 统计信息 */}
                    {repository.total_tasks !== undefined && (
                        <div className="flex items-center text-sm text-gray-600">
                            <User className="w-4 h-4 mr-1" />共{" "}
                            {repository.total_tasks} 个分析任务
                        </div>
                    )}

                    {/* 时间信息 */}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            创建: {formatDate(repository.created_at)}
                        </div>
                        <div className="flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            更新: {formatDate(repository.updated_at)}
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
