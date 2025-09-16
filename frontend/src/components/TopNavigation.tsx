import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "./ui/tooltip";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { useAuth } from "../contexts/ProjectContext";
import {
    Brain,
    User,
    Home,
    Upload,
    RotateCcw,
    Settings,
    HelpCircle,
    LogOut,
    UserCircle,
    History,
    Bell,
    ChevronDown,
    Clock,
    GitBranch,
    MessageCircle,
} from "lucide-react";

interface ProjectVersion {
    id: string;
    name: string;
    date: string;
    isCurrent: boolean;
}

interface TopNavigationProps {
    currentPage:
        | "upload"
        | "config"
        | "analyzing"
        | "deepwiki"
        | "background"
        | "profile"
        | "chat";
    onNavigate: (
        page:
            | "upload"
            | "analyzing"
            | "deepwiki"
            | "background"
            | "profile"
            | "chat"
    ) => void;
    projectName?: string;
    showProfileBadge?: boolean;
    projectVersions?: ProjectVersion[];
    currentVersionId?: string;
    onVersionChange?: (versionId: string) => void;
}

export default function TopNavigation({
    currentPage,
    onNavigate,
    projectName,
    showProfileBadge = false,
    projectVersions = [],
    currentVersionId,
    onVersionChange,
}: TopNavigationProps) {
    const { logout } = useAuth();

    const handleLogout = () => {
        logout();
        // 登出后重新加载页面，这样会触发认证检查
        window.location.reload();
    };
    const getPageTitle = () => {
        switch (currentPage) {
            case "upload":
                return "AI 代码库领航员";
            case "config":
                return "分析配置";
            case "analyzing":
                return "代码分析中";
            case "background":
                return "后台运行";
            case "deepwiki":
                return projectName ? `项目：${projectName}` : "项目文档";
            case "profile":
                return "用户中心";
            case "chat":
                return "AI 助手对话";
            default:
                return "AI 代码库领航员";
        }
    };

    const canNavigateToProfile = () => {
        return currentPage !== "analyzing"; // 除了分析页面，所有页面都可以访问用户中心
    };

    const canNavigateToHome = () => {
        return currentPage !== "upload";
    };

    const getCurrentVersion = () => {
        return (
            projectVersions.find((v) => v.id === currentVersionId) ||
            projectVersions[0]
        );
    };

    const formatVersionDate = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInDays = Math.floor(
            (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24)
        );

        if (diffInDays === 0) {
            return "今天";
        } else if (diffInDays === 1) {
            return "昨天";
        } else if (diffInDays < 7) {
            return `${diffInDays}天前`;
        } else {
            return date.toLocaleDateString("zh-CN", {
                month: "short",
                day: "numeric",
            });
        }
    };

    return (
        <TooltipProvider>
            <header className="border-b border-border bg-background px-6 py-4 sticky top-0 z-50">
                <div className="flex items-center justify-between w-full">
                    {/* Left section - Brand and current page */}
                    <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-2">
                            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                                <Brain className="h-5 w-5 text-primary-foreground" />
                            </div>
                            <div>
                                <h1 className="text-lg font-medium text-foreground">
                                    {getPageTitle()}
                                </h1>
                                {currentPage === "analyzing" && (
                                    <p className="text-sm text-muted-foreground">
                                        正在本地处理，您的代码安全无忧
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* Status indicators */}
                        {currentPage === "analyzing" && (
                            <Badge
                                variant="secondary"
                                className="animate-pulse"
                            >
                                <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                                分析中
                            </Badge>
                        )}

                        {currentPage === "background" && (
                            <Badge variant="secondary">
                                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                                后台运行
                            </Badge>
                        )}

                        {/* Version indicator for deepwiki and chat page */}
                        {(currentPage === "deepwiki" ||
                            currentPage === "chat") &&
                            projectVersions.length > 0 &&
                            getCurrentVersion() && (
                                <Badge variant="outline" className="text-xs">
                                    <GitBranch className="h-3 w-3 mr-1" />
                                    {getCurrentVersion()?.name}
                                </Badge>
                            )}
                    </div>

                    {/* Right section - Navigation actions */}
                    <div className="flex items-center space-x-3">
                        {/* Home button */}
                        {canNavigateToHome() && (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => onNavigate("upload")}
                                    >
                                        <Home className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>返回首页</p>
                                </TooltipContent>
                            </Tooltip>
                        )}

                        {/* Upload new project button (when not on upload page) */}
                        {currentPage !== "upload" &&
                            currentPage !== "analyzing" &&
                            currentPage !== "chat" && (
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => onNavigate("upload")}
                                        >
                                            <Upload className="h-4 w-4 mr-2" />
                                            新建分析
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>上传新的代码库进行分析</p>
                                    </TooltipContent>
                                </Tooltip>
                            )}

                        {/* Chat button (when on deepwiki page) */}
                        {currentPage === "deepwiki" && (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => onNavigate("chat")}
                                        className="flex items-center space-x-2"
                                    >
                                        <MessageCircle className="h-4 w-4" />
                                        <span className="hidden md:inline">
                                            AI 助手
                                        </span>
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>与AI助手对话，深入了解代码库</p>
                                </TooltipContent>
                            </Tooltip>
                        )}

                        {/* Chat page navigation */}
                        {currentPage === "chat" && (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => onNavigate("deepwiki")}
                                    >
                                        <Brain className="h-4 w-4 mr-2" />
                                        返回文档
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>返回项目文档</p>
                                </TooltipContent>
                            </Tooltip>
                        )}

                        {/* Version selector and Refresh button (when on deepwiki or chat page) */}
                        {(currentPage === "deepwiki" ||
                            currentPage === "chat") && (
                            <div className="flex items-center space-x-2">
                                {/* Version selector */}
                                {projectVersions.length > 0 &&
                                    onVersionChange && (
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="flex items-center space-x-2"
                                                >
                                                    <History className="h-4 w-4" />
                                                    <span className="hidden md:inline text-sm">
                                                        版本历史
                                                    </span>
                                                    <ChevronDown className="h-3 w-3" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent
                                                align="end"
                                                className="w-72"
                                            >
                                                <DropdownMenuLabel className="flex items-center space-x-2">
                                                    <GitBranch className="h-4 w-4" />
                                                    <span>项目版本历史</span>
                                                </DropdownMenuLabel>
                                                <DropdownMenuSeparator />

                                                {projectVersions.map(
                                                    (version) => (
                                                        <DropdownMenuItem
                                                            key={version.id}
                                                            onClick={() =>
                                                                onVersionChange(
                                                                    version.id
                                                                )
                                                            }
                                                            className={`flex items-center justify-between space-x-3 cursor-pointer py-3 ${
                                                                version.id ===
                                                                currentVersionId
                                                                    ? "bg-blue-50 text-blue-700"
                                                                    : ""
                                                            }`}
                                                        >
                                                            <div className="flex items-center space-x-3">
                                                                <div
                                                                    className={`w-2 h-2 rounded-full ${
                                                                        version.id ===
                                                                        currentVersionId
                                                                            ? "bg-blue-500"
                                                                            : "bg-gray-300"
                                                                    }`}
                                                                />
                                                                <div className="flex-1">
                                                                    <div className="flex items-center space-x-2">
                                                                        <span className="font-medium">
                                                                            {
                                                                                version.name
                                                                            }
                                                                        </span>
                                                                        {version.isCurrent && (
                                                                            <Badge
                                                                                variant="secondary"
                                                                                className="text-xs"
                                                                            >
                                                                                当前
                                                                            </Badge>
                                                                        )}
                                                                    </div>
                                                                    <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                                                                        <Clock className="h-3 w-3" />
                                                                        <span>
                                                                            {formatVersionDate(
                                                                                version.date
                                                                            )}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </DropdownMenuItem>
                                                    )
                                                )}

                                                <DropdownMenuSeparator />
                                                <DropdownMenuItem
                                                    onClick={() =>
                                                        onNavigate("upload")
                                                    }
                                                    className="text-blue-600 hover:text-blue-700 cursor-pointer"
                                                >
                                                    <Upload className="h-4 w-4 mr-2" />
                                                    创建新版本
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    )}

                                {/* Refresh/Restart analysis button */}
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => onNavigate("upload")}
                                        >
                                            <RotateCcw className="h-4 w-4 mr-2" />
                                            重新分析
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>重新分析当前项目</p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                        )}

                        {/* User Center Dropdown */}
                        {canNavigateToProfile() && (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <div className="relative">
                                        <Button
                                            variant={
                                                currentPage === "profile"
                                                    ? "secondary"
                                                    : "ghost"
                                            }
                                            size="sm"
                                            className="flex items-center space-x-2 px-3"
                                        >
                                            <Avatar className="h-6 w-6">
                                                <AvatarFallback className="text-xs bg-primary text-primary-foreground">
                                                    用
                                                </AvatarFallback>
                                            </Avatar>
                                            <span className="hidden md:inline text-sm">
                                                用户中心
                                            </span>
                                        </Button>

                                        {/* Notification badge */}
                                        {showProfileBadge && (
                                            <div className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full border-2 border-background"></div>
                                        )}
                                    </div>
                                </DropdownMenuTrigger>

                                <DropdownMenuContent
                                    align="end"
                                    className="w-56"
                                >
                                    <DropdownMenuLabel className="flex items-center space-x-2">
                                        <Avatar className="h-8 w-8">
                                            <AvatarFallback className="text-sm bg-primary text-primary-foreground">
                                                用
                                            </AvatarFallback>
                                        </Avatar>
                                        <div>
                                            <p className="font-medium">用户</p>
                                            <p className="text-xs text-muted-foreground">
                                                user@example.com
                                            </p>
                                        </div>
                                    </DropdownMenuLabel>

                                    <DropdownMenuSeparator />

                                    <DropdownMenuItem
                                        onClick={() => onNavigate("profile")}
                                        className="flex items-center space-x-2 cursor-pointer"
                                    >
                                        <UserCircle className="h-4 w-4" />
                                        <span>个人空间</span>
                                        {showProfileBadge && (
                                            <Badge
                                                variant="secondary"
                                                className="ml-auto"
                                            >
                                                <Bell className="h-3 w-3 mr-1" />
                                                新
                                            </Badge>
                                        )}
                                    </DropdownMenuItem>

                                    <DropdownMenuItem className="flex items-center space-x-2 cursor-pointer">
                                        <History className="h-4 w-4" />
                                        <span>分析历史</span>
                                    </DropdownMenuItem>

                                    <DropdownMenuItem className="flex items-center space-x-2 cursor-pointer">
                                        <Settings className="h-4 w-4" />
                                        <span>设置</span>
                                    </DropdownMenuItem>

                                    <DropdownMenuItem className="flex items-center space-x-2 cursor-pointer">
                                        <HelpCircle className="h-4 w-4" />
                                        <span>帮助与反馈</span>
                                    </DropdownMenuItem>

                                    <DropdownMenuSeparator />

                                    <DropdownMenuItem
                                        className="flex items-center space-x-2 cursor-pointer text-destructive focus:text-destructive"
                                        onClick={handleLogout}
                                    >
                                        <LogOut className="h-4 w-4" />
                                        <span>退出登录</span>
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        )}
                    </div>
                </div>
            </header>
        </TooltipProvider>
    );
}
