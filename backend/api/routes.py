"""API 路由模块

定义 4 个业务接口 + 1 个全流程分析接口 + 1 个健康检查接口。
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from backend.schemas.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    TitleOptimizeRequest,
    TitleOptimizeResponse,
    ContentGenerateRequest,
    ContentGenerateResponse,
    StrategyRequest,
    StrategyResponse,
    FullAnalysisRequest,
    FullAnalysisResponse,
    SuggestRequest,
    SuggestResponse,
    CompetitiveAnalysisRequest,
    CompetitiveAnalysisResponse,
    HealthResponse,
    OnboardingReport,
    ProductOnboardingRequest,
    ProductOnboardingResponse,
    VisualAnalysis,
    VisualPrompt,
    VisualAnalysisResponse,
)
from backend.services.llm import chat, chat_stream, chat_vision
from backend.services.prompt import (
    build_analyze_prompt,
    build_title_prompt,
    build_content_prompt,
    build_strategy_prompt,
    build_suggest_prompt,
    build_competitor_prompt,
    build_onboarding_prompt,
    build_visual_prompt,
    build_insight_prompt,
    build_explore_prompt,
    build_strategy_filter_prompt,
    build_generate_prompt,
    build_critic_prompt,
    build_json_format_prompt,
)
from backend.services.excel_parser import parse_product_file
from backend.services.rag import get_rag_service
from backend.services.logger import logger
from backend.config import settings

router = APIRouter()

# 历史记录文件路径
HISTORY_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "history.json"
MAX_HISTORY = 5
_history_lock = asyncio.Lock()


def _load_history() -> list[dict]:
    """加载历史记录"""
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


async def _save_history(entry: dict) -> None:
    """保存历史记录，保留最近 MAX_HISTORY 条"""
    async with _history_lock:
        history = _load_history()
        history.insert(0, entry)
        history = history[:MAX_HISTORY]
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )


async def _call_llm(system: str, user: str, response_model: type) -> dict:
    """调用 LLM 并以 JSON object 模式解析响应

    使用 API 原生 json_object 模式，LLM 承诺只输出 JSON，
    省去手写 JSON 提取逻辑，更稳定也更简洁。
    """
    raw = await chat(system, user, response_format={"type": "json_object"})
    raw = raw.strip()
    # json_object 模式下 LLM 只输出 JSON，偶有代码块包裹
    if raw.startswith("```"):
        parts = raw.split("\n", 1)
        raw = parts[1].strip() if len(parts) > 1 else raw[3:].strip()
    if raw.endswith("```"):
        raw = raw[: raw.rfind("```")].strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="LLM 返回的 JSON 格式错误")
    try:
        return response_model(**data).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"响应数据验证失败: {str(e)}")


# ===================== 健康检查 =====================


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    return HealthResponse(model=settings.llm_model)


# ===================== 历史记录 =====================


@router.get("/history")
async def get_history():
    """获取最近 5 条分析历史记录"""
    return {"history": _load_history()}


@router.delete("/history")
async def delete_history(index: int | None = None):
    """删除历史记录：不传 index 清空全部，传 index 删除指定条"""
    history = _load_history()
    if index is None:
        HISTORY_FILE.write_text("[]", encoding="utf-8")
        return {"ok": True, "deleted": len(history)}
    if 0 <= index < len(history):
        deleted = history.pop(index)
        history = history[:MAX_HISTORY]
        HISTORY_FILE.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return {"ok": True, "deleted": 1, "item": deleted.get("product_name", "")}
    raise HTTPException(status_code=404, detail="记录不存在")


# ===================== 商品智能分析 =====================


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_product(req: AnalyzeRequest):
    """商品智能分析"""
    try:
        rag = get_rag_service()
        rag_context = rag.search(f"{req.product_name} {req.features or ''} 卖点提炼")
        system, user = build_analyze_prompt(
            product_name=req.product_name,
            price=req.price,
            features=req.features,
            target_users=req.target_users,
            rag_context=rag_context,
        )
        return await _call_llm(system, user, AnalyzeResponse)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


# ===================== 标题优化 =====================


@router.post("/title-optimize", response_model=TitleOptimizeResponse)
async def optimize_title(req: TitleOptimizeRequest):
    """AI 商品标题优化"""
    try:
        rag = get_rag_service()
        rag_context = rag.search(f"标题优化 {req.product_name} {req.features or ''}")
        system, user = build_title_prompt(
            original_title=req.original_title,
            product_name=req.product_name,
            features=req.features,
            target_users=req.target_users,
            rag_context=rag_context,
        )
        return await _call_llm(system, user, TitleOptimizeResponse)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标题优化失败: {str(e)}")


# ===================== 营销内容生成 =====================


@router.post("/content-generate", response_model=ContentGenerateResponse)
async def generate_content(req: ContentGenerateRequest):
    """AI 营销内容生成"""
    try:
        rag = get_rag_service()
        if req.platform == "xiaohongshu":
            rag_context = rag.search(f"小红书 内容 种草 {req.product_name}")
        else:
            rag_context = rag.search(
                f"卖点提炼 FAB {req.product_name} {req.features or ''}"
            )
        system, user = build_content_prompt(
            product_name=req.product_name,
            platform=req.platform,
            price=req.price,
            features=req.features,
            target_users=req.target_users,
            rag_context=rag_context,
        )
        return await _call_llm(system, user, ContentGenerateResponse)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内容生成失败: {str(e)}")


# ===================== 运营策略建议 =====================


@router.post("/strategy", response_model=StrategyResponse)
async def generate_strategy(req: StrategyRequest):
    """AI 运营策略建议"""
    try:
        rag = get_rag_service()
        rag_context = rag.search(f"{req.product_name} 运营 推广")
        system, user = build_strategy_prompt(
            product_name=req.product_name,
            price=req.price,
            features=req.features,
            target_users=req.target_users,
            rag_context=rag_context,
        )
        return await _call_llm(system, user, StrategyResponse)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"策略生成失败: {str(e)}")


# ===================== 提示词一键优化 =====================


@router.post("/suggest", response_model=SuggestResponse)
async def suggest_product(req: SuggestRequest):
    """根据商品名称智能补全价格、用户、卖点等信息"""
    try:
        system, user = build_suggest_prompt(product_name=req.product_name)
        return await _call_llm(system, user, SuggestResponse)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能补全失败: {str(e)}")


# ===================== 竞品卡位分析 =====================


@router.post("/competitive-analysis", response_model=CompetitiveAnalysisResponse)
async def competitive_analysis(req: CompetitiveAnalysisRequest):
    """对比商品与竞品，输出差异化策略"""
    try:
        system, user = build_competitor_prompt(
            product_name=req.product_name,
            competitor=req.competitor,
            price=req.price,
            features=req.features,
            target_users=req.target_users,
        )
        return await _call_llm(system, user, CompetitiveAnalysisResponse)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"竞品分析失败: {str(e)}")


# ===================== 全流程分析 =====================


async def _safe_call_llm(
    system: str, user: str, response_model: type, step_name: str
) -> dict:
    """安全的 LLM 调用，失败返回错误信息不抛异常"""
    try:
        return await _call_llm(system, user, response_model)
    except HTTPException as e:
        return {"_error": f"{step_name}失败: {e.detail}"}
    except Exception as e:
        return {"_error": f"{step_name}失败: {str(e)}"}


@router.post("/full-analysis", response_model=FullAnalysisResponse)
async def full_analysis(req: FullAnalysisRequest):
    """全流程商品增长分析

    串行执行：商品分析 → 标题优化 → 营销内容 → 运营策略
    每步独立处理，单步失败不影响后续步骤。
    """
    rag = get_rag_service()
    steps = []

    # Step 1: 商品智能分析
    rag_ctx = rag.search(f"{req.product_name} {req.features or ''} 卖点提炼")
    sys_p, user_p = build_analyze_prompt(
        product_name=req.product_name,
        price=req.price,
        features=req.features,
        target_users=req.target_users,
        rag_context=rag_ctx,
    )
    result = await _safe_call_llm(sys_p, user_p, AnalyzeResponse, "商品分析")
    steps.append(
        {
            "step": 1,
            "name": "商品智能分析",
            "icon": "📊",
            "success": "_error" not in result,
            "data": None if "_error" in result else result,
            "error": result.get("_error"),
        }
    )

    # Step 2: 标题优化
    original = req.original_title or req.product_name
    rag_ctx = rag.search(f"标题优化 {req.product_name} {req.features or ''}")
    sys_p, user_p = build_title_prompt(
        original_title=original,
        product_name=req.product_name,
        features=req.features,
        target_users=req.target_users,
        rag_context=rag_ctx,
    )
    result = await _safe_call_llm(sys_p, user_p, TitleOptimizeResponse, "标题优化")
    steps.append(
        {
            "step": 2,
            "name": "AI 标题优化",
            "icon": "✏️",
            "success": "_error" not in result,
            "data": None if "_error" in result else result,
            "error": result.get("_error"),
        }
    )

    # Step 3: 营销内容生成
    if req.platform == "xiaohongshu":
        rag_ctx = rag.search(f"小红书 内容 种草 {req.product_name}")
    else:
        rag_ctx = rag.search(f"卖点提炼 FAB {req.product_name} {req.features or ''}")
    sys_p, user_p = build_content_prompt(
        product_name=req.product_name,
        platform=req.platform,
        price=req.price,
        features=req.features,
        target_users=req.target_users,
        rag_context=rag_ctx,
    )
    result = await _safe_call_llm(sys_p, user_p, ContentGenerateResponse, "内容生成")
    steps.append(
        {
            "step": 3,
            "name": "营销内容生成",
            "icon": "📝",
            "success": "_error" not in result,
            "data": None if "_error" in result else result,
            "error": result.get("_error"),
        }
    )

    # Step 4: 运营策略建议
    rag_ctx = rag.search(f"{req.product_name} 运营 推广")
    sys_p, user_p = build_strategy_prompt(
        product_name=req.product_name,
        price=req.price,
        features=req.features,
        target_users=req.target_users,
        rag_context=rag_ctx,
    )
    result = await _safe_call_llm(sys_p, user_p, StrategyResponse, "策略生成")
    steps.append(
        {
            "step": 4,
            "name": "运营策略建议",
            "icon": "📈",
            "success": "_error" not in result,
            "data": None if "_error" in result else result,
            "error": result.get("_error"),
        }
    )

    return FullAnalysisResponse(
        product_name=req.product_name,
        steps=steps,
    )


# ===================== SSE 流式全流程分析 =====================


async def _stream_step(
    system: str,
    user: str,
    step_name: str,
    temperature: float | None = None,
    json_output: bool = False,
    max_tokens: int | None = None,
    response_model: type | None = None,
) -> dict:
    """流式调用 LLM + 收集 tokens

    Args:
        json_output: True → 解析 JSON + Pydantic 校验；False → 返回 {"text": "..."}
        max_tokens: 限制输出长度，发散步骤建议 1024，JSON 步骤建议 4096
    """
    tokens: list[str] = []
    kwargs = {}
    if json_output:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        async for token in chat_stream(
            system, user, temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            tokens.append(token)
    except asyncio.CancelledError:
        # 客户端断开连接，停止流式输出
        raise
    except Exception as e:
        return {"_error": f"{step_name}调用失败: {str(e)}"}

    raw = "".join(tokens).strip()

    if not json_output:
        # 防御：LLM 可能意外输出 JSON 包装文本（如 {"text": "xxx"}）
        # 只在仅有一个 "text" 键时才解包，避免误伤正常内容
        if raw.startswith("{") and raw.endswith("}"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "text" in parsed and len(parsed) == 1:
                    inner = parsed["text"]
                    if inner and isinstance(inner, str):
                        raw = inner
            except (json.JSONDecodeError, TypeError):
                pass
        # 防御：清洗 LLM 常见的开场白前缀（循环清理多层前缀）
        raw_before = raw  # 保存清洗前原文，防止过度清洗清空短回复
        for _ in range(5):
            before = raw
            raw = re.sub(
                r"^(好的|OK|行|可以|没问题|明白了|收到指令|收到)[，,。，、]?\s*",
                "",
                raw,
                flags=re.IGNORECASE | re.MULTILINE,
            )
            raw = re.sub(
                r"^作为.+?(专家|负责人|助手|AI|策略师)[，,。，、]?\s*",
                "",
                raw,
                flags=re.MULTILINE,
            )
            raw = re.sub(
                r"^以下(是|为).+?[：:]\s*",
                "",
                raw,
                flags=re.MULTILINE,
            )
            raw = raw.strip()
            if raw == before:
                break
        raw = raw.strip()
        # 清除混入输出的系统指令片段（如 ## 输出规则 / ## 工作原则 整段）
        raw = re.sub(
            r"(?im)^(##\s*输出规则|##\s*工作原则).*(\n- .*)*\n?",
            "",
            raw,
        )
        raw = raw.strip()
        # 空文本：标记为错误，防止占位文本污染下游上下文
        if not raw or not raw.strip():
            # 如果清洗前有内容，回退到清洗前原文，避免误杀短回复
            if raw_before and raw_before.strip():
                raw = raw_before.strip()
            # 内容审核返回空 = 无需修改，给兜底值
            elif step_name == "内容审核":
                raw = "无需修改"
            else:
                return {"_error": f"{step_name}未能生成有效内容（LLM 返回为空）"}
        return {"text": raw}

    if raw.startswith("```"):
        parts = raw.split("\n", 1)
        raw = parts[1].strip() if len(parts) > 1 else raw[3:].strip()
    if raw.endswith("```"):
        raw = raw[: raw.rfind("```")].strip()
    # 提取最外层 { }，兼容模型在 JSON 前后加说明文字
    first_brace = raw.find("{")
    last_brace = raw.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        raw = raw[first_brace:last_brace + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 尝试修复常见问题：尾部多余逗号
        try:
            import re as _re
            fixed = _re.sub(r",\s*([}\]])", r"\1", raw)
            data = json.loads(fixed)
        except (json.JSONDecodeError, Exception):
            return {"_error": f"{step_name}: LLM 返回的 JSON 格式错误"}
    if response_model:
        try:
            return response_model(**data).model_dump()
        except Exception as e:
            return {"_error": f"{step_name}: 数据校验失败: {str(e)}"}
    return {"text": raw, "json": data}


@router.post("/full-analysis/stream")
async def full_analysis_stream(req: FullAnalysisRequest):
    """SSE 流式全流程分析

    逐步推送事件：step_start → step_end（每步）→ complete
    前端可以逐条渲染，不需要等全部完成。
    """

    async def event_generator():
        logger.info(f"全流程分析开始: {req.product_name}")
        rag = get_rag_service()
        rag_ctx = rag.search(f"{req.product_name} {req.features or ''} 卖点提炼")

        # 6 阶段 Agent Workflow
        steps_config = [
            {
                "name": "商品洞察",
                "icon": "🔍",
                "build_prompt": lambda ctx="": build_insight_prompt(
                    product_name=req.product_name,
                    price=req.price,
                    features=req.features,
                    target_users=req.target_users,
                    rag_context=rag_ctx,
                ),
                "temp": settings.agent_insight_temp,
                "json_output": False,
                "max_tokens": 768,
            },
            {
                "name": "营销方向探索",
                "icon": "💡",
                "build_prompt": lambda ctx="": build_explore_prompt(
                    ctx,
                    product_name=req.product_name,
                    price=req.price,
                    features=req.features,
                    target_users=req.target_users,
                ),
                "temp": settings.agent_explore_temp,
                "json_output": False,
                "max_tokens": 768,
            },
            {
                "name": "策略筛选",
                "icon": "🎯",
                "build_prompt": lambda ctx="": build_strategy_filter_prompt(
                    ctx,
                    product_name=req.product_name,
                    price=req.price,
                    features=req.features,
                    target_users=req.target_users,
                ),
                "temp": settings.agent_strategy_temp,
                "json_output": False,
                "max_tokens": 2048,
            },
            {
                "name": "内容生成",
                "icon": "📝",
                "build_prompt": lambda ctx="": build_generate_prompt(
                    ctx,
                    product_name=req.product_name,
                    price=req.price,
                    features=req.features,
                    target_users=req.target_users,
                ),
                "temp": settings.agent_generate_temp,
                "json_output": False,
                "max_tokens": 4096,
            },
            {
                "name": "内容审核",
                "icon": "🔎",
                "build_prompt": lambda ctx="": build_critic_prompt(
                    ctx,
                    product_name=req.product_name,
                    price=req.price,
                    features=req.features,
                    target_users=req.target_users,
                ),
                "temp": settings.agent_critic_temp,
                "json_output": False,
                "max_tokens": 1536,
            },
            {
                "name": "运营素材汇总",
                "icon": "📋",
                "build_prompt": lambda ctx="": build_json_format_prompt(
                    ctx,
                    product_name=req.product_name,
                    price=req.price,
                    features=req.features,
                    target_users=req.target_users,
                ),
                "temp": settings.agent_json_temp,
                "json_output": True,
                "max_tokens": 8192,
            },
        ]

        success_count = 0
        step_results = []
        context = ""  # 上一步输出，传递给下一步
        plan_text = ""  # Step ④ 的完整方案，供 Step ⑥ 使用（Step ⑤ 只输出碎片）

        for i, cfg in enumerate(steps_config, 1):
            yield f"data: {json.dumps({'type': 'step_start', 'step': i, 'name': cfg['name'], 'icon': cfg['icon']})}\n\n"

            # Step ⑥ 需要完整方案，而非 Step ⑤ 的问题列表碎片
            if cfg["name"] == "运营素材汇总":
                sys_p, user_p = cfg["build_prompt"](plan_text)
            else:
                sys_p, user_p = cfg["build_prompt"](context)
            result = await _stream_step(
                sys_p,
                user_p,
                cfg["name"],
                temperature=cfg["temp"],
                json_output=cfg["json_output"],
                max_tokens=cfg.get("max_tokens"),
            )

            if "_error" not in result:
                success_count += 1
                step_results.append(
                    {
                        "step": i,
                        "name": cfg["name"],
                        "icon": cfg["icon"],
                        "success": True,
                        "data": result,
                    }
                )
                yield f"data: {json.dumps({'type': 'step_end', 'step': i, 'success': True, 'data': result})}\n\n"
                # 传递上下文给下一步
                context = (
                    result.get("text", "")
                    if isinstance(result.get("text"), str)
                    else json.dumps(result, ensure_ascii=False)[:5000]
                )
                # Step ⑥ 需要完整方案（Step ⑤ 只输出问题列表碎片）
                if cfg["name"] == "内容生成":
                    plan_text = context
            else:
                step_results.append(
                    {
                        "step": i,
                        "name": cfg["name"],
                        "icon": cfg["icon"],
                        "success": False,
                        "error": result["_error"],
                    }
                )
                yield f"data: {json.dumps({'type': 'step_end', 'step': i, 'success': False, 'error': result['_error']})}\n\n"
                logger.warning(f"  ✗ {cfg['name']}: {result['_error']}")
                # Critic 失败不阻断后续步骤
                if cfg["name"] != "内容审核":
                    break

        logger.info(f"全流程分析完成: {success_count}/{len(steps_config)}")
        yield f"data: {json.dumps({'type': 'complete', 'product_name': req.product_name, 'success': success_count, 'total': len(steps_config)})}\n\n"

        await _save_history(
            {
                "type": "full",
                "product_name": req.product_name,
                "timestamp": datetime.now().strftime("%m-%d %H:%M"),
                "summary": f"全流程分析 · {success_count}/{len(steps_config)} 成功",
                "steps": step_results,
            }
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ===================== 商品 Excel 上传 =====================


@router.post("/upload-products")
async def upload_products(file: UploadFile = File(...)):
    """上传商品 Excel 文件，返回解析后的商品列表"""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(
            status_code=400, detail="仅支持 .xlsx / .xls / .csv 格式的文件"
        )
    try:
        file_bytes = await file.read()
        products = parse_product_file(file_bytes, file.filename)
        if not products:
            raise HTTPException(
                status_code=400,
                detail="未在文件中找到有效商品数据，请检查表头是否包含「商品名称」列",
            )
        return {"count": len(products), "products": products}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")


# ===================== 商品上新运营分析 =====================


@router.post("/product-onboarding", response_model=ProductOnboardingResponse)
async def product_onboarding(req: ProductOnboardingRequest):
    """商品上新运营分析
    为每个商品生成包含定位、用户、痛点、卖点、关键词、标题、详情页、小红书内容的完整运营报告。
    """
    rag = get_rag_service()
    reports = []
    for product in req.products:
        try:
            product_dict = product.model_dump()
            rag_context = rag.search(
                f"{product_dict.get('product_name', '')} {product_dict.get('selling_points', '')} 运营 卖点"
            )
            system, user = build_onboarding_prompt(
                product_dict, rag_context=rag_context
            )
            report_data = await _call_llm(system, user, OnboardingReport)
            report_data["product_name"] = product_dict["product_name"]
            reports.append(report_data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"商品「{product.product_name}」分析失败: {str(e)}",
            )
    result = ProductOnboardingResponse(reports=reports)
    # 保存历史
    _save_history(
        {
            "type": "onboarding",
            "product_name": req.products[0].product_name
            if len(req.products) == 1
            else f"{req.products[0].product_name} 等{len(req.products)}件",
            "timestamp": datetime.now().strftime("%m-%d %H:%M"),
            "summary": f"商品上新 · {len(reports)} 件商品运营报告",
            "reports": [r for r in reports],
        }
    )
    return result


# ===================== AI 商品视觉策划 =====================


@router.post("/visual-analysis", response_model=VisualAnalysisResponse)
async def visual_analysis(
    images: list[UploadFile] = File(...),
    product_name: str = "",
    features: str = "",
    target_users: str = "",
):
    """商品视觉分析与 Prompt 生成

    上传 1-3 张商品图片，视觉模型分析后生成 5 个电商场景的 AI 生图 Prompt。
    """
    # 验证图片
    if not images:
        raise HTTPException(status_code=400, detail="请至少上传 1 张商品图片")
    if len(images) > 3:
        raise HTTPException(status_code=400, detail="最多上传 3 张图片")

    for img in images:
        if not img.filename or not img.filename.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):
            raise HTTPException(
                status_code=400,
                detail=f"图片「{img.filename}」格式不支持，仅支持 jpg/png/webp",
            )

    try:
        # 读取所有图片为二进制
        image_bytes = [await img.read() for img in images]

        # RAG 检索视觉知识
        rag = get_rag_service()
        rag_context = rag.search(
            f"商品摄影 {product_name} {features or ''} 电商视觉 AI绘图 Prompt"
        )

        # 构建 Prompt
        system, user = build_visual_prompt(
            product_name=product_name,
            features=features or None,
            target_users=target_users or None,
            rag_context=rag_context,
        )

        # 调用视觉模型
        raw = await chat_vision(
            system_prompt=system,
            user_text=user,
            images=image_bytes,
            response_format={"type": "json_object"},
        )
        raw = raw.strip()
        if raw.startswith("```"):
            parts = raw.split("\n", 1)
            raw = parts[1].strip() if len(parts) > 1 else raw[3:].strip()
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")].strip()
        # 提取最外层 { } + 修复尾部逗号
        first_brace = raw.find("{")
        last_brace = raw.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            raw = raw[first_brace:last_brace + 1]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            fixed = re.sub(r",\s*([}\]])", r"\1", raw)
            data = json.loads(fixed)

        # 验证数据
        analysis = VisualAnalysis(**data["visual_analysis"])
        prompts = [VisualPrompt(**p) for p in data["prompts"]]
        result = VisualAnalysisResponse(
            visual_analysis=analysis,
            consistency_constraint=data.get("consistency_constraint", ""),
            prompts=prompts,
        )
        # 保存历史
        await _save_history(
            {
                "type": "visual",
                "product_name": product_name or "商品图片",
                "timestamp": datetime.now().strftime("%m-%d %H:%M"),
                "summary": f"视觉策划 · {analysis.category}",
                "visual_analysis": analysis.model_dump(),
                "prompts": [p.model_dump() for p in prompts],
            }
        )
        return result
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="视觉模型返回的 JSON 格式错误")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视觉分析失败: {str(e)}")
