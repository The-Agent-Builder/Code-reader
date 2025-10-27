"""
大模型调用工具类
提供统一的 LLM API 调用接口
"""

import time
from typing import Dict, List, Any, Optional, Union, Generator
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from config import Settings


class LLMCaller:
    """大模型调用器 - 封装 OpenAI API 调用"""
    
    def __init__(self, config: Optional[Settings] = None):
        """
        初始化大模型调用器
        
        Args:
            config: 配置对象，如果为 None 则使用默认配置
        """
        if config is None:
            config = Settings()
            
        self.api_key = config.OPENAI_API_KEY
        self.base_url = config.OPENAI_BASE_URL
        self.model = config.OPENAI_MODEL
        self.timeout = config.LLM_REQUEST_TIMEOUT
        self.retry_delay = config.LLM_RETRY_DELAY
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        # 初始化同步和异步客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
        
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    def call(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[ChatCompletion, Generator[ChatCompletionChunk, None, None]]:
        """
        同步调用大模型
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，默认使用配置中的模型
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            stream: 是否使用流式响应
            **kwargs: 其他参数传递给 OpenAI API
            
        Returns:
            ChatCompletion 对象或流式生成器
        """
        if model is None:
            model = self.model
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            return response
        except Exception as e:
            raise RuntimeError(f"LLM API 调用失败: {str(e)}") from e
    
    async def acall(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[ChatCompletion, Any]:
        """
        异步调用大模型
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，默认使用配置中的模型
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            stream: 是否使用流式响应
            **kwargs: 其他参数传递给 OpenAI API
            
        Returns:
            ChatCompletion 对象或异步流式生成器
        """
        if model is None:
            model = self.model
        
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            return response
        except Exception as e:
            raise RuntimeError(f"LLM API 异步调用失败: {str(e)}") from e
    
    def call_with_retry(
        self,
        messages: List[Dict[str, str]],
        max_retries: int = 3,
        **kwargs
    ) -> ChatCompletion:
        """
        带重试机制的同步调用
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
            **kwargs: 其他参数传递给 call 方法
            
        Returns:
            ChatCompletion 对象
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.call(messages, **kwargs)
                if isinstance(response, ChatCompletion):
                    return response
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                    time.sleep(wait_time)
                    continue
        
        raise RuntimeError(
            f"LLM API 调用失败，已重试 {max_retries} 次。最后一次错误: {str(last_error)}"
        ) from last_error
    
    async def acall_with_retry(
        self,
        messages: List[Dict[str, str]],
        max_retries: int = 3,
        **kwargs
    ) -> ChatCompletion:
        """
        带重试机制的异步调用
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
            **kwargs: 其他参数传递给 acall 方法
            
        Returns:
            ChatCompletion 对象
        """
        import asyncio
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = await self.acall(messages, **kwargs)
                if isinstance(response, ChatCompletion):
                    return response
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                    await asyncio.sleep(wait_time)
                    continue
        
        raise RuntimeError(
            f"LLM API 异步调用失败，已重试 {max_retries} 次。最后一次错误: {str(last_error)}"
        ) from last_error
    
    def get_text_response(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        获取纯文本响应（同步）
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数传递给 call 方法
            
        Returns:
            生成的文本内容
        """
        response = self.call(messages, stream=False, **kwargs)
        if isinstance(response, ChatCompletion):
            return response.choices[0].message.content or ""
        return ""
    
    async def aget_text_response(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        获取纯文本响应（异步）
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数传递给 acall 方法
            
        Returns:
            生成的文本内容
        """
        response = await self.acall(messages, stream=False, **kwargs)
        if isinstance(response, ChatCompletion):
            return response.choices[0].message.content or ""
        return ""
    
    @staticmethod
    def create_messages(
        system_prompt: Optional[str] = None,
        user_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        创建标准格式的消息列表
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户输入
            history: 历史对话记录
            
        Returns:
            消息列表
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
        
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
        
        return messages


# 创建全局单例实例
_llm_caller_instance: Optional[LLMCaller] = None


def get_llm_caller() -> LLMCaller:
    """
    获取 LLMCaller 单例实例
    
    Returns:
        LLMCaller 实例
    """
    global _llm_caller_instance
    if _llm_caller_instance is None:
        _llm_caller_instance = LLMCaller()
    return _llm_caller_instance

if __name__ == "__main__":
    llm_caller = get_llm_caller()
    response = llm_caller.get_text_response(
        messages=[{"role": "user", "content": "Hello, how are you?"}],
    )
    print(response)