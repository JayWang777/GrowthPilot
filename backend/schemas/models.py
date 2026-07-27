"""数据模型定义

定义所有 API 的请求/响应 Pydantic 模型。
"""

from pydantic import BaseModel, Field
from typing import Optional


# ===================== 共享子模型 =====================


class Reasoning(BaseModel):
    """推理链条——展示 AI 从输入到输出的逻辑路径"""

    from_: str = Field(..., alias="from", description="推理的来源信息")
    chain: str = Field(..., description="推理过程描述")

    model_config = {"populate_by_name": True}


# ===================== 请求模型 =====================


class ProductInfo(BaseModel):
    """商品基本信息，多个 API 复用"""

    product_name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    price: Optional[str] = Field(None, max_length=50, description="商品价格")
    features: Optional[str] = Field(None, max_length=1000, description="商品特点描述")
    target_users: Optional[str] = Field(
        None, max_length=500, description="目标用户描述"
    )


class AnalyzeRequest(ProductInfo):
    """商品分析请求"""

    pass


class TitleOptimizeRequest(BaseModel):
    """标题优化请求"""

    original_title: str = Field(..., min_length=1, max_length=200, description="原标题")
    product_name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    features: Optional[str] = Field(None, max_length=1000, description="商品特点")
    target_users: Optional[str] = Field(None, max_length=500, description="目标用户")


class ContentGenerateRequest(ProductInfo):
    """营销内容生成请求"""

    platform: str = Field(
        ..., pattern="^(xiaohongshu|taobao|douyin)$", description="内容平台"
    )


class StrategyRequest(ProductInfo):
    """运营策略请求"""

    pass


class SuggestRequest(BaseModel):
    """提示词一键优化请求——只填商品名，AI 自动补全"""

    product_name: str = Field(..., min_length=1, max_length=200, description="商品名称")


class CompetitiveAnalysisRequest(BaseModel):
    """竞品卡位分析请求"""

    product_name: str = Field(
        ..., min_length=1, max_length=200, description="自己的商品"
    )
    price: Optional[str] = Field(None, max_length=50, description="自己的价格")
    features: Optional[str] = Field(None, max_length=1000, description="自己的特点")
    target_users: Optional[str] = Field(
        None, max_length=500, description="自己的目标用户"
    )
    competitor: str = Field(..., min_length=1, max_length=2000, description="竞品描述")


# ===================== 响应模型 =====================


class Positioning(BaseModel):
    """商品定位"""

    target_users: str = Field(..., description="目标用户画像")
    scenario: str = Field(..., description="消费场景")


class SellingPoint(BaseModel):
    """卖点"""

    rank: int = Field(..., description="重要程度排序")
    point: str = Field(..., description="卖点描述")


class AnalyzeResponse(BaseModel):
    """商品分析响应"""

    positioning: Positioning
    pain_points: list[str] = Field(..., description="用户痛点列表")
    selling_points: list[SellingPoint] = Field(
        ..., description="核心卖点（按重要程度排序）"
    )
    reasoning: Optional[Reasoning] = Field(
        None, description="推理链条——为什么选择这些定位"
    )


class TitleOption(BaseModel):
    """标题选项"""

    title: str = Field(..., description="优化标题")
    reason: str = Field(..., description="优化原因")


class TitleOptimizeResponse(BaseModel):
    """标题优化响应"""

    optimized_titles: list[TitleOption] = Field(..., description="优化标题列表")
    reasoning: Optional[Reasoning] = Field(
        None, description="推理链条——原标题到优化方案的分析路径"
    )


class ContentScore(BaseModel):
    """内容版本自评分"""

    转化力: int = Field(..., ge=1, le=10, description="转化能力评分")
    记忆点: int = Field(..., ge=1, le=10, description="用户记忆度评分")
    真实感: int = Field(..., ge=1, le=10, description="内容真实度评分")


class ContentVersion(BaseModel):
    """内容版本"""

    angle: str = Field(
        ..., description="版本角度（如：情绪共鸣 / 功效举证 / 场景种草）"
    )
    title: str = Field(..., description="该版本标题")
    content: str = Field(..., description="该版本正文")
    tags: list[str] = Field(..., description="该版本推荐标签")
    scores: ContentScore = Field(..., description="自评分")


class ContentGenerateResponse(BaseModel):
    """营销内容生成响应"""

    versions: list[ContentVersion] = Field(
        ..., min_length=3, max_length=3, description="3 个不同角度的内容版本"
    )
    reasoning: Optional[Reasoning] = Field(
        None, description="推理链条——为什么选择这些内容方向"
    )


class ContentDirection(BaseModel):
    """内容方向"""

    title: str = Field(..., description="内容标题/主题")
    description: str = Field(..., description="内容思路说明")


class PlatformSuggestion(BaseModel):
    """平台建议"""

    platform: str = Field(..., description="平台名称")
    strategy: str = Field(..., description="运营策略")


class StrategyResponse(BaseModel):
    """运营策略建议响应"""

    target_users: str = Field(..., description="推荐目标用户")
    content_directions: list[ContentDirection] = Field(..., description="内容方向建议")
    platform_suggestions: list[PlatformSuggestion] = Field(
        ..., description="平台运营建议"
    )
    reasoning: Optional[Reasoning] = Field(None, description="推理链条——策略制定依据")


class SuggestResponse(BaseModel):
    """提示词一键优化响应"""

    price: str = Field(..., description="建议价格区间")
    target_users: str = Field(..., description="建议目标用户")
    features: str = Field(..., description="建议填写的商品特点")
    positioning: str = Field(..., description="一句话卖点定位")


class CompetitiveAnalysisResponse(BaseModel):
    """竞品卡位分析响应"""

    competitor_positioning: str = Field(..., description="竞品定位分析")
    competitor_strengths: list[str] = Field(..., description="竞品优势")
    our_differentiation: str = Field(..., description="我们的差异点")
    suggested_angle: str = Field(..., description="建议内容切入角度")
    learnable_points: list[str] = Field(..., description="可借鉴的点")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field("ok", description="服务状态")
    model: str = Field(..., description="当前使用的 LLM 模型")


# ===================== 全流程分析 =====================


class FullAnalysisRequest(ProductInfo):
    """全流程分析请求"""

    original_title: Optional[str] = Field(None, max_length=200, description="原标题")
    platform: str = Field(
        "xiaohongshu",
        pattern="^(xiaohongshu|taobao|douyin)$",
        description="内容平台",
    )


class StepResult(BaseModel):
    """单步执行结果"""

    success: bool = Field(..., description="是否成功")
    data: Optional[dict] = Field(None, description="结果数据")
    error: Optional[str] = Field(None, description="错误信息")


class FullAnalysisResponse(BaseModel):
    """全流程分析响应"""

    product_name: str = Field(..., description="商品名称")
    steps: list[dict] = Field(
        ..., description="各步骤结果（按顺序：分析→标题→内容→策略）"
    )


# ===================== 商品上新运营分析 =====================


class ProductRow(BaseModel):
    """Excel 中的一行商品资料"""

    product_name: str = Field(..., description="商品名称")
    price: str = Field("", description="价格")
    category: str = Field("", description="分类")
    description: str = Field("", description="商品描述")
    specs: str = Field("", description="规格参数")
    selling_points: str = Field("", description="卖点")


class ProductOnboardingRequest(BaseModel):
    """商品上新分析请求"""

    products: list[ProductRow] = Field(
        ..., min_length=1, max_length=20, description="商品列表"
    )


class OnboardingReport(BaseModel):
    """单个商品的上新运营报告

    注意：product_name 由后端从请求中注入，不在 LLM 输出里。
    """

    product_name: str = Field("", description="商品名称（后端注入）")
    positioning: str = Field(..., description="商品定位")
    target_users: str = Field(..., description="目标用户画像")
    pain_points: list[str] = Field(..., description="消费痛点（≥3条）")
    selling_points: list[str] = Field(..., description="核心卖点（≥3条）")
    search_keywords: list[str] = Field(..., description="搜索关键词（≥10个）")
    ecommerce_titles: list[str] = Field(..., description="电商标题方案（≥3个）")
    detail_page_structure: str = Field(..., description="商品详情页结构建议")
    xiaohongshu_content: str = Field(..., description="小红书内容建议")


class ProductOnboardingResponse(BaseModel):
    """商品上新分析响应"""

    reports: list[OnboardingReport] = Field(..., description="各商品的运营报告")


# ===================== AI 商品视觉策划 =====================


class VisualAnalysis(BaseModel):
    """视觉模型对商品图片的分析结果"""

    category: str = Field(..., description="商品类别")
    color: str = Field(..., description="主要颜色（含色相描述）")
    material: str = Field(..., description="材质分析")
    texture: str = Field(..., description="质感/纹理特征")
    shape_features: str = Field(..., description="形态结构特点")
    selling_point_visual: str = Field(..., description="可从视觉上突出的核心卖点")
    target_users: str = Field(..., description="基于视觉风格推断的目标用户画像")


class VisualPrompt(BaseModel):
    """单个视觉场景的 AI 生图 Prompt"""

    scene: str = Field(
        ...,
        description="场景名称（商品主图/材质细节图/使用场景图/功能说明图/小红书种草图）",
    )
    purpose: str = Field(..., description="图片用途说明")
    marketing_goal: str = Field(..., description="营销目标")
    prompt: str = Field(
        ..., description="正向 AI 绘图 Prompt（英文，含商品一致性约束）"
    )
    negative_prompt: str = Field(..., description="负向 Prompt")
    consistency_note: str = Field(..., description="本场景下需特别注意的商品一致性要点")


class VisualAnalysisResponse(BaseModel):
    """视觉分析完整响应"""

    visual_analysis: VisualAnalysis = Field(..., description="商品视觉分析结果")
    consistency_constraint: str = Field(..., description="全局商品一致性约束文字")
    prompts: list[VisualPrompt] = Field(
        ..., min_length=5, max_length=5, description="5 个场景的 AI 生图 Prompt"
    )
