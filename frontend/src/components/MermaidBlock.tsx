import { useEffect, useMemo, useRef } from "react";
import mermaid from "mermaid";

const defaultOptions: mermaid.Config = {
  startOnLoad: false,
  securityLevel: "loose",
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
  const renderId = useMemo(() => `mermaid-${Math.random().toString(36).slice(2)}`, []);

  useEffect(() => {
    initializeMermaid();

    let isCancelled = false;

    const renderChart = async () => {
      if (!containerRef.current) return;

      containerRef.current.innerHTML = "";

      try {
        const { svg } = await mermaid.render(renderId, chart.trim());
        if (!isCancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (error) {
        if (!isCancelled && containerRef.current) {
          containerRef.current.innerHTML = `<pre class="bg-red-50 text-red-600 p-3 rounded border border-red-200 text-sm">Mermaid 渲染失败：${String(
            error
          )}</pre>`;
        }
        console.error("Mermaid 渲染失败", error);
      }
    };

    renderChart();

    return () => {
      isCancelled = true;
    };
  }, [chart, renderId]);

  return <div ref={containerRef} className="mermaid" aria-live="polite" />;
}

