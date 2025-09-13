import { useState, useEffect } from "react";
import {
  ChevronDown,
  ChevronRight,
  BarChart3,
  Network,
  Layers,
  FileText,
  Loader2,
} from "lucide-react";
import { Button } from "./ui/button";
import { api } from "../services/api";

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  taskId?: number | null;
}

interface MarkdownSection {
  id: string;
  title: string;
  level: number;
  children?: MarkdownSection[];
}

// 解析markdown内容，提取标题结构
const parseMarkdownHeadings = (content: string): MarkdownSection[] => {
  const lines = content.split("\n");
  const sections: MarkdownSection[] = [];
  const stack: MarkdownSection[] = [];
  let inCodeBlock = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmedLine = line.trim();

    // 检查是否在代码块中
    if (trimmedLine.startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      continue;
    }

    // 如果在代码块中，跳过这一行
    if (inCodeBlock) {
      continue;
    }

    // 更严格的标题匹配：确保 # 后面有空格，且不在行首有其他字符
    const h1Match = line.match(/^# (.+)$/);
    const h2Match = line.match(/^## (.+)$/);

    if (h1Match) {
      const title = h1Match[1].trim();

      // 过滤掉一些明显不是标题的内容
      if (isValidTitle(title)) {
        const id = generateSectionId(title);

        const section: MarkdownSection = {
          id,
          title,
          level: 1,
          children: [],
        };

        sections.push(section);
        stack.length = 0;
        stack.push(section);
      }
    } else if (h2Match && stack.length > 0) {
      const title = h2Match[1].trim();

      if (isValidTitle(title)) {
        const id = generateSectionId(title);

        const section: MarkdownSection = {
          id,
          title,
          level: 2,
        };

        const parent = stack[stack.length - 1];
        if (parent && parent.children) {
          parent.children.push(section);
        }
      }
    }
  }

  return sections;
};

// 验证是否是有效的标题
const isValidTitle = (title: string): boolean => {
  // 过滤掉空标题
  if (!title || title.trim().length === 0) {
    return false;
  }

  // 过滤掉只包含特殊字符的标题
  if (/^[#\-=\*\s]+$/.test(title)) {
    return false;
  }

  // 过滤掉看起来像代码或URL的内容
  if (
    title.includes("://") ||
    title.includes("```") ||
    title.startsWith("http")
  ) {
    return false;
  }

  // 过滤掉过长的标题（可能是误识别的内容）
  if (title.length > 100) {
    return false;
  }

  return true;
};

// 生成标题ID
const generateSectionId = (title: string): string => {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5\s]/g, "")
    .replace(/\s+/g, "-")
    .replace(/^-+|-+$/g, ""); // 移除开头和结尾的连字符
};

export function Sidebar({
  activeSection,
  onSectionChange,
  taskId,
}: SidebarProps) {
  const [markdownSections, setMarkdownSections] = useState<MarkdownSection[]>(
    []
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set()
  );

  // 加载README文档
  const loadReadmeContent = async (taskId: number) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log("Loading README for task:", taskId);
      const response = await api.getTaskReadmeByTaskId(taskId);

      if (response.status === "success" && response.readme) {
        const sections = parseMarkdownHeadings(response.readme.content);
        setMarkdownSections(sections);
        console.log("Parsed markdown sections:", sections);
      } else {
        setError("未找到README文档");
        setMarkdownSections([]);
      }
    } catch (err) {
      console.error("Error loading README:", err);
      setError("加载README文档失败");
      setMarkdownSections([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 当taskId改变时加载README
  useEffect(() => {
    if (taskId) {
      loadReadmeContent(taskId);
    } else {
      setMarkdownSections([]);
    }
  }, [taskId]);

  // 切换展开状态
  const toggleExpanded = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  // 渲染markdown导航项
  const renderMarkdownSection = (section: MarkdownSection) => {
    const isExpanded = expandedSections.has(section.id);
    const hasChildren = section.children && section.children.length > 0;

    return (
      <div key={section.id} className="space-y-1">
        <Button
          variant="ghost"
          className={`
            w-full justify-start px-2 py-1 h-auto
            ${
              activeSection === section.id
                ? "bg-blue-100 text-blue-700"
                : "text-gray-700 hover:bg-gray-100"
            }
          `}
          onClick={() => {
            onSectionChange(section.id);
            if (hasChildren) {
              toggleExpanded(section.id);
            }
          }}
        >
          <FileText className="h-4 w-4 mr-2" />
          <span className="text-sm flex-1 text-left">{section.title}</span>
          {hasChildren &&
            (isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            ))}
        </Button>

        {isExpanded && hasChildren && (
          <div className="ml-6 space-y-1">
            {section.children!.map((child) => (
              <Button
                key={child.id}
                variant="ghost"
                className={`
                  w-full justify-start px-2 py-1 h-auto text-sm
                  ${
                    activeSection === child.id
                      ? "bg-blue-50 text-blue-600"
                      : "text-gray-600 hover:bg-gray-50"
                  }
                `}
                onClick={() => onSectionChange(child.id)}
              >
                {child.title}
              </Button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <nav className="p-4 space-y-2">
      {/* 项目概览 - 固定显示 */}
      <div className="space-y-1">
        <Button
          variant="ghost"
          className={`
            w-full justify-start px-2 py-1 h-auto
            ${
              activeSection === "overview"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-700 hover:bg-gray-100"
            }
          `}
          onClick={() => onSectionChange("overview")}
        >
          <BarChart3 className="h-4 w-4 mr-2" />
          <span className="text-sm">项目概览</span>
        </Button>
      </div>

      {/* 分隔线 */}
      {markdownSections.length > 0 && (
        <div className="border-t border-gray-200 my-3"></div>
      )}

      {/* 加载状态 */}
      {isLoading && (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
          <span className="ml-2 text-sm text-gray-500">加载文档中...</span>
        </div>
      )}

      {/* 错误状态 */}
      {error && <div className="text-sm text-red-500 py-2 px-2">{error}</div>}

      {/* Markdown导航 */}
      {markdownSections.map(renderMarkdownSection)}
    </nav>
  );
}
