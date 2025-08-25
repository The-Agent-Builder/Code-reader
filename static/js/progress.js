/**
 * 进度条功能 JavaScript
 * 处理分析进度的实时更新和显示
 */

let analysisId = null;
let progressInterval = null;
let startTime = null;

// 页面加载完成后初始化
document.addEventListener("DOMContentLoaded", function () {
  // 清理任何残留的轮询
  if (progressInterval) {
    clearInterval(progressInterval);
    progressInterval = null;
  }

  // 重置状态
  analysisId = null;
  startTime = null;
  window.pollErrorCount = 0;

  const analysisForm = document.getElementById("analysisForm");
  if (analysisForm) {
    analysisForm.addEventListener("submit", handleFormSubmit);
  }

  // 加载已分析的仓库列表
  loadAnalysisList();
});

// 页面卸载时清理
window.addEventListener("beforeunload", function () {
  if (progressInterval) {
    clearInterval(progressInterval);
  }
});

async function handleFormSubmit(e) {
  e.preventDefault();

  const repoUrl = document.getElementById("repoUrl").value;
  const useVectorization = document.getElementById("useVectorization").checked;
  const forceRefresh = document.getElementById("forceRefresh").checked;

  // 开始分析（批处理大小由后端配置决定）
  await startAnalysis(repoUrl, useVectorization, forceRefresh);
}

async function startAnalysis(repoUrl, useVectorization, forceRefresh = false) {
  try {
    console.log("startAnalysis called with:", repoUrl); // 调试信息

    // 禁用表单
    const analyzeBtn = document.getElementById("analyzeBtn");
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin me-2"></i>启动中...';

    // 发送分析请求（批处理大小由后端配置决定）
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        repo_url: repoUrl,
        use_vectorization: useVectorization,
        force_refresh: forceRefresh,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "分析请求失败");
    }

    const result = await response.json();
    analysisId = result.analysis_id;

    // 检查是否已完成分析
    if (result.status === "completed" || result.status === "success") {
      showNotification("该仓库已分析完成！", "success");
      // 刷新分析列表
      if (typeof loadAnalysisList === "function") {
        loadAnalysisList();
      }
      resetForm();
      return;
    }

    // 显示进度条
    console.log("Showing progress container"); // 调试信息
    document.getElementById("progressContainer").style.display = "block";
    document.getElementById("resultContainer").style.display = "none";

    // 重置错误计数器
    window.pollErrorCount = 0;

    // 开始轮询进度
    startTime = new Date();
    startProgressPolling();
  } catch (error) {
    console.error("启动分析失败:", error);
    alert("启动分析失败: " + error.message);
    resetForm();
  }
}

function startProgressPolling() {
  progressInterval = setInterval(async () => {
    try {
      // 检查是否有有效的分析ID
      if (!analysisId) {
        console.warn("No valid analysis ID, stopping polling");
        clearInterval(progressInterval);
        return;
      }

      const response = await fetch(`/api/analysis/${analysisId}/status`);
      if (!response.ok) {
        if (response.status === 404) {
          console.warn(`Analysis ${analysisId} not found, stopping polling`);
          clearInterval(progressInterval);
          return;
        }
        throw new Error(`获取状态失败: ${response.status}`);
      }

      const status = await response.json();
      updateProgress(status);

      if (
        status.status === "completed" ||
        status.status === "success" ||
        status.status === "failed" ||
        status.status === "error"
      ) {
        clearInterval(progressInterval);
        handleAnalysisComplete(status);
      }
    } catch (error) {
      console.error("获取进度失败:", error);
      // 如果连续失败多次，停止轮询
      if (!window.pollErrorCount) {
        window.pollErrorCount = 0;
      }
      window.pollErrorCount++;

      if (window.pollErrorCount >= 5) {
        console.error("Too many polling errors, stopping");
        clearInterval(progressInterval);
        showNotification("获取分析状态失败，请刷新页面重试", "error");
      }
    }
  }, 1000); // 每秒更新一次
}

function updateProgress(status) {
  console.log("updateProgress called with:", status); // 调试信息

  const progress = (status.progress || 0) * 100;
  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");

  // 更新进度条
  progressBar.style.width = progress + "%";
  progressText.textContent = Math.round(progress) + "%";

  // 文件进度和当前文件信息已移除，不再显示

  // 更新状态消息
  if (status.message) {
    document.getElementById("statusMessage").textContent = status.message;
  }

  // 时间显示已移除

  // 更新状态徽章
  const statusBadge = document.getElementById("statusBadge");
  if (status.status === "processing") {
    statusBadge.className = "badge bg-info status-badge";
    statusBadge.textContent = "处理中";
  } else if (status.status === "completed" || status.status === "success") {
    statusBadge.className = "badge bg-success status-badge";
    statusBadge.textContent = "已完成";
  } else if (status.status === "failed" || status.status === "error") {
    statusBadge.className = "badge bg-danger status-badge";
    statusBadge.textContent = "失败";
  } else if (status.status === "pending") {
    statusBadge.className = "badge bg-warning status-badge";
    statusBadge.textContent = "等待中";
  }
}

function handleAnalysisComplete(status) {
  if (status.status === "completed" || status.status === "success") {
    // 显示成功结果
    document.getElementById("resultContainer").style.display = "block";

    // 更新统计信息
    let statsText = "分析完成";
    if (status.total_files) {
      statsText = `${status.total_files} 个文件`;
      if (status.completed_files) {
        statsText = `${status.completed_files}/${status.total_files} 个文件`;
      }
    }

    // 尝试从不同的数据结构中获取统计信息
    if (status.result) {
      if (
        status.result.code_analysis &&
        Array.isArray(status.result.code_analysis)
      ) {
        const totalFiles = status.result.code_analysis.length;
        const totalItems = status.result.code_analysis.reduce(
          (sum, file) =>
            sum + (file.analysis_items ? file.analysis_items.length : 0),
          0
        );
        statsText = `${totalFiles} 个文件，${totalItems} 个分析项`;
      } else if (status.result.statistics) {
        const stats = status.result.statistics;
        statsText = `${stats.total_files || 0} 个文件，${
          stats.total_functions || 0
        } 个函数，${stats.total_classes || 0} 个类`;
      }
    }

    document.getElementById("analysisStats").textContent = statsText;

    // 设置查看结果链接
    document.getElementById("viewResultBtn").href = `/analysis/${analysisId}`;

    // 显示成功消息
    showNotification("分析完成！", "success");
  } else {
    // 显示错误
    showNotification("分析失败: " + status.message, "error");
  }

  resetForm();
}

function resetForm() {
  // 停止轮询
  if (progressInterval) {
    clearInterval(progressInterval);
    progressInterval = null;
  }

  // 重置状态
  analysisId = null;
  startTime = null;
  window.pollErrorCount = 0;

  // 重置按钮
  const analyzeBtn = document.getElementById("analyzeBtn");
  analyzeBtn.disabled = false;
  analyzeBtn.innerHTML = '<i class="fas fa-play me-2"></i>开始分析';

  // 隐藏进度容器
  document.getElementById("progressContainer").style.display = "none";
  document.getElementById("resultContainer").style.display = "none";

  // 重置状态消息
  document.getElementById("statusMessage").textContent = "准备中...";
}

function showNotification(message, type = "info") {
  // 创建通知元素
  const notification = document.createElement("div");
  notification.className = `alert alert-${
    type === "success" ? "success" : type === "error" ? "danger" : "info"
  } alert-dismissible fade show position-fixed`;
  notification.style.cssText =
    "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";

  notification.innerHTML = `
        <i class="fas fa-${
          type === "success"
            ? "check-circle"
            : type === "error"
            ? "exclamation-circle"
            : "info-circle"
        } me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  document.body.appendChild(notification);

  // 自动移除通知
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification);
    }
  }, 5000);
}

// 页面卸载时清理定时器
window.addEventListener("beforeunload", function () {
  if (progressInterval) {
    clearInterval(progressInterval);
  }
});

// 加载已分析的仓库列表
async function loadAnalysisList(page = 1) {
  try {
    const response = await fetch(`/api/analyses?page=${page}&page_size=10`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    displayAnalysisList(data);
    updatePagination(data);
  } catch (error) {
    console.error("加载分析列表失败:", error);
    document.getElementById("analysisListContainer").innerHTML = `
      <div class="alert alert-warning">
        <i class="fas fa-exclamation-triangle me-2"></i>
        加载分析列表失败: ${error.message}
      </div>
    `;
  }
}

// 显示分析列表
function displayAnalysisList(data) {
  const container = document.getElementById("analysisListContainer");
  const totalCount = document.getElementById("totalCount");

  totalCount.textContent = data.total;

  if (data.analyses.length === 0) {
    container.innerHTML = `
      <div class="text-center text-muted">
        <i class="fas fa-inbox me-2"></i>
        暂无分析记录
      </div>
    `;
    return;
  }

  const listHtml = data.analyses
    .map((analysis) => {
      const createdAt = new Date(analysis.created_at).toLocaleString("zh-CN");
      const repoName = analysis.repo_name || "未知仓库";
      const status = analysis.status || "unknown";
      const statusBadge = getStatusBadge(status);

      return `
      <div class="card mb-3 analysis-item" data-analysis-id="${
        analysis.analysis_id
      }">
        <div class="card-body">
          <div class="row align-items-center">
            <div class="col-lg-7 col-md-6">
              <h6 class="card-title mb-1">
                <i class="fab fa-github me-2"></i>
                ${repoName}
              </h6>
              <p class="card-text text-muted mb-1">
                <small>
                  <i class="fas fa-clock me-1"></i>
                  ${createdAt}
                </small>
              </p>
              <div class="d-flex align-items-center flex-wrap">
                ${statusBadge}
                <span class="text-muted ms-2">
                  <i class="fas fa-file-code me-1"></i>
                  ${analysis.statistics?.total_files || 0} 文件
                </span>
                <span class="text-muted ms-2">
                  <i class="fas fa-function me-1"></i>
                  ${analysis.statistics?.total_functions || 0} 函数
                </span>
                <span class="text-muted ms-2">
                  <i class="fas fa-cube me-1"></i>
                  ${analysis.statistics?.total_classes || 0} 类
                </span>
              </div>
            </div>
            <div class="col-lg-5 col-md-6 mt-2 mt-md-0">
              <div class="d-flex flex-column flex-md-row gap-1 justify-content-end">
                <button class="btn btn-outline-primary btn-sm" onclick="viewAnalysisDetail('${
                  analysis.analysis_id
                }')" title="查看详情">
                  <i class="fas fa-eye me-1"></i>
                  查看详情
                </button>
                <button class="btn btn-outline-warning btn-sm" onclick="reanalyzeRepository('${
                  analysis.analysis_id
                }', '${analysis.repo_url || ""}')" title="重新分析">
                  <i class="fas fa-redo me-1"></i>
                  重新分析
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="deleteAnalysis('${
                  analysis.analysis_id
                }', '${repoName}')" title="删除">
                  <i class="fas fa-trash me-1"></i>
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    })
    .join("");

  container.innerHTML = listHtml;
}

// 获取状态徽章
function getStatusBadge(status) {
  switch (status) {
    case "completed":
    case "success":
      return '<span class="badge bg-success">已完成</span>';
    case "processing":
      return '<span class="badge bg-primary">处理中</span>';
    case "failed":
    case "error":
      return '<span class="badge bg-danger">失败</span>';
    case "pending":
      return '<span class="badge bg-warning">等待中</span>';
    default:
      return '<span class="badge bg-secondary">未知</span>';
  }
}

// 更新分页控件
function updatePagination(data) {
  const pagination = document.getElementById("pagination");
  const totalPages = Math.ceil(data.total / data.page_size);
  const currentPage = data.page;

  if (totalPages <= 1) {
    pagination.innerHTML = "";
    return;
  }

  let paginationHtml = "";

  // 上一页
  if (currentPage > 1) {
    paginationHtml += `
      <li class="page-item">
        <a class="page-link" href="#" onclick="loadAnalysisList(${
          currentPage - 1
        })">
          <i class="fas fa-chevron-left"></i>
        </a>
      </li>
    `;
  }

  // 页码
  const startPage = Math.max(1, currentPage - 2);
  const endPage = Math.min(totalPages, currentPage + 2);

  for (let i = startPage; i <= endPage; i++) {
    const activeClass = i === currentPage ? "active" : "";
    paginationHtml += `
      <li class="page-item ${activeClass}">
        <a class="page-link" href="#" onclick="loadAnalysisList(${i})">${i}</a>
      </li>
    `;
  }

  // 下一页
  if (currentPage < totalPages) {
    paginationHtml += `
      <li class="page-item">
        <a class="page-link" href="#" onclick="loadAnalysisList(${
          currentPage + 1
        })">
          <i class="fas fa-chevron-right"></i>
        </a>
      </li>
    `;
  }

  pagination.innerHTML = paginationHtml;
}

// 查看分析详情
function viewAnalysisDetail(analysisId) {
  // 打开新窗口显示分析详情
  window.open(`/analysis/${analysisId}`, "_blank");
}

// 重新分析仓库
async function reanalyzeRepository(analysisId, repoUrl) {
  if (!repoUrl) {
    // 如果没有repo_url，从分析详情中获取
    try {
      const response = await fetch(`/api/analysis/${analysisId}`);
      if (response.ok) {
        const analysisData = await response.json();
        repoUrl = analysisData.repo_url;
      }
    } catch (error) {
      console.error("获取仓库URL失败:", error);
      showAlert("无法获取仓库信息，请稍后重试", "danger");
      return;
    }
  }

  if (!repoUrl) {
    showAlert("无法获取仓库URL，无法重新分析", "danger");
    return;
  }

  // 确认对话框
  if (
    !confirm(`确定要重新分析仓库 "${repoUrl}" 吗？\n\n这将覆盖现有的分析结果。`)
  ) {
    return;
  }

  try {
    // 显示加载状态
    showAlert("正在启动重新分析...", "info");

    // 调用重新分析API
    const response = await fetch(`/api/analysis/${analysisId}/reanalyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    // 跳转到进度页面
    window.location.href = `/progress.html?analysis_id=${result.analysis_id}`;
  } catch (error) {
    console.error("重新分析失败:", error);
    showAlert(`重新分析失败: ${error.message}`, "danger");
  }
}

// 删除分析结果
async function deleteAnalysis(analysisId, repoName) {
  // 确认对话框
  if (
    !confirm(
      `确定要删除仓库 "${repoName}" 的分析结果吗？\n\n此操作不可撤销，将删除所有相关数据。`
    )
  ) {
    return;
  }

  try {
    // 显示加载状态
    showAlert("正在删除分析结果...", "info");

    const response = await fetch(`/api/analysis/${analysisId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();

    if (result.success) {
      showAlert("分析结果已成功删除", "success");
      // 重新加载列表
      loadAnalysisList();
    } else {
      throw new Error(result.message || "删除失败");
    }
  } catch (error) {
    console.error("删除失败:", error);
    showAlert(`删除失败: ${error.message}`, "danger");
  }
}

// 显示提示信息
function showAlert(message, type = "info") {
  // 创建alert元素
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  alertDiv.style.cssText =
    "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  // 添加到页面
  document.body.appendChild(alertDiv);

  // 3秒后自动移除
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 3000);
}

// 导出函数供其他脚本使用
window.ProgressManager = {
  startAnalysis,
  updateProgress,
  resetForm,
  showNotification,
  loadAnalysisList,
  viewAnalysisDetail,
  reanalyzeRepository,
  deleteAnalysis,
  showAlert,
};

// 调试信息
console.log("Progress.js loaded with new functions:", {
  reanalyzeRepository: typeof reanalyzeRepository,
  deleteAnalysis: typeof deleteAnalysis,
  showAlert: typeof showAlert,
});
