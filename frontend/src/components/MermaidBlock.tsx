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
    lineColor: "#333333", // 确保线条颜色足够深
    primaryBorderColor: "#333333",
    primaryTextColor: "#1f2937",
    secondaryColor: "#f8f9fa",
    tertiaryColor: "#ffffff",
    // 流程图特定配置
    flowchart: {
      nodeBkg: "#f8f9fa",
      nodeBorder: "#333333",
      clusterBkg: "#ffffff",
      clusterBorder: "#333333",
      defaultLinkColor: "#333333",
      titleColor: "#1f2937",
    },
    // 序列图特定配置
    sequence: {
      actorBkg: "#f8f9fa",
      actorBorder: "#333333",
      actorTextColor: "#1f2937",
      actorLineColor: "#333333",
      signalColor: "#333333",
      signalTextColor: "#1f2937",
      labelBoxBkgColor: "#ffffff",
      labelBoxBorderColor: "#333333",
      labelTextColor: "#1f2937",
      loopTextColor: "#1f2937",
      activationBkgColor: "#e5e7eb",
      activationBorderColor: "#333333",
    },
  },
  flowchart: {
    useMaxWidth: true,
    htmlLabels: true,
    curve: "basis",
  },
  sequence: {
    useMaxWidth: true,
    wrap: true,
  },
  logLevel: "error",
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
  zoomingEnabled?: boolean;
}

export function MermaidBlock({ chart, zoomingEnabled = false }: MermaidBlockProps) {
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
          //Mermaid 渲染失败 让其展示原文 原文格式和其他代码展示一致
          if (!isCancelled && containerRef.current) {
            containerRef.current.innerHTML = `<pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto mb-4 text-sm font-mono">${chart}</pre>`;
          }
          // Mermaid 渲染失败
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

  // Initialize pan-zoom functionality when SVG is rendered
  useEffect(() => {
    if (hasRendered && zoomingEnabled && containerRef.current) {
      const initializePanZoom = async () => {
        // 等待 SVG 元素完全渲染
        const waitForSvg = () => {
          return new Promise<SVGElement | null>((resolve) => {
            const checkSvg = () => {
              const svgElement = containerRef.current?.querySelector("svg");
              if (svgElement && svgElement.children.length > 0) {
                resolve(svgElement);
              } else {
                setTimeout(checkSvg, 50);
              }
            };
            checkSvg();
          });
        };

        try {
          const svgElement = await waitForSvg();
          if (svgElement) {
            // Remove any max-width constraints
            svgElement.style.maxWidth = "none";
            svgElement.style.width = "100%";
            svgElement.style.height = "100%";

            // Dynamically import svg-pan-zoom only when needed in the browser
            const svgPanZoom = (await import("svg-pan-zoom")).default;

            svgPanZoom(svgElement, {
              zoomEnabled: true,
              controlIconsEnabled: false,
              fit: true,
              center: true,
              minZoom: 0.1,
              maxZoom: 10,
              zoomScaleSensitivity: 0.3,
            });
            
            // svg-pan-zoom initialized successfully
          }
        } catch (error) {
          // Failed to load svg-pan-zoom
        }
      };

      // Wait for the SVG to be rendered
      setTimeout(() => {
        void initializePanZoom();
      }, 200);
    }
  }, [hasRendered, zoomingEnabled]);

  return (
    <div 
      ref={inViewRef} 
      className="mermaid-wrapper"
      style={{ minHeight: isLoading ? "100px" : "auto" }}
    >
      <div
        className={`w-full max-w-full ${zoomingEnabled ? "h-[600px] p-4" : ""}`}
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
      <div 
        ref={containerRef} 
        className={`mermaid ${zoomingEnabled ? "h-full rounded-lg border-2 border-black" : ""}`} 
        aria-live="polite" 
      />
      </div>
    </div>
  );
}

