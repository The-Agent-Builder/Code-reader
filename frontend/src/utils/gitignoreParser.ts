/**
 * .gitignore 文件解析器
 * 支持常见的 gitignore 规则
 */

export interface GitignoreRule {
  pattern: string;
  isNegation: boolean;
  isDirectory: boolean;
  regex: RegExp;
}

export class GitignoreParser {
  private rules: GitignoreRule[] = [];

  /**
   * 解析 .gitignore 文件内容
   */
  parse(content: string): void {
    this.rules = [];
    const lines = content.split('\n');

    for (const line of lines) {
      const trimmed = line.trim();
      
      // 跳过空行和注释
      if (!trimmed || trimmed.startsWith('#')) {
        continue;
      }

      this.addRule(trimmed);
    }
  }

  /**
   * 添加一个 gitignore 规则
   */
  private addRule(pattern: string): void {
    let isNegation = false;
    let isDirectory = false;
    let cleanPattern = pattern;

    // 处理否定规则 (!)
    if (pattern.startsWith('!')) {
      isNegation = true;
      cleanPattern = pattern.slice(1);
    }

    // 处理目录规则 (/)
    if (cleanPattern.endsWith('/')) {
      isDirectory = true;
      cleanPattern = cleanPattern.slice(0, -1);
    }

    // 转换为正则表达式
    const regex = this.patternToRegex(cleanPattern);

    this.rules.push({
      pattern: cleanPattern,
      isNegation,
      isDirectory,
      regex,
    });
  }

  /**
   * 将 gitignore 模式转换为正则表达式
   */
  private patternToRegex(pattern: string): RegExp {
    // 转义特殊字符，但保留 * 和 ?
    let regexPattern = pattern
      .replace(/[.+^${}()|[\]\\]/g, '\\$&')
      .replace(/\*/g, '.*')
      .replace(/\?/g, '.');

    // 处理开头的斜杠
    if (pattern.startsWith('/')) {
      regexPattern = '^' + regexPattern.slice(1);
    } else {
      // 如果没有开头斜杠，可以匹配任何路径
      regexPattern = '(^|/)' + regexPattern;
    }

    // 处理结尾
    regexPattern += '($|/)';

    return new RegExp(regexPattern);
  }

  /**
   * 检查文件路径是否被忽略
   */
  isIgnored(filePath: string, isDirectory: boolean = false): boolean {
    let ignored = false;

    for (const rule of this.rules) {
      // 如果规则是针对目录的，但当前项不是目录，跳过
      if (rule.isDirectory && !isDirectory) {
        continue;
      }

      // 检查路径是否匹配规则
      if (this.matchesRule(filePath, rule)) {
        if (rule.isNegation) {
          ignored = false; // 否定规则，不忽略
        } else {
          ignored = true; // 普通规则，忽略
        }
      }
    }

    return ignored;
  }

  /**
   * 检查路径是否匹配规则
   */
  private matchesRule(filePath: string, rule: GitignoreRule): boolean {
    // 标准化路径（移除开头的斜杠）
    const normalizedPath = filePath.startsWith('/') ? filePath.slice(1) : filePath;
    
    return rule.regex.test(normalizedPath);
  }

  /**
   * 获取所有规则
   */
  getRules(): GitignoreRule[] {
    return [...this.rules];
  }

  /**
   * 清空所有规则
   */
  clear(): void {
    this.rules = [];
  }
}

/**
 * 从文件列表中查找并解析 .gitignore 文件
 */
export async function parseGitignoreFromFiles(files: FileList): Promise<GitignoreParser> {
  const parser = new GitignoreParser();
  
  // 查找 .gitignore 文件
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const fileName = file.name;
    const filePath = (file as any).webkitRelativePath || fileName;
    
    // 检查是否是 .gitignore 文件
    if (fileName === '.gitignore' || filePath.endsWith('/.gitignore')) {
      try {
        const content = await file.text();
        parser.parse(content);
        console.log(`Found and parsed .gitignore: ${filePath}`);
        break; // 只使用第一个找到的 .gitignore 文件
      } catch (error) {
        console.warn(`Failed to read .gitignore file: ${filePath}`, error);
      }
    }
  }
  
  return parser;
}

/**
 * 创建一个默认的 gitignore 解析器（包含常见规则）
 */
export function createDefaultGitignoreParser(): GitignoreParser {
  const parser = new GitignoreParser();
  
  // 添加一些常见的默认规则
  const defaultRules = [
    '# Dependencies',
    'node_modules/',
    '__pycache__/',
    '.venv/',
    'venv/',
    
    '# Build outputs',
    'dist/',
    'build/',
    'target/',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    
    '# IDE',
    '.vscode/',
    '.idea/',
    '*.swp',
    '*.swo',
    
    '# OS',
    '.DS_Store',
    'Thumbs.db',
    
    '# Logs',
    '*.log',
    'logs/',
    
    '# Lock files',
    'package-lock.json',
    'yarn.lock',
    'uv.lock',
    'Pipfile.lock',
  ];
  
  parser.parse(defaultRules.join('\n'));
  return parser;
}

/**
 * 合并多个 gitignore 解析器
 */
export function mergeGitignoreParsers(...parsers: GitignoreParser[]): GitignoreParser {
  const merged = new GitignoreParser();
  
  for (const parser of parsers) {
    for (const rule of parser.getRules()) {
      // 重新添加规则（这会重新构建正则表达式）
      const pattern = rule.isNegation ? '!' + rule.pattern : rule.pattern;
      const finalPattern = rule.isDirectory ? pattern + '/' : pattern;
      merged.parse(finalPattern);
    }
  }
  
  return merged;
}
