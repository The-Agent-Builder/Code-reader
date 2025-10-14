import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import mermaid from "mermaid";

const defaultOptions = {
  startOnLoad: false,
  suppressErrorRendering: true, //禁止在 DOM 中插入 'Syntax error' 图
  securityLevel: "loose",
  theme: "base",
  themeVariables: {
    background: "transparent",
    mainBkg: "transparent",
  },
};

let mermaidInitialized = false;

const initializeMermaid = () => {
  if (!mermaidInitialized) {
    mermaid.initialize(defaultOptions);
    mermaidInitialized = true;
  }
};

interface MermaidBlockProps {
  chart: string;
}

export function MermaidBlock({ chart }: MermaidBlockProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const renderId = useMemo(() => `mermaid-${Math.random().toString(36).slice(2)}`, []);
  
  const [isInView, setIsInView] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasRendered, setHasRendered] = useState(false);
  const [cachedChart, setCachedChart] = useState("");

  // 懒加载：使用 Intersection Observer 监听元素是否进入视口
  const inViewRef = useCallback((node: HTMLDivElement | null) => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    if (!node) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setIsInView(true);
        }
      },
      {
        threshold: 0,
        rootMargin: "100px", // 提前100px开始加载
      }
    );

    observerRef.current.observe(node);
  }, []);

  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  useEffect(() => {
    // 只有在视口内、未渲染过、且内容有变化时才渲染
    if (!isInView || hasRendered || !chart.trim() || cachedChart === chart) {
      return;
    }

    let isCancelled = false;
    
    // 防抖：延迟渲染，避免快速变化导致多次渲染
    const debounceTimer = setTimeout(() => {
      const renderChart = async () => {
        if (isCancelled || !containerRef.current) return;

        setIsLoading(true);
        containerRef.current.innerHTML = "";

        try {
          initializeMermaid();

          // 使用 requestIdleCallback 在浏览器空闲时渲染，避免阻塞主线程
          const renderInIdle = (): Promise<string> => {
            return new Promise((resolve, reject) => {
              const callback = async () => {
                try {
                  const { svg } = await mermaid.render(renderId, chart.trim());
                  resolve(svg);
                } catch (error) {
                  reject(error);
                }
              };

              // 优先使用 requestIdleCallback，降低渲染优先级
              if ("requestIdleCallback" in window) {
                (window as any).requestIdleCallback(callback, { timeout: 2000 });
              } else {
                setTimeout(callback, 0);
              }
            });
          };

          const svg = await renderInIdle();

          // 使用 requestAnimationFrame 确保 DOM 更新流畅
          if (!isCancelled && containerRef.current) {
            requestAnimationFrame(() => {
              if (containerRef.current) {
                containerRef.current.innerHTML = svg;
                setHasRendered(true);
                setCachedChart(chart);
              }
            });
          }
        } catch (error) {
          if (!isCancelled && containerRef.current) {
            containerRef.current.innerHTML = `<pre class="bg-red-50 text-red-600 p-3 rounded border border-red-200 text-sm">Mermaid 渲染失败：${String(
              error
            )}</pre>`;
          }
          console.error("Mermaid 渲染失败", error);
        } finally {
          setIsLoading(false);
        }
      };

      renderChart();
    }, 150); // 150ms 防抖

    return () => {
      isCancelled = true;
      clearTimeout(debounceTimer);
    };
  }, [chart, renderId, isInView, hasRendered, cachedChart]);

  return (
    <div 
      ref={inViewRef} 
      className="mermaid-wrapper"
      style={{ minHeight: isLoading ? "100px" : "auto" }}
    >
      {isLoading && (
        <div className="flex items-center justify-center space-x-2 text-gray-500 py-4">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500" />
          <span className="text-sm">渲染图表中...</span>
        </div>
      )}
      {!isInView && !isLoading && !hasRendered && (
        <div className="text-gray-400 text-sm py-4 text-center">
          📊 Mermaid 图表 (滚动到此处加载)
        </div>
      )}
      <div ref={containerRef} className="mermaid" aria-live="polite" />
    </div>
  );
}

