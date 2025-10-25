import React, { useEffect, useRef, useMemo } from "react";
import Markdown from "marked-react";
import mermaid from "mermaid";
import { findFileInTree, FileNode, normalizePath } from "../utils/fileTree";

// 初始化 mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "loose",
  fontFamily: "sans-serif",
  logLevel: "fatal", // 只显示致命错误，忽略其他错误
});

interface MarkedMarkdownProps {
  content: string;
  onFileHighlight: (file: string) => void;
  onSectionChange: (section: string) => void;
  scrollToSection: (sectionId: string) => void;
  fileTree: FileNode | null;
}

// Mermaid 渲染组件
const MermaidRenderer: React.FC<{ chart: string }> = ({ chart }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartId = useRef(`mermaid-${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    if (containerRef.current && chart) {
      mermaid
        .render(chartId.current, chart.trim())
        .then(({ svg }) => {
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        })
        .catch((error) => {
          // 捕获 Mermaid 渲染错误，静默处理不显示错误
          console.warn("Mermaid 图表渲染失败:", error);
          if (containerRef.current) {
            // 可以选择显示一个简单的提示或留空
            containerRef.current.innerHTML = "";
          }
        });
    }
  }, [chart]);

  return (
    <div className="mermaid-container my-6 flex justify-center">
      <div ref={containerRef} className="max-w-full overflow-x-auto" />
    </div>
  );
};

// 生成标题ID
const generateSectionId = (title: string): string => {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/^-+|-+$/g, "");
};

// 处理标题文本，提取自定义ID
const processHeadingText = (text: string) => {
  const match = text.match(/^(.*?)(?:\s*\{#([A-Za-z0-9_-]+)\})\s*$/);
  if (match) {
    return {
      text: match[1]?.trimEnd() || "",
      customId: match[2],
    };
  }
  return {
    text,
    customId: null,
  };
};

export const MarkedMarkdown: React.FC<MarkedMarkdownProps> = ({
  content,
  onFileHighlight,
  onSectionChange,
  scrollToSection,
  fileTree,
}) => {
  // 使用 useMemo 缓存渲染器配置
  const renderer = useMemo(() => {
    const customRenderer: any = {
      // 折叠块
      html(html) {
        // 保留原始 HTML（用于 details/summary 标签）
        return <div dangerouslySetInnerHTML={{ __html: html }} />;
      },

      // 标题
      heading(text, level) {
        const { text: cleanText, customId } = processHeadingText(
          typeof text === "string" ? text : String(text)
        );
        const id = customId || generateSectionId(cleanText);

        const className = {
          1: "text-3xl font-bold text-gray-900 mb-6 border-b border-gray-200 pb-3 scroll-mt-4",
          2: "text-2xl font-semibold text-gray-800 mb-4 mt-8 scroll-mt-4",
          3: "text-xl font-medium text-gray-700 mb-3 mt-6",
          4: "text-lg font-medium text-gray-700 mb-2 mt-4",
          5: "text-base font-medium text-gray-700 mb-2 mt-3",
          6: "text-sm font-medium text-gray-700 mb-2 mt-2",
        }[level];

        return React.createElement(
          `h${level}`,
          { id, className },
          cleanText
        );
      },

      // 段落
      paragraph(children) {
        return <p className="text-gray-700 leading-relaxed mb-4">{children}</p>;
      },

      // 列表
      list(children, ordered) {
        const Tag = ordered ? "ol" : "ul";
        const className = ordered
          ? "list-decimal list-inside mb-4 space-y-2 text-gray-700"
          : "list-disc list-inside mb-4 space-y-2 text-gray-700";
        return <Tag className={className}>{children}</Tag>;
      },

      listitem(children) {
        return <li className="ml-4">{children}</li>;
      },

      // 链接
      link(href, text) {
        if (!href) {
          return <span>{text}</span>;
        }

        // 处理内部锚点链接
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
                  scrollToSection(sectionId);
                }
              }}
            >
              {text}
            </a>
          );
        }

        // 处理文件链接
        const normalizedHref = normalizePath(href);
        const fileExists = findFileInTree(fileTree, normalizedHref);

        if (fileExists) {
          return (
            <button
              className="text-blue-600 hover:text-blue-800 underline font-medium transition-colors"
              onClick={() => onFileHighlight(normalizedHref)}
              title={`定位到文件: ${normalizedHref}`}
            >
              {text}
            </button>
          );
        } else {
          return (
            <span
              className="text-gray-500 font-mono text-sm bg-gray-100 px-1 py-0.5 rounded"
              title={`文件不存在: ${normalizedHref}`}
            >
              {text}
            </span>
          );
        }
      },

      // 代码块
      code(code, lang) {
        // Mermaid 图表
        if (lang === "mermaid") {
          return <MermaidRenderer chart={code} />;
        }

        return (
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4 text-sm font-mono">
            <code className={lang ? `language-${lang}` : ""}>{code}</code>
          </pre>
        );
      },

      // 行内代码
      codespan(code) {
        return (
          <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">
            {code}
          </code>
        );
      },

      // 引用块
      blockquote(children) {
        return (
          <blockquote className="border-l-4 border-blue-500 pl-4 py-2 mb-4 bg-blue-50 text-gray-700 italic">
            {children}
          </blockquote>
        );
      },

      // 表格
      table(children) {
        return (
          <div className="overflow-x-auto mb-4">
            <table className="min-w-full border border-gray-300">{children}</table>
          </div>
        );
      },

      tablehead(children) {
        return <thead>{children}</thead>;
      },

      tablebody(children) {
        return <tbody>{children}</tbody>;
      },

      tablerow(children) {
        return <tr>{children}</tr>;
      },

      tablecell(children, flags) {
        const Tag = flags.header ? "th" : "td";
        const className = flags.header
          ? "border border-gray-300 px-4 py-2 bg-gray-100 font-semibold text-left"
          : "border border-gray-300 px-4 py-2";
        return <Tag className={className}>{children}</Tag>;
      },

      // 强调
      strong(children) {
        return <strong className="font-semibold">{children}</strong>;
      },

      em(children) {
        return <em className="italic">{children}</em>;
      },

      // 删除线
      del(children) {
        return <del className="line-through">{children}</del>;
      },

      // 分割线
      hr() {
        return <hr className="my-8 border-gray-300" />;
      },

      // 图片
      image(href, title, text) {
        return (
          <img
            src={href || ""}
            alt={text || ""}
            title={title || ""}
            className="max-w-full h-auto rounded-lg my-4"
          />
        );
      },
    };

    return customRenderer;
  }, [onFileHighlight, onSectionChange, scrollToSection, fileTree]);

  return (
    <div className="markdown-content max-w-none">
      <Markdown
        value={content}
        renderer={renderer}
        gfm={true} // 启用 GitHub Flavored Markdown
      />
    </div>
  );
};

