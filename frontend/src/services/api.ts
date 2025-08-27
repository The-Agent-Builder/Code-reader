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
};

export default api;
