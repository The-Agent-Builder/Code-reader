import mermaid from 'mermaid';

// 初始化mermaid配置
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

interface MermaidBlock {
  type: 'mermaid';
  content: string;
  id: string;
}

/**
 * 预处理markdown内容，将mermaid代码块转换为SVG
 * @param markdownContent 原始markdown内容
 * @returns 处理后的markdown内容，其中mermaid代码块被替换为SVG
 */
export async function preprocessMermaidInMarkdown(markdownContent: string): Promise<string> {
  if (!markdownContent) return markdownContent;

  // 匹配mermaid代码块的正则表达式
  const mermaidRegex = /```mermaid\n([\s\S]*?)\n```/g;
  const mermaidBlocks: MermaidBlock[] = [];
  let match;

  // 找到所有mermaid代码块
  while ((match = mermaidRegex.exec(markdownContent)) !== null) {
    const content = match[1].trim();
    if (content) {
      mermaidBlocks.push({
        type: 'mermaid',
        content,
        id: `mermaid-${Math.random().toString(36).substring(2, 9)}`,
      });
    }
  }

  if (mermaidBlocks.length === 0) {
    return markdownContent;
  }

  // 并行处理所有mermaid代码块
  const svgPromises = mermaidBlocks.map(async (block) => {
    try {
      const { svg } = await mermaid.render(block.id, block.content);
      return {
        id: block.id,
        svg,
        originalBlock: match,
      };
    } catch (error) {
      console.error(`Failed to render mermaid diagram ${block.id}:`, error);
      // 如果渲染失败，转换为代码格式让其显示
      const errorSvg = '```python\n' + `${block.content}` + '\n```\n\n';
      return {
        id: block.id,
        svg: errorSvg,
        originalBlock: match,
      };
    }
  });

  const svgResults = await Promise.all(svgPromises);

  // 替换原始markdown中的mermaid代码块
  let processedContent = markdownContent;
  
  // 重新匹配并替换
  const mermaidRegex2 = /```mermaid\n([\s\S]*?)\n```/g;
  let matchIndex = 0;
  
  processedContent = processedContent.replace(mermaidRegex2, () => {
    if (matchIndex < svgResults.length) {
      const result = svgResults[matchIndex];
      matchIndex++;
      return result.svg;
    }
    return match[0]; // 如果索引超出范围，保持原样
  });

  return processedContent;
}

/**
 * 检查内容是否包含mermaid代码块
 * @param content markdown内容
 * @returns 是否包含mermaid代码块
 */
export function hasMermaidBlocks(content: string): boolean {
  return /```mermaid\n[\s\S]*?\n```/.test(content);
}

/**
 * 提取所有mermaid代码块的内容
 * @param content markdown内容
 * @returns mermaid代码块内容数组
 */
export function extractMermaidBlocks(content: string): string[] {
  const mermaidRegex = /```mermaid\n([\s\S]*?)\n```/g;
  const blocks: string[] = [];
  let match;

  while ((match = mermaidRegex.exec(content)) !== null) {
    const content = match[1].trim();
    if (content) {
      blocks.push(content);
    }
  }

  return blocks;
}
