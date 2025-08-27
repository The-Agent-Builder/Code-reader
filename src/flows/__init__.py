# PocketFlow flows for local folder analysis

# Import local folder analysis flows
from .file_analysis_flow import (
    LocalFolderAnalysisFlow,
    GitHubAnalysisFlow,
    QuickAnalysisFlow,
    analyze_repository,
    analyze_local_folder,
    create_analysis_flow
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
    "create_analysis_flow"
    # "WebUIFlow",
    # "handle_webui_request"
]
