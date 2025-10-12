// Mermaid 预加载器 - 在应用启动时预加载 Mermaid 库
class MermaidPreloader {
  private static preloadStarted = false;

  static async preload() {
    if (this.preloadStarted) return;
    this.preloadStarted = true;

    try {
      // 在后台预加载 Mermaid
      console.log('🚀 开始预加载 Mermaid...');
      const start = performance.now();
      
      // 使用动态导入预加载
      await import('mermaid');
      
      const end = performance.now();
      console.log(`✅ Mermaid 预加载完成，耗时: ${(end - start).toFixed(2)}ms`);
    } catch (error) {
      console.warn('⚠️ Mermaid 预加载失败:', error);
    }
  }
}

export default MermaidPreloader;
