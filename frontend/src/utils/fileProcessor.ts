/**
 * 文件处理工具 - 优化内存使用
 */

interface FileChunk {
  data: Uint8Array;
  index: number;
  total: number;
}

interface ProcessedFile {
  name: string;
  size: number;
  type: string;
  lastModified: number;
  webkitRelativePath: string;
  chunks?: FileChunk[];
}

export class FileProcessor {
  private static readonly CHUNK_SIZE = 1024 * 1024; // 1MB chunks
  private static readonly MAX_MEMORY_USAGE = 100 * 1024 * 1024; // 100MB limit

  /**
   * 检查文件是否可以安全处理
   */
  static canProcessFiles(files: FileList): { canProcess: boolean; reason?: string } {
    const totalSize = Array.from(files).reduce((sum, file) => sum + file.size, 0);
    
    if (totalSize > this.MAX_MEMORY_USAGE) {
      return {
        canProcess: false,
        reason: `文件总大小 ${this.formatFileSize(totalSize)} 超过限制 ${this.formatFileSize(this.MAX_MEMORY_USAGE)}`
      };
    }

    // 检查单个文件大小
    const largeFiles = Array.from(files).filter(file => file.size > 50 * 1024 * 1024);
    if (largeFiles.length > 0) {
      return {
        canProcess: false,
        reason: `包含过大的文件: ${largeFiles.map(f => f.name).join(', ')}`
      };
    }

    return { canProcess: true };
  }

  /**
   * 流式读取文件，避免内存溢出
   */
  static async processFileStream(file: File): Promise<ProcessedFile> {
    const chunks: FileChunk[] = [];
    const totalChunks = Math.ceil(file.size / this.CHUNK_SIZE);
    
    for (let i = 0; i < totalChunks; i++) {
      const start = i * this.CHUNK_SIZE;
      const end = Math.min(start + this.CHUNK_SIZE, file.size);
      const chunk = file.slice(start, end);
      
      const arrayBuffer = await chunk.arrayBuffer();
      chunks.push({
        data: new Uint8Array(arrayBuffer),
        index: i,
        total: totalChunks
      });
      
      // 强制垃圾回收（如果可用）
      if (typeof window !== 'undefined' && (window as any).gc) {
        (window as any).gc();
      }
    }

    return {
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified,
      webkitRelativePath: (file as any).webkitRelativePath || "",
      chunks
    };
  }

  /**
   * 轻量级文件信息提取（不读取内容）
   */
  static extractFileInfo(files: FileList): ProcessedFile[] {
    return Array.from(files).map(file => ({
      name: file.name,
      size: file.size,
      type: file.type,
      lastModified: file.lastModified,
      webkitRelativePath: (file as any).webkitRelativePath || ""
      // 不包含 chunks 或 content
    }));
  }

  /**
   * 使用 Web Workers 处理大文件
   */
  static async processWithWorker(file: File): Promise<ProcessedFile> {
    return new Promise((resolve, reject) => {
      const worker = new Worker('/workers/fileProcessor.js');
      
      worker.postMessage({
        file: file,
        chunkSize: this.CHUNK_SIZE
      });
      
      worker.onmessage = (event) => {
        const { success, data, error } = event.data;
        if (success) {
          resolve(data);
        } else {
          reject(new Error(error));
        }
        worker.terminate();
      };
      
      worker.onerror = (error) => {
        reject(error);
        worker.terminate();
      };
    });
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * 内存使用监控
   */
  static getMemoryUsage(): { used: number; total: number } | null {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize
      };
    }
    return null;
  }

  /**
   * 清理内存
   */
  static forceGarbageCollection(): void {
    // 创建大量临时对象然后释放，触发垃圾回收
    const temp = new Array(1000).fill(null).map(() => new Array(1000).fill(0));
    temp.length = 0;
    
    // 如果浏览器支持手动垃圾回收
    if (typeof window !== 'undefined' && (window as any).gc) {
      (window as any).gc();
    }
  }
}

/**
 * 文件上传状态管理
 */
export class FileUploadManager {
  private files: File[] = [];
  private processedFiles: ProcessedFile[] = [];
  
  constructor(private maxMemoryUsage: number = 100 * 1024 * 1024) {}
  
  async addFiles(fileList: FileList): Promise<void> {
    const newFiles = Array.from(fileList);
    const totalSize = [...this.files, ...newFiles]
      .reduce((sum, file) => sum + file.size, 0);
    
    if (totalSize > this.maxMemoryUsage) {
      throw new Error(`总文件大小超过限制: ${FileProcessor.formatFileSize(this.maxMemoryUsage)}`);
    }
    
    this.files.push(...newFiles);
  }
  
  async processFiles(onProgress?: (progress: number) => void): Promise<ProcessedFile[]> {
    this.processedFiles = [];
    
    for (let i = 0; i < this.files.length; i++) {
      const file = this.files[i];
      
      // 对于小文件，直接提取信息
      if (file.size < 1024 * 1024) { // 1MB以下
        this.processedFiles.push({
          name: file.name,
          size: file.size,
          type: file.type,
          lastModified: file.lastModified,
          webkitRelativePath: (file as any).webkitRelativePath || ""
        });
      } else {
        // 大文件使用流式处理
        const processed = await FileProcessor.processFileStream(file);
        this.processedFiles.push(processed);
      }
      
      if (onProgress) {
        onProgress((i + 1) / this.files.length * 100);
      }
      
      // 定期清理内存
      if (i % 10 === 0) {
        FileProcessor.forceGarbageCollection();
      }
    }
    
    return this.processedFiles;
  }
  
  getFiles(): File[] {
    return this.files;
  }
  
  getProcessedFiles(): ProcessedFile[] {
    return this.processedFiles;
  }
  
  clear(): void {
    this.files = [];
    this.processedFiles = [];
    FileProcessor.forceGarbageCollection();
  }
}
