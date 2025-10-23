import React, {
  useState,
  useEffect,
  useLayoutEffect,
  Children,
  isValidElement,
  memo,
  useMemo,
  useRef,
  useCallback,
  Component,
} from "react";
import type { ReactNode } from "react";
import ReactDOMServer from "react-dom/server";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { findFileInTree, FileNode, normalizePath } from "../utils/fileTree";
import { MermaidBlock } from "./MermaidBlock";
import { SvgWithFullscreen } from "./SvgWithFullscreen";
import { useSvgPanZoom } from "../hooks/useSvgPanZoom";
import { PaginatedContent, getContentBySectionId } from "../utils/markdownPagination";
import { preprocessMermaidInMarkdown, hasMermaidBlocks } from "../utils/mermaidPreprocessor";

interface TaskStatistics {
  code_lines: number;
  total_files: number;
  module_count: number;
}

// 简化的错误处理组件
const MarkdownErrorBoundary = ({ children }: { children: ReactNode }) => {
  try {
    return <>{children}</>;
  } catch (error) {
    console.error("Markdown rendering error:", error);
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-medium mb-2">内容渲染错误</h3>
          <p className="text-red-600 text-sm">
            抱歉，内容渲染时出现了错误。请尝试刷新页面或联系管理员。
          </p>
        </div>
      </div>
    );
  }
};

interface MainContentProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  onFileSelect: (file: string) => void;
  onFileHighlight: (file: string) => void; // 新增：文件高亮回调
  fileTree: FileNode | null; // 新增：文件树数据
  projectName?: string;
  taskStatistics?: TaskStatistics | null;
  taskId?: number | null;
  processedReadmeContent?: string; // 新增：预处理后的README内容
  paginatedContent?: PaginatedContent[]; // 新增：分页后的内容
}

// 生成标题ID（与Sidebar中的逻辑保持一致）
const generateSectionId = (title: string): string => {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5\s-]/g, "") // 保留连字符
    .replace(/\s+/g, "-")
    .replace(/^-+|-+$/g, ""); // 移除开头和结尾的连字符
};

// 生成稳定的key
const generateStableKey = (content: string, type: string): string => {
  // 使用内容的简单哈希作为key的基础
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    const char = content.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // 转换为32位整数
  }
  return `${type}-${Math.abs(hash).toString(36)}`;
};

const getNodeText = (node: ReactNode): string => {
  if (typeof node === "string" || typeof node === "number") {
    return String(node);
  }

  if (Array.isArray(node)) {
    return node.map((child) => getNodeText(child)).join("");
  }

  if (isValidElement(node)) {
    return getNodeText(node.props?.children);
  }

  return "";
};

const processHeadingChildren = (children: ReactNode) => {
  const childArray = Children.toArray(children);
  let customId: string | undefined;

  const sanitizedChildren = childArray
    .map((child) => {
      if (typeof child === "string") {
        const match = child.match(/^(.*?)(?:\s*\{#([A-Za-z0-9_-]+)\})\s*$/);
        if (match) {
          customId = match[2];
          const textPart = match[1]?.trimEnd();
          return textPart ? textPart : null;
        }
      }
      return child;
    })
    .filter((child) => child !== null && child !== undefined) as ReactNode[];

  const textContent = sanitizedChildren.map((child) => getNodeText(child)).join("").trim();

  return {
    sanitizedChildren,
    textContent,
    customId,
  };
};

// 将自定义 markdown 组件提取到外部，避免重复创建
// 使用 useMemo 缓存这个配置对象，避免每次渲染都重新创建
const createMarkdownComponents = (
  onFileHighlight: (file: string) => void,
  onSectionChange: (section: string) => void,
  fileTree: FileNode | null
) => ({
  details: ({ children, ...props }: any) => (
    <details
      className="border border-gray-200 rounded-md p-3 bg-white shadow-sm open:shadow transition-shadow"
      {...props}
    >
      {children}
    </details>
  ),
  summary: ({ children, ...props }: any) => (
    <summary
      className="cursor-pointer font-medium text-gray-800 mb-2"
      {...props}
    >
      {children}
    </summary>
  ),
  h1: ({ children, ...props }: any) => {
    const { sanitizedChildren, textContent, customId } =
      processHeadingChildren(children);
    const id = customId || generateSectionId(textContent);
    return (
      <h1
        id={id}
        className="text-3xl font-bold text-gray-900 mb-6 border-b border-gray-200 pb-3 scroll-mt-4"
        {...props}
      >
        {sanitizedChildren}
      </h1>
    );
  },
  h2: ({ children, ...props }: any) => {
    const { sanitizedChildren, textContent, customId } =
      processHeadingChildren(children);
    const id = customId || generateSectionId(textContent);
    return (
      <h2
        id={id}
        className="text-2xl font-semibold text-gray-800 mb-4 mt-8 scroll-mt-4"
        {...props}
      >
        {sanitizedChildren}
      </h2>
    );
  },
  h3: ({ children, ...props }: any) => (
    <h3
      className="text-xl font-medium text-gray-700 mb-3 mt-6"
      {...props}
    >
      {children}
    </h3>
  ),
  p: ({ children, ...props }: any) => (
    <p
      className="text-gray-700 leading-relaxed mb-4"
      {...props}
    >
      {children}
    </p>
  ),
  ul: ({ children, ...props }: any) => (
    <ul
      className="list-disc list-inside mb-4 space-y-2 text-gray-700"
      {...props}
    >
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: any) => (
    <ol
      className="list-decimal list-inside mb-4 space-y-2 text-gray-700"
      {...props}
    >
      {children}
    </ol>
  ),
  li: ({ children, ...props }: any) => (
    <li className="ml-4" {...props}>
      {children}
    </li>
  ),
  a: ({ href, children, ...props }: any) => {
    if (!href) {
      return <span {...props}>{children}</span>;
    }

    if (href.startsWith("#")) {
      const sectionId = href.replace(/^#/, "");
      return (
        <a
          href={href}
          className="text-blue-600 hover:text-blue-800 underline font-medium transition-colors"
          onClick={(event) => {
            event.preventDefault();
            if (sectionId) {
              onSectionChange(sectionId);
            }
          }}
          {...props}
        >
          {children}
        </a>
      );
    }

    const normalizedHref = normalizePath(href);
    const fileExists = findFileInTree(fileTree, normalizedHref);

    if (fileExists) {
      return (
        <button
          className="text-blue-600 hover:text-blue-800 underline font-medium transition-colors"
          onClick={() => onFileHighlight(normalizedHref)}
          title={`定位到文件: ${normalizedHref}`}
          {...props}
        >
          {children}
        </button>
      );
    } else {
      return (
        <span
          className="text-gray-500 font-mono text-sm bg-gray-100 px-1 py-0.5 rounded"
          title={`文件不存在: ${normalizedHref}`}
          {...props}
        >
          {children}
        </span>
      );
    }
  },
  code: ({ className, children, ...props }: any) => {
    const language = className?.replace("language-", "");
    
    // 检查是否是已经预处理过的SVG内容
    const content = String(children);
    if (content.includes('<svg') && content.includes('</svg>')) {
      // 使用更安全的方式渲染SVG
      return (
        <div key={generateStableKey(content, 'svg')} className="mermaid-svg-container my-4">
          <SvgWithFullscreen 
            svgContent={content}
            className="w-full"
          />
        </div>
      );
    }
    
    if (language === "mermaid") {
      return (
        <div key={generateStableKey(String(children), 'mermaid')}>
          <MermaidBlock 
            chart={String(children)} 
            zoomingEnabled={true} 
          />
        </div>
      );
    }

    const isInline = !className;
    return (
      <code
        key={`code-${Math.random().toString(36).substring(2, 9)}`}
        className={`${className} ${isInline
            ? "bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800"
            : ""
          }`}
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children, className, ...props }: any) => {
    const child = Array.isArray(children) ? children[0] : children;
    const childClassName = (child as any)?.props?.className as string | undefined;

    // 检查是否是已经预处理过的SVG内容
    const content = String((child as any)?.props?.children ?? []);
    if (content.includes('<svg') && content.includes('</svg>')) {
      return (
        <div key={generateStableKey(content, 'svg-pre')} className="mermaid-svg-container my-4">
          <SvgWithFullscreen 
            svgContent={content}
            className="w-full"
          />
        </div>
      );
    }

    // 检查是否是 React 组件形式的 SVG
    if (React.isValidElement(child) && child.type === 'svg') {
      // 将 React SVG 组件转换为字符串
      const svgString = ReactDOMServer.renderToStaticMarkup(child);
      return (
        <div key={generateStableKey(svgString, 'svg-react')} className="mermaid-svg-container my-4">
          <SvgWithFullscreen 
            svgContent={svgString}
            className="w-full"
          />
        </div>
      );
    }

    if (childClassName?.includes("language-mermaid")) {
      const chart = (child as any)?.props?.children ?? [];
      return (
        <div key={generateStableKey(String(chart), 'mermaid-pre')}>
          <MermaidBlock 
            chart={String(chart)} 
            zoomingEnabled={true} 
          />
        </div>
      );
    }

    return (
      <pre
        key={`pre-${Math.random().toString(36).substring(2, 9)}`}
        className={`bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4 text-sm font-mono ${className ?? ""}`.trim()}
        {...props}
      >
        {children}
      </pre>
    );
  },
  blockquote: ({ children, ...props }: any) => (
    <blockquote
      className="border-l-4 border-blue-500 pl-4 py-2 mb-4 bg-blue-50 text-gray-700 italic"
      {...props}
    >
      {children}
    </blockquote>
  ),
  table: ({ children, ...props }: any) => (
    <div className="overflow-x-auto mb-4">
      <table
        className="min-w-full border border-gray-300"
        {...props}
      >
        {children}
      </table>
    </div>
  ),
  th: ({ children, ...props }: any) => (
    <th
      className="border border-gray-300 px-4 py-2 bg-gray-100 font-semibold text-left"
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ children, ...props }: any) => (
    <td className="border border-gray-300 px-4 py-2" {...props}>
      {children}
    </td>
  ),
});

const MainContentComponent = ({
  activeSection,
  onSectionChange,
  onFileSelect,
  onFileHighlight,
  fileTree,
  projectName,
  taskStatistics,
  taskId,
  processedReadmeContent,
  paginatedContent,
}: MainContentProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isProcessingMermaid, setIsProcessingMermaid] = useState(false);
  const [processedContent, setProcessedContent] = useState<string>("");

  // SVG 缩放功能
  const contentRef = useRef<HTMLDivElement>(null);
  
  // 滚动到顶部的函数
  const scrollToTop = useCallback(() => {
    // 首先尝试通过ref访问
    if (contentRef.current) {
      const scrollContainer = contentRef.current.closest('main');
      if (scrollContainer) {
        scrollContainer.scrollTop = 0;
        scrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
        return;
      }
    }
    
    // 如果ref方法失败，使用DOM查询
    const scrollContainer = document.querySelector("main");
    if (scrollContainer) {
      scrollContainer.scrollTop = 0;
      scrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, []);
  // 获取当前章节的内容用于SVG缩放
  const currentContentForSvg = useMemo(() => {
    if (activeSection === "overview") return null;
    
    if (paginatedContent && paginatedContent.length > 0) {
      const sectionContent = getContentBySectionId(paginatedContent, activeSection);
      return sectionContent || null;
    }
    
    return processedReadmeContent || null;
  }, [paginatedContent, processedReadmeContent, activeSection]);
  
  useSvgPanZoom(contentRef, currentContentForSvg, true);


  // 当taskId改变时重置状态
  useEffect(() => {
    if (!taskId) {
      setIsLoading(false);
      setError(null);
    }
  }, [taskId]);

  // 当activeSection改变时，滚动到顶部
  useEffect(() => {
    if (activeSection && (processedReadmeContent || paginatedContent)) {
      // 使用 setTimeout 确保 DOM 更新完成
      setTimeout(() => {
        scrollToTop();
      }, 100); // 增加延迟确保DOM完全更新
    }
  }, [activeSection, processedReadmeContent, paginatedContent, scrollToTop]);

  // 强制清理DOM，防止SVG组件冲突
  useLayoutEffect(() => {
    // 清理可能残留的SVG元素
    const svgElements = document.querySelectorAll('.mermaid-svg-container svg');
    svgElements.forEach(svg => {
      try {
        if (svg.parentNode) {
          svg.parentNode.removeChild(svg);
        }
      } catch (error) {
        // 忽略清理错误
        console.warn('SVG cleanup warning:', error);
      }
    });
  }, [activeSection]);

  // 预处理 mermaid 代码块
  useEffect(() => {
    const processMermaidContent = async () => {
      // 先重置状态，避免DOM不一致
      setProcessedContent("");
      setIsProcessingMermaid(false);
      
      if (activeSection === "overview") {
        return;
      }

      // 添加延迟，确保DOM完全清理
      await new Promise(resolve => setTimeout(resolve, 50));

      // 获取当前章节的内容
      let currentContent = "";
      if (paginatedContent && paginatedContent.length > 0) {
        const sectionContent = getContentBySectionId(paginatedContent, activeSection);
        if (sectionContent) {
          currentContent = sectionContent;
        } else {
          currentContent = paginatedContent[0]?.content || "";
        }
      } else if (processedReadmeContent) {
        currentContent = processedReadmeContent;
      }

      if (!currentContent) {
        return;
      }

      // 检查是否包含 mermaid 代码块
      if (hasMermaidBlocks(currentContent)) {
        setIsProcessingMermaid(true);
        try {
          const processed = await preprocessMermaidInMarkdown(currentContent);
          setProcessedContent(processed);
        } catch (error) {
          console.error("Failed to process mermaid content:", error);
          setProcessedContent(currentContent); // 如果处理失败，使用原始内容
        } finally {
          setIsProcessingMermaid(false);
        }
      } else {
        setProcessedContent(currentContent);
        setIsProcessingMermaid(false);
      }
    };

    processMermaidContent();
  }, [activeSection, paginatedContent, processedReadmeContent]);




  // 使用 useMemo 缓存 markdown 组件配置，避免每次渲染都重新创建
  const markdownComponents = useMemo(
    () => createMarkdownComponents(onFileHighlight, onSectionChange, fileTree),
    [onFileHighlight, onSectionChange, fileTree]
  );

  // 使用 useMemo 缓存 ReactMarkdown 的渲染结果，避免重复解析
  const renderedMarkdown = useMemo(() => {
    if (activeSection === "overview") return null;

    // 使用预处理后的内容
    const currentContent = processedContent;

    if (!currentContent) return null;

    return (
      <div className="space-y-6 p-6">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="text-gray-500">加载文档中...</div>
          </div>
        )}

        {isProcessingMermaid && (
          <div className="flex items-center justify-center py-8">
            <div className="text-gray-500">正在转换图表...</div>
          </div>
        )}

        {error && <div className="text-red-500 py-4">{error}</div>}

        {!isLoading && !error && !isProcessingMermaid && (
          <div key={`content-${activeSection}`} className="markdown-content max-w-none">
            <MarkdownErrorBoundary>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeRaw]}
                components={markdownComponents}
              >
                {currentContent}
              </ReactMarkdown>
            </MarkdownErrorBoundary>
          </div>
        )}
      </div>
    );
  }, [processedContent, markdownComponents, isLoading, error, isProcessingMermaid, activeSection]);

  const renderContent = () => {
    // 如果是项目概览，显示固定的概览内容
    if (activeSection === "overview") {
      return (
        <div className="space-y-8">
          {/* 项目概述 */}
          <div>
            <h1>{projectName ? `${projectName} - 项目概览` : "项目概览"}</h1>
            <p className="text-gray-600 mt-2">
              {projectName
                ? `${projectName} 项目的详细分析和文档。`
                : "这是一个基于 Python 的 Web 应用程序，采用 Flask 框架构建。本应用提供了完整的用户认证系统和内容管理功能，采用现代化的架构设计和最佳实践。"}
            </p>
          </div>

          {/* 关键指标 */}
          <div>
            <h2 className="mb-4">关键指标</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="p-4">
                <h3>代码行数</h3>
                <p className="text-2xl font-bold text-blue-600">
                  {taskStatistics?.code_lines?.toLocaleString() || "加载中..."}
                </p>
                <p className="text-sm text-gray-500">代码行数</p>
              </Card>
              <Card className="p-4">
                <h3>文件数量</h3>
                <p className="text-2xl font-bold text-green-600">
                  {taskStatistics?.total_files?.toLocaleString() || "加载中..."}
                </p>
                <p className="text-sm text-gray-500">源代码文件</p>
              </Card>
              <Card className="p-4">
                <h3>模块数量</h3>
                <p className="text-2xl font-bold text-purple-600">
                  {taskStatistics?.module_count?.toLocaleString() ||
                    "加载中..."}
                </p>
                <p className="text-sm text-gray-500">模块数量</p>
              </Card>
            </div>
          </div>
        </div>
      );
    }

    // 如果有markdown内容，显示对应的章节内容（使用缓存的渲染结果）
    if ((processedReadmeContent || paginatedContent) && activeSection !== "overview") {
      return renderedMarkdown;
    }

    // 默认情况，显示原有的静态内容
    switch (activeSection) {
      case "data-models":
      case "entity-diagram":
        return (
          <div className="space-y-6">
            <div>
              <h1>数据模型浏览器</h1>
              <p className="text-gray-600 mt-2">
                AI 摘要: User 模型是系统的核心，管理用户认证和权限。Post
                模型负责���容�����理，两者通过外键关联。
              </p>
            </div>

            <Card className="p-6">
              <h3 className="mb-4">实体关系图</h3>
              <div className="bg-gray-50 rounded-lg p-8 min-h-80 flex items-center justify-center">
                <div className="space-y-8">
                  {/* User Entity */}
                  <div
                    className="bg-white border-2 border-blue-300 rounded-lg p-4 cursor-pointer hover:shadow-lg hover:border-blue-400 transition-all duration-200"
                    onClick={() => onFileSelect("src/models/user.py")}
                  >
                    <h4 className="font-bold text-blue-700 mb-2">User</h4>
                    <div className="text-sm text-gray-600 space-y-1">
                      <div className="flex justify-between">
                        <span>id</span>
                        <span className="text-xs text-blue-600">
                          Integer (PK)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>email</span>
                        <span className="text-xs text-gray-500">String</span>
                      </div>
                      <div className="flex justify-between">
                        <span>password_hash</span>
                        <span className="text-xs text-gray-500">String</span>
                      </div>
                      <div className="flex justify-between">
                        <span>created_at</span>
                        <span className="text-xs text-gray-500">DateTime</span>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-blue-600">
                      点击查看源代码 →
                    </div>
                  </div>

                  {/* Relationship line */}
                  <div className="flex justify-center">
                    <div className="flex flex-col items-center">
                      <div className="w-px h-8 bg-gray-400"></div>
                      <div className="text-xs text-gray-500 bg-white px-2 py-1 rounded border">
                        1:N
                      </div>
                      <div className="w-px h-8 bg-gray-400"></div>
                    </div>
                  </div>

                  {/* Post Entity */}
                  <div
                    className="bg-white border-2 border-green-300 rounded-lg p-4 cursor-pointer hover:shadow-lg hover:border-green-400 transition-all duration-200"
                    onClick={() => onFileSelect("src/models/post.py")}
                  >
                    <h4 className="font-bold text-green-700 mb-2">Post</h4>
                    <div className="text-sm text-gray-600 space-y-1">
                      <div className="flex justify-between">
                        <span>id</span>
                        <span className="text-xs text-green-600">
                          Integer (PK)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>title</span>
                        <span className="text-xs text-gray-500">String</span>
                      </div>
                      <div className="flex justify-between">
                        <span>content</span>
                        <span className="text-xs text-gray-500">Text</span>
                      </div>
                      <div className="flex justify-between">
                        <span>user_id</span>
                        <span className="text-xs text-orange-600">
                          Integer (FK)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>published_at</span>
                        <span className="text-xs text-gray-500">DateTime</span>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-green-600">
                      点击查看源代码 →
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        );

      case "glossary":
      case "terms":
        return (
          <div className="space-y-6">
            <div>
              <h1>领域术语词典</h1>
              <p className="text-gray-600 mt-2">项目中的核心概念和术语解释</p>
            </div>

            <div className="space-y-4">
              {[
                {
                  term: "User",
                  definition: "系统用户，包含认证信息和个人资料",
                  file: "src/models/user.py",
                },
                {
                  term: "Post",
                  definition: "用户发布的内容文章，支持富文本格式",
                  file: "src/models/post.py",
                },
                {
                  term: "Authentication",
                  definition: "用户身份验证机制，基于 JWT Token",
                  file: "src/api/auth.py",
                },
                {
                  term: "Migration",
                  definition: "数据库结构变更的版本控制机制",
                  file: null,
                },
                {
                  term: "Blueprint",
                  definition: "Flask 应用的模块化组织方式",
                  file: null,
                },
              ].map((item) => (
                <Card key={item.term} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <Badge variant="secondary">{item.term}</Badge>
                      <p className="text-gray-700 flex-1">{item.definition}</p>
                    </div>
                    {item.file && (
                      <button
                        onClick={() => onFileSelect(item.file)}
                        className="text-sm text-blue-600 hover:text-blue-800 ml-4"
                      >
                        查看源码 →
                      </button>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        );

      case "architecture":
      case "external-deps":
        return (
          <div className="space-y-6">
            <div>
              <h1>架构边界</h1>
              <p className="text-gray-600 mt-2">系统的外部依赖和内部接口分析</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-4">
                <h3 className="mb-4">外部依赖</h3>
                <div className="space-y-3">
                  {[
                    {
                      name: "PostgreSQL",
                      type: "数据库",
                      description: "主要数据存储",
                    },
                    {
                      name: "Redis",
                      type: "缓存",
                      description: "会话和缓存存储",
                    },
                    {
                      name: "AWS S3",
                      type: "存储",
                      description: "文件上传存储",
                    },
                    {
                      name: "SendGrid",
                      type: "API",
                      description: "邮件发送服务",
                    },
                  ].map((dep) => (
                    <div
                      key={dep.name}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <div className="font-medium">{dep.name}</div>
                        <div className="text-sm text-gray-600">
                          {dep.description}
                        </div>
                      </div>
                      <Badge variant="outline">{dep.type}</Badge>
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="p-4">
                <h3 className="mb-4">内部接口</h3>
                <div className="space-y-3">
                  {[
                    {
                      path: "/api/auth/login",
                      method: "POST",
                      description: "用户登录认证",
                      file: "src/api/auth.py",
                    },
                    {
                      path: "/api/auth/register",
                      method: "POST",
                      description: "用户注册",
                      file: "src/api/auth.py",
                    },
                    {
                      path: "/api/posts",
                      method: "GET",
                      description: "获取文章列表",
                      file: "src/api/posts.py",
                    },
                    {
                      path: "/api/posts",
                      method: "POST",
                      description: "创建新文章",
                      file: "src/api/posts.py",
                    },
                  ].map((api) => (
                    <div
                      key={`${api.method}-${api.path}`}
                      className="p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">{api.method}</Badge>
                          <code className="text-sm">{api.path}</code>
                        </div>
                        <button
                          onClick={() => onFileSelect(api.file)}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          查看实现 →
                        </button>
                      </div>
                      <div className="text-sm text-gray-600">
                        {api.description}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        );

      case "call-graph":
      case "module-graph":
        return (
          <div className="space-y-6">
            <div>
              <h1>调用图谱</h1>
              <p className="text-gray-600 mt-2">模块依赖关系和函数调用链分析</p>
            </div>

            <Card className="p-6">
              <h3 className="mb-4">模块依赖图</h3>
              <div className="bg-gray-50 rounded-lg p-8 min-h-96">
                <div className="space-y-8">
                  {/* API/表现层 */}
                  <div className="space-y-3">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-700 bg-blue-100 rounded-full py-2 px-4 inline-block">
                        API / 表现层
                      </h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        {
                          module: "认证接口",
                          files: [
                            { name: "auth.py", path: "src/api/auth.py" },
                            {
                              name: "middleware.py",
                              path: "src/api/middleware.py",
                            },
                          ],
                        },
                        {
                          module: "内容接口",
                          files: [
                            { name: "posts.py", path: "src/api/posts.py" },
                            {
                              name: "comments.py",
                              path: "src/api/comments.py",
                            },
                          ],
                        },
                        {
                          module: "用户接口",
                          files: [
                            { name: "users.py", path: "src/api/users.py" },
                            {
                              name: "profiles.py",
                              path: "src/api/profiles.py",
                            },
                          ],
                        },
                      ].map((module) => (
                        <div
                          key={module.module}
                          className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4"
                        >
                          <div className="font-medium text-blue-900 mb-3 text-center">
                            {module.module}
                          </div>
                          <div className="space-y-1">
                            {module.files.map((file) => (
                              <div
                                key={file.name}
                                className="text-sm bg-white rounded px-2 py-1 cursor-pointer hover:bg-blue-100 transition-colors"
                                onClick={() => onFileSelect(file.path)}
                              >
                                {file.name}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 分层分割线 */}
                  <div className="flex justify-center">
                    <div className="text-2xl text-gray-400">⬇</div>
                  </div>

                  {/* 业务逻辑层 */}
                  <div className="space-y-3">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-700 bg-purple-100 rounded-full py-2 px-4 inline-block">
                        业务逻辑层
                      </h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        {
                          module: "认证服务",
                          files: [
                            {
                              name: "auth_service.py",
                              path: "src/services/auth_service.py",
                            },
                            {
                              name: "token_service.py",
                              path: "src/services/token_service.py",
                            },
                          ],
                        },
                        {
                          module: "业务服务",
                          files: [
                            {
                              name: "post_service.py",
                              path: "src/services/post_service.py",
                            },
                            {
                              name: "user_service.py",
                              path: "src/services/user_service.py",
                            },
                          ],
                        },
                      ].map((module) => (
                        <div
                          key={module.module}
                          className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4"
                        >
                          <div className="font-medium text-purple-900 mb-3 text-center">
                            {module.module}
                          </div>
                          <div className="space-y-1">
                            {module.files.map((file) => (
                              <div
                                key={file.name}
                                className="text-sm bg-white rounded px-2 py-1 cursor-pointer hover:bg-purple-100 transition-colors"
                                onClick={() => onFileSelect(file.path)}
                              >
                                {file.name}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 分层分割线 */}
                  <div className="flex justify-center">
                    <div className="text-2xl text-gray-400">⬇</div>
                  </div>

                  {/* 数据访问层 */}
                  <div className="space-y-3">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-700 bg-green-100 rounded-full py-2 px-4 inline-block">
                        数据访问层
                      </h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        {
                          module: "数据模型",
                          files: [
                            { name: "user.py", path: "src/models/user.py" },
                            { name: "post.py", path: "src/models/post.py" },
                          ],
                        },
                        {
                          module: "数据库工具",
                          files: [
                            {
                              name: "database.py",
                              path: "src/core/database.py",
                            },
                            { name: "migrations/", path: "src/migrations/" },
                          ],
                        },
                        {
                          module: "缓存层",
                          files: [
                            {
                              name: "redis_client.py",
                              path: "src/core/redis_client.py",
                            },
                            {
                              name: "cache_service.py",
                              path: "src/services/cache_service.py",
                            },
                          ],
                        },
                      ].map((module) => (
                        <div
                          key={module.module}
                          className="bg-green-50 border-2 border-green-200 rounded-lg p-4"
                        >
                          <div className="font-medium text-green-900 mb-3 text-center">
                            {module.module}
                          </div>
                          <div className="space-y-1">
                            {module.files.map((file) => (
                              <div
                                key={file.name}
                                className="text-sm bg-white rounded px-2 py-1 cursor-pointer hover:bg-green-100 transition-colors"
                                onClick={() => onFileSelect(file.path)}
                              >
                                {file.name}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 分层分割线 */}
                  <div className="flex justify-center">
                    <div className="text-2xl text-gray-400">⬇</div>
                  </div>

                  {/* 基础设施层 */}
                  <div className="space-y-3">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-700 bg-gray-200 rounded-full py-2 px-4 inline-block">
                        基础设施层
                      </h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        {
                          module: "数据库",
                          files: [
                            { name: "PostgreSQL", path: null },
                            { name: "Redis", path: null },
                          ],
                        },
                        {
                          module: "外部服务",
                          files: [
                            { name: "AWS S3", path: null },
                            { name: "SendGrid", path: null },
                          ],
                        },
                      ].map((module) => (
                        <div
                          key={module.module}
                          className="bg-gray-100 border-2 border-gray-300 rounded-lg p-4"
                        >
                          <div className="font-medium text-gray-700 mb-3 text-center">
                            {module.module}
                          </div>
                          <div className="space-y-1">
                            {module.files.map((file) => (
                              <div
                                key={file.name}
                                className={`text-sm rounded px-2 py-1 ${file.path
                                    ? "bg-white cursor-pointer hover:bg-gray-200 transition-colors"
                                    : "bg-gray-50 text-gray-600"
                                  }`}
                                onClick={() =>
                                  file.path && onFileSelect(file.path)
                                }
                              >
                                {file.name}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        );

      default:
        return (
          <div className="space-y-6">
            <div>
              <h1>选择左侧菜单查看内容</h1>
              <p className="text-gray-600 mt-2">
                请从左侧导航栏选择要查看的分析结果
              </p>
            </div>
          </div>
        );
    }
  };

  return <div ref={contentRef} className="p-8 max-w-none">{renderContent()}</div>;
};

// 使用 memo 优化组件，但允许 activeSection 变化时重新渲染（因为需要执行 useEffect）
export const MainContent = memo(MainContentComponent, (prevProps, nextProps) => {
  // 返回 true 表示 props 相等，不需要重新渲染
  // 返回 false 表示需要重新渲染

  // 关键数据变化时必须重新渲染
  if (prevProps.taskId !== nextProps.taskId) return false;
  if (prevProps.projectName !== nextProps.projectName) return false;
  if (prevProps.fileTree !== nextProps.fileTree) return false;
  if (prevProps.activeSection !== nextProps.activeSection) return false; // activeSection 变化时需要重新渲染以触发 useEffect
  if (prevProps.processedReadmeContent !== nextProps.processedReadmeContent) return false;
  if (prevProps.paginatedContent !== nextProps.paginatedContent) return false;

  // taskStatistics 的深度比较
  if (
    prevProps.taskStatistics?.code_lines !== nextProps.taskStatistics?.code_lines ||
    prevProps.taskStatistics?.total_files !== nextProps.taskStatistics?.total_files ||
    prevProps.taskStatistics?.module_count !== nextProps.taskStatistics?.module_count
  ) {
    return false;
  }

  // 回调函数通常是稳定的，但为了安全起见还是检查一下
  if (prevProps.onSectionChange !== nextProps.onSectionChange) return false;
  if (prevProps.onFileSelect !== nextProps.onFileSelect) return false;
  if (prevProps.onFileHighlight !== nextProps.onFileHighlight) return false;

  // 如果所有检查都通过，props 相等，不需要重新渲染
  return true;
});
