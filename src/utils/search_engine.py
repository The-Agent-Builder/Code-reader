"""
搜索引擎模块
提供关键词全文检索接口，支持按类名/函数名查询
"""
import re
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from .logger import logger
from .error_handler import SearchEngineError
from .result_storage import ResultStorage


@dataclass
class SearchResult:
    """搜索结果数据类"""
    analysis_id: str
    repo_name: str
    file_path: str
    element_type: str  # 'function' or 'class'
    element_name: str
    description: str
    source: str
    language: str
    code: str
    score: float = 0.0


class SearchEngine:
    """代码分析结果搜索引擎"""
    
    def __init__(self, result_storage: Optional[ResultStorage] = None):
        self.result_storage = result_storage or ResultStorage()
    
    def search(self, query: str, search_type: str = "all", limit: int = 20) -> List[SearchResult]:
        """
        搜索代码元素
        
        Args:
            query: 搜索查询
            search_type: 搜索类型 ('all', 'function', 'class', 'name', 'description')
            limit: 结果限制数量
            
        Returns:
            搜索结果列表
        """
        try:
            # 获取所有分析结果
            analyses = self.result_storage.get_analysis_list()
            results = []
            
            for analysis_meta in analyses:
                analysis_id = analysis_meta.get('analysis_id')
                analysis_data = self.result_storage.get_analysis_by_id(analysis_id)
                
                if not analysis_data:
                    continue
                
                # 搜索当前分析结果
                analysis_results = self._search_in_analysis(
                    analysis_data, query, search_type, analysis_id
                )
                results.extend(analysis_results)
            
            # 按相关性排序
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            raise SearchEngineError(f"Search failed: {str(e)}")
    
    def _search_in_analysis(self, analysis_data: Dict[str, Any], query: str, 
                          search_type: str, analysis_id: str) -> List[SearchResult]:
        """在单个分析结果中搜索"""
        results = []
        repo_info = analysis_data.get('repo_info', {})
        repo_name = repo_info.get('full_name', 'Unknown')
        code_analysis = analysis_data.get('code_analysis', [])
        
        for file_analysis in code_analysis:
            file_path = file_analysis.get('file_path', '')
            
            # 搜索函数
            if search_type in ['all', 'function']:
                for func in file_analysis.get('functions', []):
                    score = self._calculate_relevance_score(func, query, 'function')
                    if score > 0:
                        result = SearchResult(
                            analysis_id=analysis_id,
                            repo_name=repo_name,
                            file_path=file_path,
                            element_type='function',
                            element_name=func.get('title', ''),
                            description=func.get('description', ''),
                            source=func.get('source', ''),
                            language=func.get('language', ''),
                            code=func.get('code', ''),
                            score=score
                        )
                        results.append(result)
            
            # 搜索类
            if search_type in ['all', 'class']:
                for cls in file_analysis.get('classes', []):
                    score = self._calculate_relevance_score(cls, query, 'class')
                    if score > 0:
                        result = SearchResult(
                            analysis_id=analysis_id,
                            repo_name=repo_name,
                            file_path=file_path,
                            element_type='class',
                            element_name=cls.get('title', ''),
                            description=cls.get('description', ''),
                            source=cls.get('source', ''),
                            language=cls.get('language', ''),
                            code=cls.get('code', ''),
                            score=score
                        )
                        results.append(result)
        
        return results
    
    def _calculate_relevance_score(self, element: Dict[str, Any], query: str, element_type: str) -> float:
        """计算相关性得分"""
        score = 0.0
        query_lower = query.lower()
        
        # 名称匹配（权重最高）
        title = element.get('title', '').lower()
        if query_lower == title:
            score += 10.0  # 完全匹配
        elif query_lower in title:
            score += 5.0   # 部分匹配
        elif self._fuzzy_match(query_lower, title):
            score += 2.0   # 模糊匹配
        
        # 描述匹配
        description = element.get('description', '').lower()
        if query_lower in description:
            score += 3.0
        
        # 代码内容匹配
        code = element.get('code', '').lower()
        if query_lower in code:
            score += 1.0
        
        # 文件路径匹配
        source = element.get('source', '').lower()
        if query_lower in source:
            score += 0.5
        
        # 语言匹配
        language = element.get('language', '').lower()
        if query_lower == language:
            score += 0.5
        
        return score
    
    def _fuzzy_match(self, query: str, text: str, threshold: float = 0.6) -> bool:
        """模糊匹配"""
        # 简单的编辑距离匹配
        if len(query) == 0 or len(text) == 0:
            return False
        
        # 计算相似度
        similarity = self._calculate_similarity(query, text)
        return similarity >= threshold
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度"""
        # 使用简化的Jaccard相似度
        set1 = set(s1.lower())
        set2 = set(s2.lower())
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def search_by_repo(self, repo_name: str, query: str = "", limit: int = 20) -> List[SearchResult]:
        """按仓库搜索"""
        try:
            analyses = self.result_storage.get_analysis_list()
            results = []
            
            for analysis_meta in analyses:
                if repo_name.lower() not in analysis_meta.get('repo_name', '').lower():
                    continue
                
                analysis_id = analysis_meta.get('analysis_id')
                analysis_data = self.result_storage.get_analysis_by_id(analysis_id)
                
                if not analysis_data:
                    continue
                
                if query:
                    # 有查询条件
                    analysis_results = self._search_in_analysis(
                        analysis_data, query, "all", analysis_id
                    )
                else:
                    # 无查询条件，返回所有元素
                    analysis_results = self._get_all_elements(analysis_data, analysis_id)
                
                results.extend(analysis_results)
            
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:limit]
            
        except Exception as e:
            raise SearchEngineError(f"Repository search failed: {str(e)}")
    
    def _get_all_elements(self, analysis_data: Dict[str, Any], analysis_id: str) -> List[SearchResult]:
        """获取分析结果中的所有元素"""
        results = []
        repo_info = analysis_data.get('repo_info', {})
        repo_name = repo_info.get('full_name', 'Unknown')
        code_analysis = analysis_data.get('code_analysis', [])
        
        for file_analysis in code_analysis:
            file_path = file_analysis.get('file_path', '')
            
            # 添加所有函数
            for func in file_analysis.get('functions', []):
                result = SearchResult(
                    analysis_id=analysis_id,
                    repo_name=repo_name,
                    file_path=file_path,
                    element_type='function',
                    element_name=func.get('title', ''),
                    description=func.get('description', ''),
                    source=func.get('source', ''),
                    language=func.get('language', ''),
                    code=func.get('code', ''),
                    score=1.0
                )
                results.append(result)
            
            # 添加所有类
            for cls in file_analysis.get('classes', []):
                result = SearchResult(
                    analysis_id=analysis_id,
                    repo_name=repo_name,
                    file_path=file_path,
                    element_type='class',
                    element_name=cls.get('title', ''),
                    description=cls.get('description', ''),
                    source=cls.get('source', ''),
                    language=cls.get('language', ''),
                    code=cls.get('code', ''),
                    score=1.0
                )
                results.append(result)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        try:
            analyses = self.result_storage.get_analysis_list()
            
            total_repos = len(analyses)
            total_functions = 0
            total_classes = 0
            languages = {}
            
            for analysis_meta in analyses:
                stats = analysis_meta.get('statistics', {})
                total_functions += stats.get('total_functions', 0)
                total_classes += stats.get('total_classes', 0)
                
                # 统计语言
                analysis_languages = stats.get('languages', {})
                for lang, count in analysis_languages.items():
                    languages[lang] = languages.get(lang, 0) + count
            
            return {
                'total_repositories': total_repos,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'languages': languages
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {
                'total_repositories': 0,
                'total_functions': 0,
                'total_classes': 0,
                'languages': {}
            }
