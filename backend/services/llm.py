"""LLM 调用模块

封装 OpenAI 兼容客户端，支持 DeepSeek / Qwen / GPT 等模型。
通过 .env 配置即可切换模型。

特性：
- 自动重试（最多 3 次）
- 请求超时（60s）
- response_format 支持（json_object 模式）
- 流式调用（SSE streaming）
- 多模态视觉调用（chat_vision）
"""

import base64
from collections.abc import AsyncGenerator

from openai import (
    APIError,
    APITimeoutError,
    AuthenticationError,
    AsyncOpenAI,
    RateLimitError,
)
from backend.config import settings
from backend.services.logger import logger

# 全局客户端，复用连接池
_text_client: AsyncOpenAI | None = None
_vision_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """获取文本 LLM 客户端单例"""
    global _text_client
    if _text_client is None:
        _text_client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            max_retries=3,
            timeout=60.0,
        )
    return _text_client


def get_vision_client() -> AsyncOpenAI:
    """获取视觉模型客户端单例

    视觉模型 API Key 默认复用文本模型 Key；
    可在 .env 中单独设置 VISION_API_KEY。
    """
    global _vision_client
    if _vision_client is None:
        _vision_client = AsyncOpenAI(
            api_key=settings.vision_api_key or settings.llm_api_key,
            base_url=settings.vision_base_url,
            max_retries=2,
            timeout=90.0,
        )
    return _vision_client


async def chat(
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> str:
    """调用 LLM 生成回复

    Args:
        system_prompt: 系统角色设定
        user_prompt: 用户输入
        temperature: 生成温度，默认使用配置值
        max_tokens: 最大输出 token 数，默认使用配置值
        response_format: 响应格式约束，如 {"type": "json_object"}

    Returns:
        模型生成的文本内容

    Raises:
        Exception: API 调用失败时抛出（重试耗尽后）
    """
    client = get_client()
    kwargs: dict = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature or settings.llm_temperature,
        "max_tokens": max_tokens or settings.llm_max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format
    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


async def chat_stream(
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> AsyncGenerator[str, None]:
    """流式调用 LLM，逐 token 产出

    用法：async for token in chat_stream(system, user):
    """
    client = get_client()
    kwargs: dict = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature or settings.llm_temperature,
        "max_tokens": max_tokens or settings.llm_max_tokens,
        "stream": True,
    }
    if response_format:
        kwargs["response_format"] = response_format
    stream = await client.chat.completions.create(**kwargs)
    async for chunk in stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if delta and delta.content:
            yield delta.content


async def chat_vision(
    system_prompt: str,
    user_text: str,
    images: list[bytes],
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
) -> str:
    """调用视觉模型分析商品图片

    Args:
        system_prompt: 系统角色设定
        user_text: 用户文本输入
        images: 图片二进制数据列表（jpg/png/webp）
        temperature: 生成温度，默认使用视觉模型配置值
        max_tokens: 最大输出 token 数
        response_format: 响应格式（如 json_object）

    Returns:
        模型文本输出
    """
    client = get_vision_client()

    # 构建多模态消息内容
    user_content: list[dict] = [{"type": "text", "text": user_text}]
    for img_bytes in images:
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        # 检测图片类型
        if img_bytes[:4] == b"\x89PNG":
            mime = "image/png"
        elif img_bytes[:2] == b"\xff\xd8":
            mime = "image/jpeg"
        elif img_bytes[:4] == b"RIFF":
            mime = "image/webp"
        else:
            mime = "image/jpeg"  # fallback
        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            }
        )

    kwargs: dict = {
        "model": settings.vision_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": temperature
        if temperature is not None
        else settings.vision_temperature,
        "max_tokens": max_tokens or settings.vision_max_tokens,
    }
    if response_format:
        kwargs["response_format"] = response_format

    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""
