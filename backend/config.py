"""应用配置模块

从 .env 文件读取 LLM API 配置，支持 DeepSeek / Qwen / GPT 等 OpenAI 兼容接口。
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # LLM（文本模型）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-v4-flash"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # 视觉模型（用于商品图片分析）
    # 默认使用 Qwen-VL-Max，通过阿里云 DashScope 兼容端点
    vision_api_key: str = ""
    vision_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    vision_model: str = "qwen-vl-max"
    vision_temperature: float = 0.6
    vision_max_tokens: int = 4096

    # Agent Workflow 各阶段温度
    agent_insight_temp: float = 0.7
    agent_explore_temp: float = 1.0
    agent_strategy_temp: float = 0.5
    agent_generate_temp: float = 0.8
    agent_critic_temp: float = 0.7
    agent_json_temp: float = 0.3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# 启动时校验关键配置
if not settings.llm_api_key:
    import sys

    print(
        "[WARNING] llm_api_key 未配置，LLM 调用将失败。请在 .env 文件中设置 llm_api_key。",
        file=sys.stderr,
    )
