import React, { useEffect, useState, memo, useCallback, useRef } from 'react';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
  zoomingEnabled?: boolean;
}

// 全局 Mermaid 实例管理
class MermaidManager {
  private static instance: MermaidManager;
  private mermaid: any = null;
  private initialized = false;
  private initPromise: Promise<any> | null = null;

  static getInstance(): MermaidManager {
    if (!MermaidManager.instance) {
      MermaidManager.instance = new MermaidManager();
    }
    return MermaidManager.instance;
  }

  async getMermaid() {
    if (this.mermaid && this.initialized) {
      return this.mermaid;
    }

    if (this.initPromise) {
      return this.initPromise;
    }

    this.initPromise = this.initializeMermaid();
    return this.initPromise;
  }

  private async initializeMermaid() {
    try {
      // 动态导入 mermaid
      const mermaidModule = await import('mermaid');
      this.mermaid = mermaidModule.default || mermaidModule;

      // 简化配置，提高性能
      this.mermaid.initialize({
        startOnLoad: false,
        theme: 'base',
        themeVariables: {
          background: 'transparent',
          mainBkg: 'transparent',
          primaryColor: '#f3f4f6',
          primaryTextColor: '#1f2937',
          lineColor: '#6b7280',
        },
        securityLevel: 'loose',
        fontFamily: 'system-ui, sans-serif',
        fontSize: 14,
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true,
        },
        sequence: {
          useMaxWidth: true,
        },
      });

      this.initialized = true;
      return this.mermaid;
    } catch (error) {
      // Failed to load mermaid
      throw error;
    }
  }
}

const mermaidManager = MermaidManager.getInstance();

const MermaidDiagram: React.FC<MermaidDiagramProps> = memo(({ chart, className = '', zoomingEnabled = false }) => {
  const [svgContent, setSvgContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [renderedChart, setRenderedChart] = useState<string>('');
  const [inView, setInView] = useState(false);

  const observerRef = useRef<IntersectionObserver | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const inViewRef = useCallback((node: HTMLDivElement | null) => {
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }

    if (!node) {
      setInView(false);
      return;
    }

    if (typeof window === 'undefined' || typeof IntersectionObserver === 'undefined') {
      setInView(true);
      return;
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0]) {
          setInView(entries[0].isIntersecting);
        }
      },
      {
        threshold: 0,
        rootMargin: '50px',
      }
    );

    observerRef.current.observe(node);
  }, []);

  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
        observerRef.current = null;
      }
    };
  }, []);

  // 使用 Intersection Observer 实现懒加载，优化性能

  // 检查是否已经渲染过相同的图表
  const hasRendered = renderedChart === chart && svgContent;

  useEffect(() => {
    // 如果已经渲染过相同的图表或者不在视口中或者没有内容，则不重新渲染
    if (hasRendered || !inView || !chart.trim()) return;

    // 添加防抖，避免频繁渲染
    const timeoutId = setTimeout(() => {
      const renderDiagram = async () => {
        setIsLoading(true);
        setError(null);
        setSvgContent('');

        try {
          // 获取 Mermaid 实例
          const mermaid = await mermaidManager.getMermaid();

          // 生成唯一 ID
          const id = `mermaid-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;

          // 验证图表语法（快速失败）
          try {
            await mermaid.parse(chart);
          } catch (parseError) {
            throw new Error('Invalid Mermaid syntax: ' + (parseError instanceof Error ? parseError.message : 'Unknown parse error'));
          }

          // 使用 requestIdleCallback 或 setTimeout 来避免阻塞主线程
          const renderInIdle = () => {
            return new Promise<string>((resolve, reject) => {
              const callback = async () => {
                try {
                  const { svg } = await mermaid.render(id, chart);
                  resolve(svg);
                } catch (error) {
                  reject(error);
                }
              };

              // 使用 requestIdleCallback 如果可用，否则使用 setTimeout
              if ('requestIdleCallback' in window) {
                (window as any).requestIdleCallback(callback, { timeout: 1000 });
              } else {
                setTimeout(callback, 0);
              }
            });
          };

          const svg = await renderInIdle();

          // 使用 requestAnimationFrame 来确保 DOM 更新不阻塞
          requestAnimationFrame(() => {
            setSvgContent(svg);
            setRenderedChart(chart); // 记录已渲染的图表内容
          });
        } catch (err) {
          // Mermaid rendering error
          setError(err instanceof Error ? err.message : 'Failed to render diagram');
        } finally {
          setIsLoading(false);
        }
      };

      renderDiagram();
    }, 100); // 100ms 防抖

    return () => clearTimeout(timeoutId);
  }, [inView, chart, hasRendered]);

  // Initialize pan-zoom functionality when SVG is rendered
  useEffect(() => {
    if (svgContent && zoomingEnabled && containerRef.current) {
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
  }, [svgContent, zoomingEnabled]);

  return (
    <div
      ref={inViewRef}
      className={`mermaid-container ${className}`}
      style={{
        minHeight: isLoading ? '100px' : 'auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'transparent',
        border: 'none',
        padding: 0,
      }}
    >
      <div
        ref={containerRef}
        className={`w-full max-w-full ${zoomingEnabled ? "h-[600px] p-4" : ""}`}
      >
      {isLoading && (
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          <span>渲染图表中...</span>
        </div>
      )}

      {error && (
        <div className="mermaid-error p-4 border border-red-300 rounded bg-red-50">
          <div className="text-red-700 font-medium mb-2">
            Mermaid 渲染错误: {error}
          </div>
          <details className="text-sm">
            <summary className="cursor-pointer text-red-600 hover:text-red-800">查看原始代码</summary>
            <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto"><code>{chart}</code></pre>
          </details>
        </div>
      )}

      {svgContent && !error && (
        <div
          className={`relative group ${zoomingEnabled ? "h-full rounded-lg border-2 border-black" : ""}`}
        >
          <div
            className={`flex justify-center overflow-auto text-center my-2 cursor-pointer hover:shadow-md transition-shadow duration-200 rounded-md ${zoomingEnabled ? "h-full" : ""}`}
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        </div>
      )}

      {!inView && !isLoading && !error && !svgContent && !hasRendered && (
        <div className="text-gray-400 text-sm py-8">
          📊 Mermaid 图表 (滚动到此处加载)
        </div>
      )}
      </div>
    </div>
  );
});

MermaidDiagram.displayName = 'MermaidDiagram';

export default MermaidDiagram;
