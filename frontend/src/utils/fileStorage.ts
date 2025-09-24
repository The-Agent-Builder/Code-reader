/**
 * 文件存储工具类
 * 用于在页面间传递FileList，避免sessionStorage配额限制
 */

class FileStorage {
  private static instance: FileStorage;
  private fileList: FileList | null = null;

  private constructor() {}

  public static getInstance(): FileStorage {
    if (!FileStorage.instance) {
      FileStorage.instance = new FileStorage();
    }
    return FileStorage.instance;
  }

  public setFiles(files: FileList): void {
    this.fileList = files;
  }

  public getFiles(): FileList | null {
    return this.fileList;
  }

  public clearFiles(): void {
    this.fileList = null;
  }

  public hasFiles(): boolean {
    return this.fileList !== null && this.fileList.length > 0;
  }
}

export default FileStorage;
