/**
 * Modern App Manager for AI Code Repository Navigator
 * Based on the new UI design with state management and page transitions
 */

class AppManager {
  constructor() {
    this.currentState = "upload";
    this.analysisConfig = null;
    this.totalAnalyzedProjects = 12847;
    this.selectedFiles = null;
    this.analysisSteps = [
      { icon: "search", label: "扫描代码文件", duration: 1000 },
      { icon: "brain", label: "分析数据模型", duration: 1500 },
      { icon: "network", label: "构建调用图谱", duration: 2000 },
      { icon: "file-text", label: "生成文档结构", duration: 1200 },
    ];
    this.currentStep = 0;
    this.progress = 0;
  }

  init() {
    this.setupEventListeners();
    this.updateProjectCounter();
    this.initializeUploadArea();
    console.log("AppManager initialized");
  }

  setupEventListeners() {
    // Upload area events
    const uploadDropzone = document.getElementById("uploadDropzone");
    const fileUpload = document.getElementById("fileUpload");
    const repoUrlInput = document.getElementById("repoUrlInput");
    const selectFolderBtn = document.getElementById("selectFolderBtn");
    const analyzeBtn = document.getElementById("analyzeBtn");

    // Navigation events
    const homeBtn = document.getElementById("homeBtn");
    const newAnalysisBtn = document.getElementById("newAnalysisBtn");
    const backToUploadBtn = document.getElementById("backToUploadBtn");
    const simulateCompleteBtn = document.getElementById("simulateCompleteBtn");

    // Email notification events
    const emailNotifyBtn = document.getElementById("emailNotifyBtn");

    if (uploadDropzone) {
      uploadDropzone.addEventListener("dragenter", this.handleDrag.bind(this));
      uploadDropzone.addEventListener("dragover", this.handleDrag.bind(this));
      uploadDropzone.addEventListener("dragleave", this.handleDrag.bind(this));
      uploadDropzone.addEventListener("drop", this.handleDrop.bind(this));
    }

    if (fileUpload) {
      fileUpload.addEventListener("change", this.handleFileSelect.bind(this));
    }

    if (repoUrlInput) {
      repoUrlInput.addEventListener(
        "input",
        this.handleRepoUrlInput.bind(this)
      );
    }

    if (selectFolderBtn) {
      selectFolderBtn.addEventListener("click", () => {
        fileUpload?.click();
      });
    }

    if (analyzeBtn) {
      analyzeBtn.addEventListener("click", this.handleStartAnalysis.bind(this));
    }

    if (homeBtn) {
      homeBtn.addEventListener("click", () => this.navigateToPage("upload"));
    }

    if (newAnalysisBtn) {
      newAnalysisBtn.addEventListener("click", () =>
        this.navigateToPage("upload")
      );
    }

    if (backToUploadBtn) {
      backToUploadBtn.addEventListener("click", () =>
        this.navigateToPage("upload")
      );
    }

    if (simulateCompleteBtn) {
      simulateCompleteBtn.addEventListener(
        "click",
        this.handleAnalysisComplete.bind(this)
      );
    }

    if (emailNotifyBtn) {
      emailNotifyBtn.addEventListener(
        "click",
        this.handleEmailNotification.bind(this)
      );
    }
  }

  initializeUploadArea() {
    const uploadContent = document.getElementById("uploadContent");
    if (uploadContent) {
      uploadContent.innerHTML = `
        <i data-lucide="upload" class="mx-auto h-16 w-16 text-gray-400"></i>
        <div>
          <h3 class="text-lg font-medium text-gray-700">
            拖拽您的代码库文件夹到此处
          </h3>
          <p class="text-sm text-gray-500">或点击选择本地文件夹</p>
        </div>
      `;
      // Re-initialize Lucide icons
      if (window.lucide) {
        window.lucide.createIcons();
      }
    }
  }

  updateProjectCounter() {
    // Simulate real-time project counter updates
    setInterval(() => {
      if (Math.random() < 0.15) {
        // 15% chance to update
        this.totalAnalyzedProjects += Math.floor(Math.random() * 3) + 1;
        this.updateProjectDisplay();
      }
    }, 8000 + Math.random() * 12000); // 8-20 second intervals
  }

  updateProjectDisplay() {
    const totalProjectsEl = document.getElementById("totalProjects");
    const totalProjectsFooterEl = document.getElementById(
      "totalProjectsFooter"
    );

    const formattedNumber = this.formatNumber(this.totalAnalyzedProjects);

    if (totalProjectsEl) {
      totalProjectsEl.textContent = formattedNumber + "+";
    }
    if (totalProjectsFooterEl) {
      totalProjectsFooterEl.textContent = formattedNumber;
    }
  }

  formatNumber(num) {
    if (num >= 10000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toLocaleString();
  }

  handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();

    const uploadDropzone = document.getElementById("uploadDropzone");
    if (!uploadDropzone) return;

    if (e.type === "dragenter" || e.type === "dragover") {
      uploadDropzone.classList.add("drag-active");
    } else if (e.type === "dragleave") {
      uploadDropzone.classList.remove("drag-active");
    }
  }

  handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();

    const uploadDropzone = document.getElementById("uploadDropzone");
    if (uploadDropzone) {
      uploadDropzone.classList.remove("drag-active");
    }

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      this.selectedFiles = e.dataTransfer.files;
      this.updateUploadDisplay();
    }
  }

  handleFileSelect(e) {
    if (e.target.files && e.target.files.length > 0) {
      this.selectedFiles = e.target.files;
      this.updateUploadDisplay();

      // 将文件信息保存到sessionStorage，准备跳转到配置页面
      const fileData = Array.from(e.target.files).map((file) => ({
        name: file.name,
        path: file.webkitRelativePath || file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
      }));

      sessionStorage.setItem("selectedFiles", JSON.stringify(fileData));
    }
  }

  handleRepoUrlInput(e) {
    const url = e.target.value.trim();
    const analyzeBtn = document.getElementById("analyzeBtn");

    if (analyzeBtn) {
      // Enable button if either URL is provided or files are selected
      analyzeBtn.disabled = !url && !this.selectedFiles;

      // Update button text based on input
      if (url) {
        analyzeBtn.textContent = "开始分析";
      } else if (this.selectedFiles) {
        analyzeBtn.textContent = "下一步";
      } else {
        analyzeBtn.textContent = "开始分析";
      }
    }
  }

  updateUploadDisplay() {
    const uploadContent = document.getElementById("uploadContent");
    const uploadDropzone = document.getElementById("uploadDropzone");
    const analyzeBtn = document.getElementById("analyzeBtn");

    if (uploadContent && this.selectedFiles) {
      uploadContent.innerHTML = `
        <i data-lucide="folder" class="mx-auto h-16 w-16 text-green-500"></i>
        <div>
          <h3 class="text-lg font-medium text-green-700">
            已选择 ${this.selectedFiles.length} 个文件
          </h3>
          <p class="text-sm text-green-600">
            点击开始分析按钮进行分析
          </p>
        </div>
      `;

      if (uploadDropzone) {
        uploadDropzone.classList.add("has-files");
      }

      if (analyzeBtn) {
        analyzeBtn.disabled = false;
      }

      // Re-initialize Lucide icons
      if (window.lucide) {
        window.lucide.createIcons();
      }
    }
  }

  async handleStartAnalysis() {
    const repoUrl = document.getElementById("repoUrlInput")?.value.trim();

    if (!repoUrl && !this.selectedFiles) {
      this.showAlert("请输入仓库URL或选择本地文件夹", "warning");
      return;
    }

    // 如果是GitHub URL，直接开始分析
    if (repoUrl) {
      // Create analysis configuration
      this.analysisConfig = {
        mode: "overall",
        selectedFiles: [],
        repoUrl: repoUrl,
      };

      // Update analysis page with configuration
      this.updateAnalysisConfig();

      // Navigate to analysis page
      this.navigateToPage("analyzing");

      // Start real analysis
      await this.startRealAnalysis(repoUrl);
    } else if (this.selectedFiles) {
      // 如果是本地文件，跳转到配置页面
      window.location.href = "/analysis-config";
    }
  }

  async startRealAnalysis(repoUrl) {
    try {
      // Call the actual backend API
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          repo_url: repoUrl,
          use_vectorization: false, // Can be made configurable
          force_refresh: false,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "分析请求失败");
      }

      const result = await response.json();

      if (result.status === "started") {
        // Start polling for progress
        this.pollAnalysisProgress(result.analysis_id);
      } else {
        throw new Error("分析启动失败");
      }
    } catch (error) {
      console.error("Analysis error:", error);
      this.showAlert(`分析启动失败: ${error.message}`, "error");
      this.navigateToPage("upload");
    }
  }

  async pollAnalysisProgress(analysisId) {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/analysis/${analysisId}/status`);
        if (!response.ok) {
          throw new Error("获取分析状态失败");
        }

        const status = await response.json();

        // Update progress display
        this.progress = status.progress || 0;
        this.updateProgressDisplay();

        if (status.status === "completed") {
          clearInterval(pollInterval);
          this.handleRealAnalysisComplete(status);
        } else if (status.status === "failed") {
          clearInterval(pollInterval);
          this.showAlert(`分析失败: ${status.error}`, "error");
          this.navigateToPage("upload");
        }
      } catch (error) {
        console.error("Polling error:", error);
        clearInterval(pollInterval);
        this.showAlert("获取分析状态失败", "error");
      }
    }, 2000); // Poll every 2 seconds
  }

  handleRealAnalysisComplete(result) {
    this.totalAnalyzedProjects += 1;
    this.updateProjectDisplay();

    // Show completion message with result link
    this.showAlert("分析完成！正在跳转到结果页面...", "success");

    // Navigate to results page
    if (result.result_filepath) {
      window.location.href = `/results?file=${encodeURIComponent(
        result.result_filepath
      )}`;
    } else {
      // Fallback to upload page
      setTimeout(() => {
        this.navigateToPage("upload");
        this.resetUploadState();
      }, 2000);
    }
  }

  updateAnalysisConfig() {
    const analysisModeEl = document.getElementById("analysisMode");
    const analysisModeDetailEl = document.getElementById("analysisModeDetail");
    const fileCountEl = document.getElementById("fileCount");

    if (analysisModeEl) {
      analysisModeEl.textContent = "代码整体分析";
    }
    if (analysisModeDetailEl) {
      analysisModeDetailEl.textContent = "整体架构";
    }
    if (fileCountEl && this.analysisConfig) {
      fileCountEl.textContent = `${this.analysisConfig.selectedFiles.length} 个`;
    }

    // Update queue status with random values
    const queuePosition = Math.floor(Math.random() * 8) + 3;
    const estimatedTime = Math.floor(Math.random() * 25) + 15;
    const totalInQueue = Math.floor(Math.random() * 20) + 15;

    const queuePositionEl = document.getElementById("queuePosition");
    const estimatedTimeEl = document.getElementById("estimatedTime");
    const totalInQueueEl = document.getElementById("totalInQueue");

    if (queuePositionEl) queuePositionEl.textContent = `#${queuePosition}`;
    if (estimatedTimeEl) estimatedTimeEl.textContent = `${estimatedTime}分`;
    if (totalInQueueEl) totalInQueueEl.textContent = totalInQueue.toString();
  }

  startAnalysisProcess() {
    this.currentStep = 0;
    this.progress = 0;
    this.updateProgressDisplay();
    this.runAnalysisStep(0);
  }

  runAnalysisStep(stepIndex) {
    if (stepIndex >= this.analysisSteps.length) {
      this.progress = 100;
      this.updateProgressDisplay();
      setTimeout(() => this.handleAnalysisComplete(), 500);
      return;
    }

    this.currentStep = stepIndex;
    const step = this.analysisSteps[stepIndex];
    const stepStart = this.progress;
    const stepEnd = this.progress + (step.duration / 5700) * 100; // Total 5.7s

    const startTime = Date.now();
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const stepProgressPercent = Math.min(elapsed / step.duration, 1);
      this.progress = stepStart + (stepEnd - stepStart) * stepProgressPercent;

      this.updateProgressDisplay();

      if (stepProgressPercent < 1) {
        requestAnimationFrame(animate);
      } else {
        setTimeout(() => this.runAnalysisStep(stepIndex + 1), 200);
      }
    };

    requestAnimationFrame(animate);
  }

  updateProgressDisplay() {
    const progressBar = document.getElementById("progressBar");
    const analysisStepsEl = document.getElementById("analysisSteps");

    if (progressBar) {
      progressBar.style.width = `${this.progress}%`;
    }

    if (analysisStepsEl) {
      analysisStepsEl.innerHTML = this.analysisSteps
        .map((step, index) => {
          const isActive = index === this.currentStep;
          const isCompleted = index < this.currentStep;
          const statusClass = isActive
            ? "active"
            : isCompleted
            ? "completed"
            : "pending";

          return `
          <div class="analysis-step ${statusClass}">
            <i data-lucide="${step.icon}" class="icon h-5 w-5"></i>
            <span class="flex-1 text-left">${step.label}</span>
            ${isCompleted ? '<span class="text-green-600">✓</span>' : ""}
          </div>
        `;
        })
        .join("");

      // Re-initialize Lucide icons
      if (window.lucide) {
        window.lucide.createIcons();
      }
    }
  }

  handleEmailNotification() {
    // Simulate email notification setup
    this.showAlert("邮箱通知已设置，分析完成后将通知您", "success");

    // Simulate background mode after 3 seconds
    setTimeout(() => {
      this.navigateToPage("background");
    }, 3000);
  }

  handleAnalysisComplete() {
    // Simulate analysis completion
    this.totalAnalyzedProjects += 1;
    this.updateProjectDisplay();

    // In a real app, this would navigate to the results page
    this.showAlert("分析完成！正在跳转到结果页面...", "success");

    // For demo purposes, navigate back to upload after 2 seconds
    setTimeout(() => {
      this.navigateToPage("upload");
      this.resetUploadState();
    }, 2000);
  }

  navigateToPage(page) {
    // Hide all pages
    const pages = ["uploadPage", "analysisPage", "backgroundPage"];
    pages.forEach((pageId) => {
      const pageEl = document.getElementById(pageId);
      if (pageEl) {
        pageEl.style.display = "none";
      }
    });

    // Show target page
    const targetPageEl = document.getElementById(page + "Page");
    if (targetPageEl) {
      targetPageEl.style.display = "flex";
    }

    // Update navigation state
    this.currentState = page;
    this.updateNavigation();
  }

  updateNavigation() {
    const pageTitle = document.getElementById("pageTitle");
    const pageSubtitle = document.getElementById("pageSubtitle");
    const statusBadge = document.getElementById("statusBadge");
    const homeBtn = document.getElementById("homeBtn");
    const newAnalysisBtn = document.getElementById("newAnalysisBtn");

    // Update page title
    const titles = {
      upload: "AI 代码库领航员",
      analyzing: "代码分析中",
      background: "后台运行",
    };

    if (pageTitle) {
      pageTitle.textContent = titles[this.currentState] || "AI 代码库领航员";
    }

    // Show/hide subtitle
    if (pageSubtitle) {
      pageSubtitle.style.display =
        this.currentState === "analyzing" ? "block" : "none";
    }

    // Show/hide status badge
    if (statusBadge) {
      statusBadge.style.display =
        this.currentState === "analyzing" ? "flex" : "none";
    }

    // Show/hide navigation buttons
    if (homeBtn) {
      homeBtn.style.display = this.currentState !== "upload" ? "block" : "none";
    }

    if (newAnalysisBtn) {
      newAnalysisBtn.style.display =
        this.currentState !== "upload" && this.currentState !== "analyzing"
          ? "block"
          : "none";
    }
  }

  resetUploadState() {
    this.selectedFiles = null;
    this.analysisConfig = null;

    const repoUrlInput = document.getElementById("repoUrlInput");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const uploadDropzone = document.getElementById("uploadDropzone");

    if (repoUrlInput) {
      repoUrlInput.value = "";
    }

    if (analyzeBtn) {
      analyzeBtn.disabled = true;
    }

    if (uploadDropzone) {
      uploadDropzone.classList.remove("has-files", "drag-active");
    }

    this.initializeUploadArea();
  }

  showAlert(message, type = "info") {
    // Create alert element
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} fixed top-4 right-4 z-50 min-w-80 p-4 rounded-lg shadow-lg`;
    alertDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      min-width: 300px;
      padding: 1rem;
      border-radius: 0.5rem;
      box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
      background-color: ${
        type === "success"
          ? "#f0fdf4"
          : type === "warning"
          ? "#fefce8"
          : "#eff6ff"
      };
      border: 1px solid ${
        type === "success"
          ? "#bbf7d0"
          : type === "warning"
          ? "#fde047"
          : "#bfdbfe"
      };
      color: ${
        type === "success"
          ? "#15803d"
          : type === "warning"
          ? "#a16207"
          : "#1d4ed8"
      };
    `;
    alertDiv.textContent = message;

    // Add to page
    document.body.appendChild(alertDiv);

    // Auto remove after 3 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.remove();
      }
    }, 3000);
  }
}

// Initialize global AppManager
window.AppManager = new AppManager();
