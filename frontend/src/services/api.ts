/**
 * API服务类 - 用于与后端API通信
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// 类型定义
export interface RepositoryInfo {
  id: number;
  name: string;
  full_name: string;
  url: string;
  description?: string;
  primary_language?: string;
  languages: LanguageInfo[];
  stars?: number;
  forks?: number;
  watchers?: number;
  size?: number;
  created_at?: string;
  updated_at?: string;
  topics: string[];
  license?: string;
  default_branch?: string;
}

export interface LanguageInfo {
  name: string;
  percentage: number;
  bytes: number;
  color?: string;
}

export interface AnalysisTaskInfo {
  id: number;
  status: "pending" | "running" | "completed" | "failed";
  start_time: string;
  end_time?: string;
  total_files: number;
  successful_files: number;
  failed_files: number;
  progress_percentage: number;
}

export interface ProjectDetailResponse {
  repository: RepositoryInfo;
  analysis_task?: AnalysisTaskInfo;
  file_count: number;
  analysis_items_count: number;
  last_analysis_time?: string;
}

export interface ProjectOverviewResponse {
  success: boolean;
  data: {
    repository: RepositoryInfo;
    analysis_task?: AnalysisTaskInfo;
    file_statistics: Record<string, any>;
    language_distribution: LanguageInfo[];
    key_metrics: Record<string, any>;
    readme_content?: string;
  };
  message?: string;
}

export interface SearchRequest {
  query: string;
  search_type: "all" | "function" | "class" | "file";
  limit: number;
}

export interface SearchResultItem {
  id: number;
  title: string;
  description?: string;
  file_path: string;
  language?: string;
  item_type: string;
  source?: string;
  code?: string;
  relevance_score: number;
}

export interface SearchResultResponse {
  success: boolean;
  repository_name: string;
  query: string;
  search_type: string;
  results: SearchResultItem[];
  total_results: number;
  message?: string;
}

export interface SystemStatisticsResponse {
  success: boolean;
  total_repositories: number;
  total_analyses: number;
  total_files_analyzed: number;
  total_analysis_items: number;
  language_statistics: Record<string, number>;
  recent_analyses: Array<Record<string, any>>;
  message?: string;
}

// API服务类
export class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${url}`, error);
      throw error;
    }
  }

  // 健康检查
  async healthCheck(): Promise<{
    status: string;
    timestamp: string;
    database: string;
  }> {
    return this.request("/health");
  }

  // 获取项目列表
  async getProjects(
    params: {
      page?: number;
      page_size?: number;
      search?: string;
      language?: string;
    } = {}
  ): Promise<{
    projects: RepositoryInfo[];
    total: number;
    page: number;
    page_size: number;
    has_next: boolean;
    has_prev: boolean;
  }> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString());
      }
    });

    return this.request(`/api/projects?${searchParams.toString()}`);
  }

  // 获取项目详情
  async getProjectDetail(repoName: string): Promise<ProjectDetailResponse> {
    return this.request(`/api/projects/${encodeURIComponent(repoName)}`);
  }

  // 获取项目概述
  async getProjectOverview(repoName: string): Promise<ProjectOverviewResponse> {
    return this.request(
      `/api/projects/${encodeURIComponent(repoName)}/overview`
    );
  }

  // 获取项目文件结构
  async getProjectFiles(
    repoName: string,
    path?: string
  ): Promise<{
    success: boolean;
    repository_name: string;
    files: Array<{
      path: string;
      name: string;
      type: string;
      size?: number;
      language?: string;
      last_modified?: string;
    }>;
    total_files: number;
    message?: string;
  }> {
    const params = path ? `?path=${encodeURIComponent(path)}` : "";
    return this.request(
      `/api/projects/${encodeURIComponent(repoName)}/files${params}`
    );
  }

  // 获取项目分析结果
  async getProjectAnalysis(
    repoName: string,
    version?: string
  ): Promise<{
    success: boolean;
    repository_name: string;
    analysis_task: AnalysisTaskInfo;
    files: Array<{
      file_path: string;
      language?: string;
      analysis_timestamp: string;
      status: string;
      items: Array<{
        id: number;
        title: string;
        description?: string;
        source?: string;
        language?: string;
        code?: string;
        start_line?: number;
        end_line?: number;
        item_type: string;
      }>;
      functions_count: number;
      classes_count: number;
      lines_of_code: number;
    }>;
    summary: Record<string, any>;
    message?: string;
  }> {
    const params = version ? `?version=${encodeURIComponent(version)}` : "";
    return this.request(
      `/api/projects/${encodeURIComponent(repoName)}/analysis${params}`
    );
  }

  // 获取分析摘要
  async getAnalysisSummary(repoName: string): Promise<{
    success: boolean;
    repository_name: string;
    total_files: number;
    analyzed_files: number;
    total_functions: number;
    total_classes: number;
    total_lines: number;
    language_breakdown: Record<string, number>;
    analysis_completion_time?: string;
    message?: string;
  }> {
    return this.request(
      `/api/projects/${encodeURIComponent(repoName)}/analysis/summary`
    );
  }

  // 获取文件分析详情
  async getFileAnalysis(
    repoName: string,
    filePath: string
  ): Promise<{
    success: boolean;
    repository_name: string;
    file_path: string;
    file_analysis: {
      file_path: string;
      language?: string;
      analysis_timestamp: string;
      status: string;
      items: Array<{
        id: number;
        title: string;
        description?: string;
        source?: string;
        language?: string;
        code?: string;
        start_line?: number;
        end_line?: number;
        item_type: string;
      }>;
      functions_count: number;
      classes_count: number;
      lines_of_code: number;
    };
    message?: string;
  }> {
    return this.request(
      `/api/projects/${encodeURIComponent(
        repoName
      )}/analysis/files/${encodeURIComponent(filePath)}`
    );
  }

  // 在项目中搜索
  async searchInProject(
    repoName: string,
    searchRequest: SearchRequest
  ): Promise<SearchResultResponse> {
    return this.request(
      `/api/projects/${encodeURIComponent(repoName)}/search`,
      {
        method: "POST",
        body: JSON.stringify(searchRequest),
      }
    );
  }

  // 获取系统统计
  async getSystemStatistics(): Promise<SystemStatisticsResponse> {
    return this.request("/api/statistics");
  }

  // 根据仓库名称获取仓库信息（新增）
  async getRepositoryByName(
    name: string,
    exactMatch: boolean = true,
    includeTasks: boolean = true
  ): Promise<{
    status: string;
    message: string;
    search_name: string;
    total_repositories?: number;
    // 精确匹配时返回单个repository对象
    repository?: {
      id: number;
      name: string;
      full_name: string;
      url: string;
      description: string;
      language: string;
      created_at: string;
      updated_at: string;
      total_tasks?: number;
      tasks?: Array<{
        id: number;
        repository_id: number;
        status: string;
        start_time: string;
        end_time: string | null;
        total_files: number;
        successful_files: number;
        failed_files: number;
        analysis_config: any;
      }>;
    };
    // 模糊匹配时返回repositories数组
    repositories?: Array<{
      id: number;
      name: string;
      full_name: string;
      url: string;
      description: string;
      language: string;
      created_at: string;
      updated_at: string;
      total_tasks?: number;
      tasks?: Array<{
        id: number;
        repository_id: number;
        status: string;
        start_time: string;
        end_time: string | null;
        total_files: number;
        successful_files: number;
        failed_files: number;
        analysis_config: any;
      }>;
    }>;
    statistics?: any;
  }> {
    const params = new URLSearchParams({
      name,
      exact_match: exactMatch.toString(),
      include_tasks: includeTasks.toString(),
      include_statistics: "true",
    });

    return this.request(`/api/repository/repositories?${params}`);
  }

  // 根据任务ID获取文件列表（新增）
  async getFilesByTaskId(taskId: number): Promise<{
    status: string;
    message: string;
    task_id: number;
    total_files: number;
    files: Array<{
      id: number;
      task_id: number;
      file_path: string;
      file_type: string;
      file_size: number;
      analysis_status: string;
      created_at: string;
    }>;
    statistics?: any;
  }> {
    console.log(`Making request to: /api/repository/files/${taskId}`);
    const response = await this.request(`/api/repository/files/${taskId}`);
    console.log(`Files API response for task ${taskId}:`, response);
    return response;
  }

  // 根据文件分析ID获取分析项（新增）
  async getAnalysisItemsByFileId(fileAnalysisId: number): Promise<{
    status: string;
    message: string;
    file_analysis_id: number;
    total_items: number;
    filtered_items: number;
    returned_items: number;
    items: Array<{
      id: number;
      file_analysis_id: number;
      search_target_id: number | null;
      title: string;
      description: string;
      source: string;
      language: string;
      code: string;
      start_line: number;
      end_line: number;
      created_at: string;
    }>;
    statistics?: any;
  }> {
    console.log(
      `Making request to: /api/repository/analysis-items/${fileAnalysisId}`
    );
    const response = await this.request(
      `/api/repository/analysis-items/${fileAnalysisId}`
    );
    console.log(
      `Analysis items API response for file_analysis_id ${fileAnalysisId}:`,
      response
    );
    return response;
  }

  // 上传仓库文件夹（新增）
  async uploadRepository(
    files: FileList,
    repositoryName: string
  ): Promise<{
    status: string;
    message: string;
    repository_name: string;
    repository_id?: number;
    local_path?: string;
    md5_directory_name?: string;
    upload_summary?: {
      total_files_uploaded: number;
      successful_files: number;
      failed_files: number;
      total_size_bytes: number;
      total_size_formatted: string;
    };
    folder_structure?: Record<string, any>;
    file_analysis?: {
      file_type_summary: {
        code_files: number;
        config_files: number;
        documentation_files: number;
        image_files: number;
        other_files: number;
      };
      file_extensions: Record<string, number>;
      folder_depth: number;
      folder_count: number;
      is_likely_code_project: boolean;
    };
    sample_files?: Array<{
      filename: string;
      size: number;
      path: string;
      extension: string;
      relative_path: string;
    }>;
    errors?: Array<{
      filename: string;
      error: string;
    }>;
  }> {
    const formData = new FormData();

    // 添加仓库名称
    formData.append("repository_name", repositoryName);

    // 添加所有文件，确保文件名包含完整路径
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const relativePath = (file as any).webkitRelativePath || file.name;

      // 创建新的 File 对象，使用完整路径作为文件名
      const fileWithPath = new File([file], relativePath, {
        type: file.type,
        lastModified: file.lastModified,
      });

      formData.append("files", fileWithPath);
    }

    console.log(
      `Uploading repository: ${repositoryName} with ${files.length} files`
    );

    const response = await fetch(`${this.baseUrl}/api/repository/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(`Upload response:`, result);
    return result;
  }

  // 创建分析任务
  async createAnalysisTask(taskData: {
    repository_id: number;
    total_files?: number;
    successful_files?: number;
    failed_files?: number;
    code_lines?: number;
    module_count?: number;
    status?: string;
    start_time?: string;
    task_index?: string;
  }): Promise<{
    status: string;
    message: string;
    task: {
      id: number;
      repository_id: number;
      total_files: number;
      successful_files: number;
      failed_files: number;
      code_lines: number;
      module_count: number;
      status: string;
      start_time: string;
      end_time?: string;
      task_index?: string;
    };
  }> {
    const response = await fetch(
      `${this.baseUrl}/api/repository/analysis-tasks`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(taskData),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(`Create analysis task response:`, result);
    return result;
  }

  // 获取分析任务信息
  async getAnalysisTask(taskId: number): Promise<{
    status: string;
    message?: string;
    task?: {
      id: number;
      status: string;
      start_time: string;
      end_time?: string;
      total_files: number;
      successful_files: number;
      failed_files: number;
      progress_percentage: number;
      task_index?: string;
    };
  }> {
    const response = await fetch(
      `${this.baseUrl}/api/repository/analysis-tasks/${taskId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(`Get analysis task response:`, result);
    return result;
  }

  // 更新分析任务状态
  async updateAnalysisTask(
    taskId: number,
    updateData: {
      status?: string;
      successful_files?: number;
      failed_files?: number;
      code_lines?: number;
      module_count?: number;
      end_time?: string;
      task_index?: string;
    }
  ): Promise<{
    status: string;
    message: string;
    task: {
      id: number;
      repository_id: number;
      total_files: number;
      successful_files: number;
      failed_files: number;
      code_lines: number;
      module_count: number;
      status: string;
      start_time: string;
      end_time?: string;
      task_index?: string;
    };
  }> {
    const response = await fetch(
      `${this.baseUrl}/api/repository/analysis-tasks/${taskId}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(`Update analysis task response:`, result);
    return result;
  }

  // 获取任务队列状态
  async getQueueStatus(): Promise<{
    status: string;
    message: string;
    queue_info: {
      total_pending: number;
      running_tasks: number;
      estimated_wait_time_minutes: number;
      has_queue: boolean;
      pending_task_ids: number[];
    };
  }> {
    const response = await fetch(
      `${this.baseUrl}/api/repository/analysis-tasks/queue/status`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(`Queue status response:`, result);
    return result;
  }

  // 创建文件分析记录
  async createFileAnalysis(fileData: {
    task_id: number;
    file_path: string;
    language: string;
    analysis_version: string;
    status: string;
    code_lines: number;
    code_content: string;
    file_analysis: string;
    dependencies: string;
    error_message: string;
  }): Promise<{
    status: string;
    message: string;
    file_analysis: {
      id: number;
      task_id: number;
      file_path: string;
      language: string;
      analysis_version: string;
      status: string;
      code_lines: number;
      code_content: string;
      file_analysis: string;
      dependencies: string;
      analysis_timestamp: string;
      error_message: string;
    };
  }> {
    const response = await fetch(
      `${this.baseUrl}/api/repository/file-analysis`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(fileData),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log(`Create file analysis response:`, result);
    return result;
  }

  // RAG 知识库相关方法

  // 检查RAG服务健康状态
  async checkRAGHealth(): Promise<{
    status: string;
    message?: string;
  }> {
    try {
      // 从环境变量或配置中获取RAG_BASE_URL
      const ragBaseUrl = "http://nodeport.sensedeal.vip:32421"; // 这里应该从配置中读取

      const response = await fetch(`${ragBaseUrl}/health`, {
        method: "GET",
        timeout: 10000,
      });

      if (response.ok) {
        return { status: "success", message: "RAG服务运行正常" };
      } else {
        return { status: "error", message: `RAG服务异常: ${response.status}` };
      }
    } catch (error) {
      return { status: "error", message: `无法连接RAG服务: ${error}` };
    }
  }

  // 创建知识库
  async createKnowledgeBase(
    documents: Array<{
      title: string;
      file: string;
      content: string;
      category: string;
      language?: string;
      start_line?: number;
      end_line?: number;
    }>,
    vectorField: string = "content",
    projectName?: string
  ): Promise<{
    status: string;
    message?: string;
    index?: string;
    count?: number;
  }> {
    try {
      const ragBaseUrl = "http://nodeport.sensedeal.vip:32421";

      const requestData = {
        documents,
        vector_field: vectorField,
      };

      console.log(`创建知识库，文档数量: ${documents.length}`);
      if (projectName) {
        console.log(`项目名称: ${projectName}`);
      }

      const response = await fetch(`${ragBaseUrl}/documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
        timeout: 300000, // 5分钟超时
      });

      if (response.ok) {
        const result = await response.json();
        console.log(
          `知识库创建成功，索引: ${result.index}, 文档数量: ${result.count}`
        );
        return {
          status: "success",
          message: "知识库创建成功",
          index: result.index,
          count: result.count,
        };
      } else {
        const errorData = await response.json().catch(() => ({}));
        return {
          status: "error",
          message: `知识库创建失败: ${
            errorData.message || response.statusText
          }`,
        };
      }
    } catch (error) {
      console.error("创建知识库时出错:", error);
      return {
        status: "error",
        message: `创建知识库时出错: ${error}`,
      };
    }
  }

  // 向已存在的索引添加文档
  async addDocumentsToIndex(
    documents: Array<{
      title: string;
      file: string;
      content: string;
      category: string;
      language?: string;
      start_line?: number;
      end_line?: number;
    }>,
    indexName: string,
    vectorField: string = "content"
  ): Promise<{
    status: string;
    message?: string;
    count?: number;
  }> {
    try {
      const ragBaseUrl = "http://nodeport.sensedeal.vip:32421";

      const requestData = {
        documents,
        vector_field: vectorField,
        index: indexName,
      };

      console.log(`向索引 ${indexName} 添加 ${documents.length} 个文档`);

      const response = await fetch(`${ragBaseUrl}/documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
        timeout: 300000, // 5分钟超时
      });

      if (response.ok) {
        const result = await response.json();
        console.log(`成功添加 ${result.count} 个文档到索引`);
        return {
          status: "success",
          message: "文档添加成功",
          count: result.count,
        };
      } else {
        const errorData = await response.json().catch(() => ({}));
        return {
          status: "error",
          message: `添加文档失败: ${errorData.message || response.statusText}`,
        };
      }
    } catch (error) {
      console.error("添加文档时出错:", error);
      return {
        status: "error",
        message: `添加文档时出错: ${error}`,
      };
    }
  }

  // 触发知识库创建flow
  async createKnowledgeBaseFlow(taskId: number): Promise<{
    status: string;
    message?: string;
    task_id?: number;
    task_status?: string;
    vectorstore_index?: string;
  }> {
    try {
      console.log(`触发任务 ${taskId} 的知识库创建flow...`);

      const response = await fetch(
        `${this.baseUrl}/api/analysis/${taskId}/create-knowledge-base`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 30000, // 30秒超时
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log(`知识库创建flow启动成功:`, result);
        return {
          status: "success",
          message: result.message || "知识库创建任务已启动",
          task_id: result.task_id,
          task_status: result.task_status,
        };
      } else {
        const errorData = await response.json().catch(() => ({}));
        return {
          status: "error",
          message: `启动知识库创建失败: ${
            errorData.message || response.statusText
          }`,
        };
      }
    } catch (error) {
      console.error("触发知识库创建flow时出错:", error);
      return {
        status: "error",
        message: `触发知识库创建flow时出错: ${error}`,
      };
    }
  }

  // 触发分析数据模型flow
  async analyzeDataModelFlow(taskId: number): Promise<{
    status: string;
    message?: string;
    task_id?: number;
    task_status?: string;
    analysis_items_count?: number;
    total_files?: number;
    successful_files?: number;
    failed_files?: number;
    success_rate?: string;
    analysis_results?: Array<{
      file_id: number;
      file_path: string;
      status: string;
      analysis_items_count?: number;
      error?: string;
    }>;
  }> {
    try {
      console.log(`触发任务 ${taskId} 的分析数据模型flow...`);

      const response = await fetch(
        `${this.baseUrl}/api/analysis/${taskId}/analyze-data-model`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 30000, // 30秒超时
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log(`分析数据模型flow启动成功:`, result);
        return {
          status: "success",
          message: result.message || "分析数据模型任务已启动",
          task_id: result.task_id,
          task_status: result.task_status,
          analysis_items_count: result.analysis_items_count,
          total_files: result.total_files,
          successful_files: result.successful_files,
          failed_files: result.failed_files,
          success_rate: result.success_rate,
          analysis_results: result.analysis_results,
        };
      } else {
        const errorData = await response.json().catch(() => ({}));
        return {
          status: "error",
          message: `启动分析数据模型失败: ${
            errorData.message || response.statusText
          }`,
        };
      }
    } catch (error) {
      console.error("触发分析数据模型flow时出错:", error);
      return {
        status: "error",
        message: `触发分析数据模型flow时出错: ${error}`,
      };
    }
  }

  // 触发单文件分析数据模型flow
  async analyzeSingleFileDataModel(
    fileId: number,
    taskIndex: string
  ): Promise<{
    status: string;
    message?: string;
    file_id?: number;
    file_path?: string;
    analysis_items_count?: number;
  }> {
    try {
      console.log(`触发文件 ${fileId} 的单文件分析数据模型flow...`);

      const response = await fetch(
        `${
          this.baseUrl
        }/api/analysis/file/${fileId}/analyze-data-model?task_index=${encodeURIComponent(
          taskIndex
        )}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 30000, // 30秒超时
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log(`单文件分析数据模型flow启动成功:`, result);
        return {
          status: "success",
          message: result.message || "单文件分析数据模型任务已启动",
          file_id: result.file_id,
          file_path: result.file_path,
          analysis_items_count: result.analysis_items_count,
        };
      } else {
        const errorData = await response.json();
        console.error("单文件分析数据模型flow启动失败:", errorData);
        return {
          status: "error",
          message: errorData.message || `HTTP ${response.status}`,
        };
      }
    } catch (error) {
      console.error("触发单文件分析数据模型flow失败:", error);
      return {
        status: "error",
        message: `触发单文件分析数据模型flow失败: ${error}`,
      };
    }
  }
}

// 默认API服务实例
export const apiService = new ApiService();

// 便捷函数
export const api = {
  // 项目相关
  getProjects: (params?: Parameters<ApiService["getProjects"]>[0]) =>
    apiService.getProjects(params),
  getProjectDetail: (repoName: string) => apiService.getProjectDetail(repoName),
  getProjectOverview: (repoName: string) =>
    apiService.getProjectOverview(repoName),
  getProjectFiles: (repoName: string, path?: string) =>
    apiService.getProjectFiles(repoName, path),

  // 分析相关
  getProjectAnalysis: (repoName: string, version?: string) =>
    apiService.getProjectAnalysis(repoName, version),
  getAnalysisSummary: (repoName: string) =>
    apiService.getAnalysisSummary(repoName),
  getFileAnalysis: (repoName: string, filePath: string) =>
    apiService.getFileAnalysis(repoName, filePath),

  // 搜索
  searchInProject: (repoName: string, searchRequest: SearchRequest) =>
    apiService.searchInProject(repoName, searchRequest),

  // 统计
  getSystemStatistics: () => apiService.getSystemStatistics(),

  // 健康检查
  healthCheck: () => apiService.healthCheck(),

  // 新增的仓库和文件相关API
  getRepositoryByName: (
    name: string,
    exactMatch?: boolean,
    includeTasks?: boolean
  ) => apiService.getRepositoryByName(name, exactMatch, includeTasks),
  getFilesByTaskId: (taskId: number) => apiService.getFilesByTaskId(taskId),
  getAnalysisItemsByFileId: (fileAnalysisId: number) =>
    apiService.getAnalysisItemsByFileId(fileAnalysisId),

  // 上传相关
  uploadRepository: (files: FileList, repositoryName: string) =>
    apiService.uploadRepository(files, repositoryName),

  // 分析任务相关
  createAnalysisTask: (taskData: {
    repository_id: number;
    total_files?: number;
    successful_files?: number;
    failed_files?: number;
    code_lines?: number;
    module_count?: number;
    status?: string;
    start_time?: string;
    task_index?: string;
  }) => apiService.createAnalysisTask(taskData),
  getAnalysisTask: (taskId: number) => apiService.getAnalysisTask(taskId),
  updateAnalysisTask: (
    taskId: number,
    updateData: Parameters<ApiService["updateAnalysisTask"]>[1]
  ) => apiService.updateAnalysisTask(taskId, updateData),

  // 文件分析相关
  createFileAnalysis: (
    fileData: Parameters<ApiService["createFileAnalysis"]>[0]
  ) => apiService.createFileAnalysis(fileData),

  // 队列相关
  getQueueStatus: () => apiService.getQueueStatus(),

  // RAG 知识库相关
  createKnowledgeBase: (
    documents: any[],
    vectorField?: string,
    projectName?: string
  ) => apiService.createKnowledgeBase(documents, vectorField, projectName),
  addDocumentsToIndex: (
    documents: any[],
    indexName: string,
    vectorField?: string
  ) => apiService.addDocumentsToIndex(documents, indexName, vectorField),
  checkRAGHealth: () => apiService.checkRAGHealth(),

  // 知识库创建flow
  createKnowledgeBaseFlow: (taskId: number) =>
    apiService.createKnowledgeBaseFlow(taskId),

  // 分析数据模型flow
  analyzeDataModelFlow: (taskId: number) =>
    apiService.analyzeDataModelFlow(taskId),
};

export default api;
