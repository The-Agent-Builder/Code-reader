// 分页内容接口
export interface PaginatedContent {
  id: string;
  title: string;
  level: number;
  content: string;
  children?: PaginatedContent[];
}

// 生成标题ID - 与 DeepWikiSidebar.tsx 中的逻辑完全一致
const generateSectionId = (title: string): string => {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5\s-]/g, "") // 保留连字符
    .replace(/\s+/g, "-")
    .replace(/^-+|-+$/g, ""); // 移除开头和结尾的连字符
};

// 验证是否是有效的标题 - 与 DeepWikiSidebar.tsx 中的逻辑完全一致
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

/**
 * 将markdown内容按标题分页
 * @param content 原始markdown内容
 * @returns 分页后的内容数组
 */
export function paginateMarkdownContent(content: string): PaginatedContent[] {
  if (!content) return [];

  const lines = content.split("\n");
  const sections: PaginatedContent[] = [];
  const stack: PaginatedContent[] = [];
  let inCodeBlock = false;
  let currentSection: PaginatedContent | null = null;
  let currentContent: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmedLine = line.trim();

    // 检查是否在代码块中
    if (trimmedLine.startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      // 将代码块标记行也包含在内容中
      if (currentSection) {
        currentContent.push(line);
      }
      continue;
    }

    // 如果在代码块中，将内容添加到当前章节
    if (inCodeBlock) {
      if (currentSection) {
        currentContent.push(line);
      }
      continue;
    }

    // 只处理一级标题：确保 # 后面有空格，且不在行首有其他字符
    const h1Match = line.match(/^# (.+)$/);

    if (h1Match) {
      const title = h1Match[1].trim();

      // 过滤掉一些明显不是标题的内容
      if (isValidTitle(title)) {
        // 保存前一个章节的内容
        if (currentSection) {
          currentSection.content = currentContent.join("\n");
        }

        const id = generateSectionId(title);
        const section: PaginatedContent = {
          id,
          title,
          level: 1,
          content: "",
          children: [],
        };

        sections.push(section);
        stack.length = 0;
        stack.push(section);
        currentSection = section;
        currentContent = [];
      } else {
        // 如果不是有效标题，将内容添加到当前章节
        if (currentSection) {
          currentContent.push(line);
        }
      }
    } else {
      // 普通内容行，添加到当前章节
      if (currentSection) {
        currentContent.push(line);
      } else {
        // 如果还没有任何章节，创建一个默认的概览章节
        if (sections.length === 0) {
          const overviewSection: PaginatedContent = {
            id: "overview",
            title: "项目概览",
            level: 1,
            content: "",
            children: [],
          };
          sections.push(overviewSection);
          stack.push(overviewSection);
          currentSection = overviewSection;
          currentContent = [];
        }
        currentContent.push(line);
      }
    }
  }

  // 保存最后一个章节的内容
  if (currentSection) {
    currentSection.content = currentContent.join("\n");
  }

  // 如果没有找到任何标题，将整个内容作为概览章节
  if (sections.length === 0) {
    const overviewSection: PaginatedContent = {
      id: "overview",
      title: "项目概览",
      level: 1,
      content: content,
      children: [],
    };
    sections.push(overviewSection);
  }
  console.log(sections,"sectionssectionssections")
  return sections;
}

/**
 * 根据章节ID获取对应的内容
 * @param sections 分页后的内容数组
 * @param sectionId 章节ID
 * @returns 对应的内容，如果找不到返回null
 */
export function getContentBySectionId(
  sections: PaginatedContent[],
  sectionId: string
): string | null {
  for (const section of sections) {
    if (section.id === sectionId) {
      return section.content;
    }
    
    // 递归查找子章节
    if (section.children) {
      for (const child of section.children) {
        if (child.id === sectionId) {
          return child.content;
        }
      }
    }
  }
  
  return null;
}

/**
 * 获取所有章节的扁平化列表（包括子章节）
 * @param sections 分页后的内容数组
 * @returns 扁平化的章节列表
 */
export function getAllSections(sections: PaginatedContent[]): PaginatedContent[] {
  const result: PaginatedContent[] = [];
  
  for (const section of sections) {
    result.push(section);
    
    if (section.children) {
      result.push(...section.children);
    }
  }
  
  return result;
}
