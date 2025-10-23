import mermaid from 'mermaid';

// Mermaid 预加载器 - 在应用启动时预加载 Mermaid 库并初始化配置
class MermaidPreloader {
  private static preloadStarted = false;
  private static initialized = false;

  /**
   * 初始化mermaid配置
   * 将mermaid的配置提取到独立函数中，确保只配置一次
   */
  private static initializeMermaid(): void {
    if (this.initialized) return;
    this.initialized = true;

    console.log('🎨 正在初始化 Mermaid 配置...');
    mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral',
      securityLevel: 'loose',
      suppressErrorRendering: true,
      logLevel: 'error',
      maxTextSize: 100000,
      htmlLabels: true,
      flowchart: {
        htmlLabels: true,
        curve: 'basis',
        nodeSpacing: 60,
        rankSpacing: 60,
        padding: 20,
      },
      themeCSS: `
        /* Japanese aesthetic styles for all diagrams */
        .node rect, .node circle, .node ellipse, .node polygon, .node path {
          fill: #f8f4e6;
          stroke: #d7c4bb;
          stroke-width: 1px;
        }
        .edgePath .path {
          stroke: #9b7cb9;
          stroke-width: 1.5px;
        }
        .edgeLabel {
          background-color: transparent;
          color: #333333;
          p {
            background-color: transparent !important;
          }
        }
        .label {
          color: #333333;
        }
        .cluster rect {
          fill: #f8f4e6;
          stroke: #d7c4bb;
          stroke-width: 1px;
        }

        /* Sequence diagram specific styles */
        .actor {
          fill: #f8f4e6;
          stroke: #d7c4bb;
          stroke-width: 1px;
        }
        text.actor {
          fill: #333333;
          stroke: none;
        }
        .messageText {
          fill: #333333;
          stroke: none;
        }
        .messageLine0, .messageLine1 {
          stroke: #9b7cb9;
        }
        .noteText {
          fill: #333333;
        }

        /* Dark mode overrides - will be applied with data-theme="dark" */
        [data-theme="dark"] .node rect,
        [data-theme="dark"] .node circle,
        [data-theme="dark"] .node ellipse,
        [data-theme="dark"] .node polygon,
        [data-theme="dark"] .node path {
          fill: #222222;
          stroke: #5d4037;
        }
        [data-theme="dark"] .edgePath .path {
          stroke: #9370db;
        }
        [data-theme="dark"] .edgeLabel {
          background-color: transparent;
          color: #f0f0f0;
        }
        [data-theme="dark"] .label {
          color: #f0f0f0;
        }
        [data-theme="dark"] .cluster rect {
          fill: #222222;
          stroke: #5d4037;
        }
        [data-theme="dark"] .flowchart-link {
          stroke: #9370db;
        }

        /* Dark mode sequence diagram overrides */
        [data-theme="dark"] .actor {
          fill: #222222;
          stroke: #5d4037;
        }
        [data-theme="dark"] text.actor {
          fill: #f0f0f0;
          stroke: none;
        }
        [data-theme="dark"] .messageText {
          fill: #f0f0f0;
          stroke: none;
          font-weight: 500;
        }
        [data-theme="dark"] .messageLine0, [data-theme="dark"] .messageLine1 {
          stroke: #9370db;
          stroke-width: 1.5px;
        }
        [data-theme="dark"] .noteText {
          fill: #f0f0f0;
        }
        /* Additional styles for sequence diagram text */
        [data-theme="dark"] #sequenceNumber {
          fill: #f0f0f0;
        }
        [data-theme="dark"] text.sequenceText {
          fill: #f0f0f0;
          font-weight: 500;
        }
        [data-theme="dark"] text.loopText, [data-theme="dark"] text.loopText tspan {
          fill: #f0f0f0;
        }
        /* Add a subtle background to message text for better readability */
        [data-theme="dark"] .messageText, [data-theme="dark"] text.sequenceText {
          paint-order: stroke;
          stroke: #1a1a1a;
          stroke-width: 2px;
          stroke-linecap: round;
          stroke-linejoin: round;
        }

        /* Force text elements to be properly colored */
        text[text-anchor][dominant-baseline],
        text[text-anchor][alignment-baseline],
        .nodeLabel,
        .edgeLabel,
        .label,
        text {
          fill: #777 !important;
        }

        [data-theme="dark"] text[text-anchor][dominant-baseline],
        [data-theme="dark"] text[text-anchor][alignment-baseline],
        [data-theme="dark"] .nodeLabel,
        [data-theme="dark"] .edgeLabel,
        [data-theme="dark"] .label,
        [data-theme="dark"] text {
          fill: #f0f0f0 !important;
        }

        /* Add clickable element styles with subtle transitions */
        .clickable {
          transition: all 0.3s ease;
        }
        .clickable:hover {
          transform: scale(1.03);
          cursor: pointer;
        }
        .clickable:hover > * {
          filter: brightness(0.95);
        }
      `,
      fontFamily: 'var(--font-geist-sans), var(--font-serif-jp), sans-serif',
      fontSize: 12,
    });
    console.log('✅ Mermaid 配置初始化完成');
  }

  static async preload() {
    console.log('🔍 MermaidPreloader.preload() 被调用');
    if (this.preloadStarted) {
      console.log('⚠️ Mermaid 预加载已开始，跳过');
      return;
    }
    this.preloadStarted = true;

    try {
      // 在后台预加载 Mermaid
      console.log('🚀 开始预加载 Mermaid...');
      const start = performance.now();
      
      // 使用动态导入预加载
      await import('mermaid');
      console.log('📦 Mermaid 模块导入成功');
      
      // 初始化mermaid配置
      console.log('🎯 准备初始化 Mermaid 配置...');
      this.initializeMermaid();
      
      const end = performance.now();
      console.log(`✅ Mermaid 预加载完成，耗时: ${(end - start).toFixed(2)}ms`);
    } catch (error) {
      console.warn('⚠️ Mermaid 预加载失败:', error);
    }
  }
}

export default MermaidPreloader;
