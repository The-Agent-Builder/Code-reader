"""
WebUIFlow - 提供前端交互界面
Design: AsyncFlow
"""
from typing import Dict, Any
from pocketflow import AsyncFlow

from .analysis_flow import GitHubAnalysisFlow, QuickAnalysisFlow
from ..utils.result_storage import ResultStorage
from ..utils.search_engine import SearchEngine
from ..utils.logger import logger


class WebUIFlow(AsyncFlow):
    """
    提供前端交互界面
    
    嵌套节点：
    - /analyze: 触发主分析流程（即以上 Flow）
    - /results: 查看已有分析记录
    - /search: 提供全文搜索接口
    """
    
    def __init__(self):
        super().__init__()
        self.result_storage = ResultStorage()
        self.search_engine = SearchEngine(self.result_storage)
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        接收浏览器请求
        """
        request_type = shared.get('request_type', 'unknown')
        logger.info(f"WebUI Flow processing request: {request_type}")
        
        # 验证请求类型
        valid_types = ['analyze', 'results', 'search', 'statistics']
        if request_type not in valid_types:
            raise ValueError(f"Invalid request type: {request_type}")
        
        return shared
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用对应子 Flow 并等待结果
        """
        request_type = prep_res.get('request_type')
        
        if request_type == 'analyze':
            return await self._handle_analyze_request(prep_res)
        elif request_type == 'results':
            return await self._handle_results_request(prep_res)
        elif request_type == 'search':
            return await self._handle_search_request(prep_res)
        elif request_type == 'statistics':
            return await self._handle_statistics_request(prep_res)
        else:
            raise ValueError(f"Unsupported request type: {request_type}")
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], 
                        exec_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        渲染 HTML 页面并返回给客户端
        """
        # 将执行结果合并到共享数据中
        shared.update(exec_res)
        
        request_type = prep_res.get('request_type')
        logger.info(f"WebUI Flow completed processing: {request_type}")
        
        return shared
    
    async def _handle_analyze_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理分析请求"""
        repo_url = request_data.get('repo_url')
        use_vectorization = request_data.get('use_vectorization', True)
        batch_size = request_data.get('batch_size', 10)
        
        if not repo_url:
            raise ValueError("Repository URL is required for analysis")
        
        # 准备分析流程的共享数据
        analysis_shared = {
            'repo_url': repo_url
        }
        
        # 选择分析流程
        if use_vectorization:
            flow = GitHubAnalysisFlow(batch_size=batch_size)
        else:
            flow = QuickAnalysisFlow(batch_size=batch_size)
        
        try:
            # 执行分析流程
            await flow.run_async(analysis_shared)
            
            return {
                'status': 'success',
                'message': 'Analysis completed successfully',
                'result': analysis_shared
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Analysis failed: {str(e)}',
                'error': str(e)
            }
    
    async def _handle_results_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理结果查看请求"""
        analysis_id = request_data.get('analysis_id')
        page = request_data.get('page', 1)
        page_size = request_data.get('page_size', 20)
        
        try:
            if analysis_id:
                # 获取特定分析结果
                result = self.result_storage.get_analysis_by_id(analysis_id)
                if result:
                    return {
                        'status': 'success',
                        'analysis_result': result
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'Analysis {analysis_id} not found'
                    }
            else:
                # 获取分析列表
                analyses = self.result_storage.get_analysis_list(limit=page_size * 10)
                
                # 简单分页
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                page_analyses = analyses[start_idx:end_idx]
                
                return {
                    'status': 'success',
                    'analyses': page_analyses,
                    'total': len(analyses),
                    'page': page,
                    'page_size': page_size
                }
                
        except Exception as e:
            logger.error(f"Failed to get results: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to get results: {str(e)}'
            }
    
    async def _handle_search_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理搜索请求"""
        query = request_data.get('query', '')
        search_type = request_data.get('search_type', 'all')
        repo_name = request_data.get('repo_name')
        limit = request_data.get('limit', 20)
        
        try:
            if repo_name:
                results = self.search_engine.search_by_repo(repo_name, query, limit)
            else:
                results = self.search_engine.search(query, search_type, limit)
            
            # 转换搜索结果为字典格式
            search_results = []
            for result in results:
                search_results.append({
                    'analysis_id': result.analysis_id,
                    'repo_name': result.repo_name,
                    'file_path': result.file_path,
                    'element_type': result.element_type,
                    'element_name': result.element_name,
                    'description': result.description,
                    'source': result.source,
                    'language': result.language,
                    'code': result.code,
                    'score': result.score
                })
            
            return {
                'status': 'success',
                'results': search_results,
                'total': len(search_results),
                'query': query,
                'search_type': search_type
            }
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Search failed: {str(e)}'
            }
    
    async def _handle_statistics_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理统计信息请求"""
        try:
            stats = self.search_engine.get_statistics()
            
            return {
                'status': 'success',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to get statistics: {str(e)}'
            }


# 便捷函数
async def handle_webui_request(request_type: str, **kwargs) -> Dict[str, Any]:
    """
    处理WebUI请求的便捷函数
    
    Args:
        request_type: 请求类型 ('analyze', 'results', 'search', 'statistics')
        **kwargs: 请求参数
        
    Returns:
        处理结果字典
    """
    shared = {
        'request_type': request_type,
        **kwargs
    }
    
    flow = WebUIFlow()
    result = await flow.run_async(shared)
    
    return shared
