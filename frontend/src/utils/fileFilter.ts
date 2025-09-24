/**
 * 综合文件过滤器
 * 结合默认规则和 .gitignore 规则进行文件过滤
 */

import { 
  shouldIgnoreFile, 
  shouldIgnoreDirectory, 
  isSupportedCodeFile,
  DEFAULT_IGNORE_DIRS,
  DEFAULT_IGNORE_FILES,
  DEFAULT_IGNORE_EXTENSIONS 
} from './fileFilterConfig';
import { GitignoreParser, parseGitignoreFromFiles, createDefaultGitignoreParser } from './gitignoreParser';

export interface FilterOptions {
  useGitignore: boolean;
  useDefaultRules: boolean;
  onlyCodeFiles: boolean;
  customIgnorePatterns?: string[];
}

export interface FilterResult {
  filteredFiles: File[];
  ignoredFiles: File[];
  stats: {
    total: number;
    filtered: number;
    ignored: number;
    ignoredByDefault: number;
    ignoredByGitignore: number;
    ignoredByExtension: number;
  };
}

export class FileFilter {
  private gitignoreParser: GitignoreParser;
  private options: FilterOptions;

  constructor(options: Partial<FilterOptions> = {}) {
    this.options = {
      useGitignore: true,
      useDefaultRules: true,
      onlyCodeFiles: false,
      ...options,
    };
    
    this.gitignoreParser = createDefaultGitignoreParser();
  }

  /**
   * 初始化过滤器（解析 .gitignore 文件）
   */
  async initialize(files: FileList): Promise<void> {
    if (this.options.useGitignore) {
      this.gitignoreParser = await parseGitignoreFromFiles(files);
      
      // 如果没有找到 .gitignore，使用默认规则
      if (this.gitignoreParser.getRules().length === 0) {
        this.gitignoreParser = createDefaultGitignoreParser();
      }
    }
  }

  /**
   * 过滤文件列表
   */
  async filterFiles(files: FileList): Promise<FilterResult> {
    // 初始化过滤器
    await this.initialize(files);

    const filteredFiles: File[] = [];
    const ignoredFiles: File[] = [];
    const stats = {
      total: files.length,
      filtered: 0,
      ignored: 0,
      ignoredByDefault: 0,
      ignoredByGitignore: 0,
      ignoredByExtension: 0,
    };

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileName = file.name;
      const filePath = (file as any).webkitRelativePath || fileName;
      
      const filterResult = this.shouldIgnoreFile(fileName, filePath);
      
      if (filterResult.ignored) {
        ignoredFiles.push(file);
        stats.ignored++;
        
        // 统计忽略原因
        if (filterResult.reason === 'default') {
          stats.ignoredByDefault++;
        } else if (filterResult.reason === 'gitignore') {
          stats.ignoredByGitignore++;
        } else if (filterResult.reason === 'extension') {
          stats.ignoredByExtension++;
        }
      } else {
        filteredFiles.push(file);
        stats.filtered++;
      }
    }

    return {
      filteredFiles,
      ignoredFiles,
      stats,
    };
  }

  /**
   * 检查单个文件是否应该被忽略
   */
  private shouldIgnoreFile(fileName: string, filePath: string): { ignored: boolean; reason?: string } {
    // 1. 检查默认规则
    if (this.options.useDefaultRules) {
      if (shouldIgnoreFile(fileName, filePath)) {
        return { ignored: true, reason: 'default' };
      }
    }

    // 2. 检查 .gitignore 规则
    if (this.options.useGitignore) {
      if (this.gitignoreParser.isIgnored(filePath, false)) {
        return { ignored: true, reason: 'gitignore' };
      }
    }

    // 3. 如果只要代码文件，检查是否是支持的代码文件
    if (this.options.onlyCodeFiles) {
      if (!isSupportedCodeFile(fileName)) {
        return { ignored: true, reason: 'extension' };
      }
    }

    // 4. 检查自定义忽略模式
    if (this.options.customIgnorePatterns) {
      for (const pattern of this.options.customIgnorePatterns) {
        if (this.matchesPattern(filePath, pattern)) {
          return { ignored: true, reason: 'custom' };
        }
      }
    }

    return { ignored: false };
  }

  /**
   * 简单的模式匹配（支持 * 通配符）
   */
  private matchesPattern(filePath: string, pattern: string): boolean {
    const regexPattern = pattern
      .replace(/[.+^${}()|[\]\\]/g, '\\$&')
      .replace(/\*/g, '.*');
    
    const regex = new RegExp(regexPattern, 'i');
    return regex.test(filePath);
  }

  /**
   * 获取过滤统计信息
   */
  getFilterStats(): { defaultRules: number; gitignoreRules: number } {
    return {
      defaultRules: DEFAULT_IGNORE_DIRS.size + DEFAULT_IGNORE_FILES.size + DEFAULT_IGNORE_EXTENSIONS.size,
      gitignoreRules: this.gitignoreParser.getRules().length,
    };
  }

  /**
   * 更新过滤选项
   */
  updateOptions(options: Partial<FilterOptions>): void {
    this.options = { ...this.options, ...options };
  }
}

/**
 * 便捷函数：快速过滤文件列表
 */
export async function quickFilterFiles(
  files: FileList, 
  options: Partial<FilterOptions> = {}
): Promise<FilterResult> {
  const filter = new FileFilter(options);
  return await filter.filterFiles(files);
}

/**
 * 便捷函数：只获取代码文件
 */
export async function getCodeFilesOnly(files: FileList): Promise<File[]> {
  const result = await quickFilterFiles(files, { onlyCodeFiles: true });
  return result.filteredFiles;
}

/**
 * 便捷函数：应用所有过滤规则
 */
export async function applyAllFilters(files: FileList): Promise<File[]> {
  const result = await quickFilterFiles(files, {
    useGitignore: true,
    useDefaultRules: true,
    onlyCodeFiles: false,
  });
  return result.filteredFiles;
}
