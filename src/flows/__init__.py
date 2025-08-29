# PocketFlow flows for local folder analysis

# Import local folder analysis flows
from .file_analysis_flow import (
    LocalFolderAnalysisFlow,
    GitHubAnalysisFlow,
    QuickAnalysisFlow,
    analyze_repository,
    analyze_local_folder,
    create_analysis_flow,
)

# Import web knowledge base creation flow
from .web_flow import (
    WebKnowledgeBaseFlow,
    create_knowledge_base,
)

# Comment out GitHub-specific flows to avoid dependency issues
# from .analysis_flow import GitHubAnalysisFlow, QuickAnalysisFlow, analyze_repository
# from .webui_flow import WebUIFlow, handle_webui_request

__all__ = [
    "LocalFolderAnalysisFlow",
    "GitHubAnalysisFlow",
    "QuickAnalysisFlow",
    "analyze_repository",
    "analyze_local_folder",
    "create_analysis_flow",
    "WebKnowledgeBaseFlow",
    "create_knowledge_base",
    # "WebUIFlow",
    # "handle_webui_request"
]
