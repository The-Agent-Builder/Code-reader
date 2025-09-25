/**
 * API服务类 - 用于与后端API通信
 */

// 在 Docker 容器中，通过 Nginx 反向代理访问后端 API
// 使用相对路径，避免跨域问题
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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

// 项目列表相关类型定义
export interface RepositoryListItem {
    id: number;
    user_id: number;
    name: string;
    full_name: string;
    local_path: string;
    status: number;
    created_at: string;
    updated_at: string;
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
    total_tasks?: number;
}

export interface PaginationInfo {
    current_page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
}

export interface RepositoryListResponse {
    status: "success" | "error";
    message: string;
    data: {
        repositories: RepositoryListItem[];
        pagination: PaginationInfo;
        filters: {
            user_id?: number;
            status?: number;
        };
        sorting: {
            order_by: string;
            order_direction: string;
        };
    };
    error?: string;
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

    // 密码验证
    async verifyPassword(password: string): Promise<{
        success: boolean;
        message?: string;
    }> {
        try {
            const response = await fetch(
                `${this.baseUrl}/api/auth/verify-password`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ password }),
                }
            );

            if (response.ok) {
                const result = await response.json();
                return result;
            } else {
                return {
                    success: false,
                    message: "密码验证失败",
                };
            }
        } catch (error) {
            console.error("密码验证请求失败:", error);
            return {
                success: false,
                message: "网络错误，请重试",
            };
        }
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
    async getProjectOverview(
        repoName: string
    ): Promise<ProjectOverviewResponse> {
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

    // 获取项目列表（新增）
    async getRepositoriesList(params?: {
        user_id?: number;
        status?: number;
        order_by?: string;
        order_direction?: string;
        page?: number;
        page_size?: number;
    }): Promise<RepositoryListResponse> {
        const searchParams = new URLSearchParams();

        if (params?.user_id !== undefined) {
            searchParams.append("user_id", params.user_id.toString());
        }
        if (params?.status !== undefined) {
            searchParams.append("status", params.status.toString());
        }
        if (params?.order_by) {
            searchParams.append("order_by", params.order_by);
        }
        if (params?.order_direction) {
            searchParams.append("order_direction", params.order_direction);
        }
        if (params?.page !== undefined) {
            searchParams.append("page", params.page.toString());
        }
        if (params?.page_size !== undefined) {
            searchParams.append("page_size", params.page_size.toString());
        }

        const url = `/api/repository/repositories-list${
            searchParams.toString() ? `?${searchParams.toString()}` : ""
        }`;
        return this.request(url);
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

    // 根据仓库full_name获取仓库信息（新增）
    async getRepositoryByFullName(fullName: string): Promise<{
        status: string;
        message: string;
        search_field: string;
        search_value: string;
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
    }> {
        const params = new URLSearchParams({
            full_name: fullName,
        });

        return this.request(`/api/repository/repositories?${params}`);
    }

    // 根据仓库ID获取分析任务列表（新增）
    async getAnalysisTasksByRepositoryId(repositoryId: number): Promise<{
        status: string;
        message: string;
        repository_id: number;
        total_tasks: number;
        tasks: Array<{
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
    }> {
        return this.request(`/api/repository/analysis-tasks/${repositoryId}`);
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

    // 获取文件详情内容
    async getFileAnalysisDetail(
        fileId: number,
        taskId: number
    ): Promise<{
        status: string;
        message: string;
        file_analysis?: {
            id: number;
            file_id: number;
            task_id: number;
            code_content: string;
            language: string;
            code_lines: number;
            file_path: string;
            analysis_timestamp: string;
            // 其他可能的字段
        };
    }> {
        const params = new URLSearchParams({
            task_id: taskId.toString(),
        });

        console.log(
            `Making request to: /api/repository/file-analysis/${fileId}?${params}`
        );
        const response = await this.request(
            `/api/repository/file-analysis/${fileId}?${params}`
        );
        console.log(
            `File analysis detail API response for file_id ${fileId}, task_id ${taskId}:`,
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
        auto_compress_upload?: {
            status: string;
            message: string;
            upload_data?: any;
        };
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
        const url = `${this.baseUrl}/api/repository/analysis-tasks/${taskId}`;

        console.log(`🔄 发送更新任务请求到: ${url}`);
        console.log(`📝 更新数据:`, updateData);
        console.log(`📋 任务ID: ${taskId}`);

        try {
            const response = await fetch(url, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(updateData),
            });

            console.log(
                `📡 响应状态: ${response.status} ${response.statusText}`
            );

            if (!response.ok) {
                // 尝试获取错误详情
                let errorDetails;
                try {
                    errorDetails = await response.json();
                    console.error(`❌ API错误响应:`, errorDetails);
                } catch (e) {
                    errorDetails = { message: response.statusText };
                    console.error(`❌ 无法解析错误响应:`, e);
                }

                throw new Error(
                    `HTTP ${response.status}: ${
                        errorDetails.message || response.statusText
                    }`
                );
            }

            const result = await response.json();
            console.log(`✅ 更新任务成功:`, result);
            return result;
        } catch (error) {
            console.error(`❌ 更新任务失败:`, error);
            console.error(`🔍 请求详情: URL=${url}, 数据=`, updateData);
            throw error;
        }
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
                return {
                    status: "error",
                    message: `RAG服务异常: ${response.status}`,
                };
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
                    message: `添加文档失败: ${
                        errorData.message || response.statusText
                    }`,
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
                    timeout: 300000, // 30秒超时
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

    // 根据任务ID获取README文档
    async getTaskReadmeByTaskId(taskId: number): Promise<{
        status: string;
        message?: string;
        task_id?: number;
        readme?: {
            id: number;
            task_id: number;
            content: string;
            created_at: string;
            updated_at: string;
        };
    }> {
        try {
            console.log(`获取任务 ${taskId} 的README文档...`);

            const response = await fetch(
                `${this.baseUrl}/api/repository/task-readmes/by-task/${taskId}`,
                {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    timeout: 300000, // 30秒超时
                }
            );

            if (response.ok) {
                const result = await response.json();
                console.log(`README文档获取成功:`, result);
                return result;
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error("README文档获取失败:", errorData);
                return {
                    status: "error",
                    message: errorData.message || `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            console.error("获取README文档时出错:", error);
            return {
                status: "error",
                message: `获取README文档时出错: ${error}`,
            };
        }
    }

    // 生成文档结构 - 调用外部README API
    async generateDocumentStructure(localPath: string): Promise<{
        status: string;
        message?: string;
        task_id?: string;
    }> {
        try {
            // 从环境变量获取 README API Base URL（优先 VITE_README_API_BASE_URL，其次 README_API_BASE_URL），不再使用相对路径默认值，避免误指向前端 3000 端口
            const readmeApiBaseUrl =
                (import.meta.env.VITE_README_API_BASE_URL as string) ||
                ((import.meta.env as any).README_API_BASE_URL as string) ||
                "";

            if (!readmeApiBaseUrl) {
                console.error("README API Base URL 未配置，请在根目录 .env 设置 README_API_BASE_URL 或 frontend/.env 设置 VITE_README_API_BASE_URL");
                return {
                    status: "error",
                    message: "README API Base URL 未配置",
                };
            }

            // 修改localPath为 env中deepwiki_uoload_filepath/$localPath最后一级目录名$
            const deepwikiUploadFilepath = import.meta.env.VITE_DEEPWIKI_UPLOAD_FILEPATH || "/app/data/uploads";
            const lastDirName = localPath.split('/').filter(Boolean).pop() || "";
            const modifiedLocalPath = deepwikiUploadFilepath ? `${deepwikiUploadFilepath}/${lastDirName}` : localPath;
            console.log(
                `调用外部README API生成文档结构，原始路径: ${localPath}, 修改后路径: ${modifiedLocalPath}`
            );
            console.log(`README API Base URL: ${readmeApiBaseUrl}`);

            const requestData = {
                local_path: modifiedLocalPath,
                language: "zh",
                provider: "openai",
                model: "kimi-k2",
                export_format: "markdown",
                analysis_depth: "detailed",
                include_code_examples: true,
                generate_architecture_diagram: true,
            };
            

            const response = await fetch(
                `${readmeApiBaseUrl}/api/analyze/local`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(requestData),
                    timeout: 300000, // 5分钟超时
                }
            );

            if (response.ok) {
                const result = await response.json();
                console.log(`文档结构生成任务创建成功:`, result);
                return {
                    status: "success",
                    task_id: result.task_id,
                    message: "文档结构生成任务已创建",
                };
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error("文档结构生成任务创建失败:", errorData);
                return {
                    status: "error",
                    message: errorData.message || `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            console.error("调用外部README API时出错:", error);
            return {
                status: "error",
                message: `调用外部README API时出错: ${error}`,
            };
        }
    }

    // 检查文档生成状态
    async checkDocumentGenerationStatus(readmeApiTaskId: string): Promise<{
        status: string;
        task_id?: string;
        progress?: number;
        current_stage?: string;
        message?: string;
        error?: string;
        result?: {
            markdown?: string;
        };
    }> {
        try {
            // 从环境变量获取 README API Base URL（优先 VITE_README_API_BASE_URL，其次 README_API_BASE_URL），不再使用相对路径默认值，避免误指向前端 3000 端口
            const readmeApiBaseUrl =
                (import.meta.env.VITE_README_API_BASE_URL as string) ||
                ((import.meta.env as any).README_API_BASE_URL as string) ||
                "";

            if (!readmeApiBaseUrl) {
                console.error("README API Base URL 未配置，请在根目录 .env 设置 README_API_BASE_URL 或 frontend/.env 设置 VITE_README_API_BASE_URL");
                return {
                    status: "error",
                    message: "README API Base URL 未配置",
                };
            }
                

            console.log(`检查文档生成状态，任务ID: ${readmeApiTaskId}`);

            const response = await fetch(
                `${readmeApiBaseUrl}/api/analyze/local/${readmeApiTaskId}/status`,
                {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    timeout: 30000, // 30秒超时
                }
            );

            if (response.ok) {
                const result = await response.json();
                console.log(`文档生成状态检查成功:`, result);
                return result;
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error("文档生成状态检查失败:", errorData);
                return {
                    status: "error",
                    message: errorData.message || `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            console.error("检查文档生成状态时出错:", error);
            return {
                status: "error",
                message: `检查文档生成状态时出错: ${error}`,
            };
        }
    }

    // 创建任务README
    async createTaskReadme(
        taskId: number,
        content: string
    ): Promise<{
        status: string;
        message?: string;
        readme?: {
            id: number;
            task_id: number;
            content: string;
            created_at: string;
            updated_at: string;
        };
    }> {
        try {
            console.log(`创建任务 ${taskId} 的README文档...`);

            const requestData = {
                task_id: taskId,
                content: content,
            };

            const response = await fetch(
                `${this.baseUrl}/api/repository/task-readmes`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(requestData),
                    timeout: 30000, // 30秒超时
                }
            );

            if (response.ok) {
                const result = await response.json();
                console.log(`README文档创建成功:`, result);
                return result;
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error("README文档创建失败:", errorData);
                return {
                    status: "error",
                    message: errorData.message || `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            console.error("创建README文档时出错:", error);
            return {
                status: "error",
                message: `创建README文档时出错: ${error}`,
            };
        }
    }

    // 获取仓库信息
    async getRepositoryById(repositoryId: number): Promise<{
        status: string;
        message?: string;
        repository?: {
            id: number;
            name: string;
            full_name: string;
            local_path: string;
            absolute_local_path?: string;
            status: number;
            created_at: string;
            updated_at: string;
        };
    }> {
        try {
            console.log(`获取仓库 ${repositoryId} 的信息...`);

            const response = await fetch(
                `${this.baseUrl}/api/repository/repositories/${repositoryId}`,
                {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    timeout: 30000, // 30秒超时
                }
            );

            if (response.ok) {
                const result = await response.json();
                console.log(`仓库信息获取成功:`, result);
                return result;
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error("仓库信息获取失败:", errorData);
                return {
                    status: "error",
                    message: errorData.message || `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            console.error("获取仓库信息时出错:", error);
            return {
                status: "error",
                message: `获取仓库信息时出错: ${error}`,
            };
        }
    }

    // 压缩并上传md5文件夹到README API
    async compressAndUploadFolder(md5FolderName: string): Promise<{
        status: string;
        message: string;
        md5_folder_name?: string;
        upload_result?: any;
        error?: string;
    }> {
        try {
            console.log(`开始压缩并上传文件夹: ${md5FolderName}`);

            const response = await fetch(
                `${this.baseUrl}/api/repository/upload/compress-and-upload/${md5FolderName}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                }
            );

            if (response.ok) {
                const result = await response.json();
                console.log(`压缩并上传成功:`, result);
                return result;
            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error("压缩并上传失败:", errorData);
                return {
                    status: "error",
                    message: errorData.message || `HTTP ${response.status}`,
                };
            }
        } catch (error) {
            console.error("压缩并上传时出错:", error);
            return {
                status: "error",
                message: `压缩并上传时出错: ${error}`,
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
    getProjectDetail: (repoName: string) =>
        apiService.getProjectDetail(repoName),
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

    // 认证相关
    verifyPassword: (password: string) => apiService.verifyPassword(password),

    // 新增的仓库和文件相关API
    getRepositoriesList: (
        params?: Parameters<ApiService["getRepositoriesList"]>[0]
    ) => apiService.getRepositoriesList(params),
    getRepositoryByName: (
        name: string,
        exactMatch?: boolean,
        includeTasks?: boolean
    ) => apiService.getRepositoryByName(name, exactMatch, includeTasks),
    getRepositoryByFullName: (fullName: string) =>
        apiService.getRepositoryByFullName(fullName),
    getAnalysisTasksByRepositoryId: (repositoryId: number) =>
        apiService.getAnalysisTasksByRepositoryId(repositoryId),
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
    getFileAnalysisDetail: (fileId: number, taskId: number) =>
        apiService.getFileAnalysisDetail(fileId, taskId),

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

    // 获取任务README文档
    getTaskReadmeByTaskId: (taskId: number) =>
        apiService.getTaskReadmeByTaskId(taskId),

    // 生成文档结构相关
    generateDocumentStructure: (localPath: string) =>
        apiService.generateDocumentStructure(localPath),
    checkDocumentGenerationStatus: (readmeApiTaskId: string) =>
        apiService.checkDocumentGenerationStatus(readmeApiTaskId),
    createTaskReadme: (taskId: number, content: string) =>
        apiService.createTaskReadme(taskId, content),

    // 仓库信息相关
    getRepositoryById: (repositoryId: number) =>
        apiService.getRepositoryById(repositoryId),

    // 压缩并上传文件夹
    compressAndUploadFolder: (md5FolderName: string) =>
        apiService.compressAndUploadFolder(md5FolderName),
};

export default api;
