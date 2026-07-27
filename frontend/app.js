/**
 * AI 商品增长运营助手 - 前端交互
 *
 * 功能：一键补全 / 竞品分析 / SSE 流式全流程 / 逻辑链展示
 */

// ===================== API =====================
const API_BASE = '/api';

// ===================== DOM =====================
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const startBtn = $('#startBtn');
const suggestBtn = $('#suggestBtn');
const resultCard = $('#resultCard');
const resultContent = $('#resultContent');
const errorCard = $('#errorCard');
const errorText = $('#errorText');
const productName = $('#productName');
const productPrice = $('#productPrice');
const targetUsers = $('#targetUsers');
const productFeatures = $('#productFeatures');

// 竞品分析
const competitorToggle = $('#competitorToggle');
const competitorBody = $('#competitorBody');
const competitorInput = $('#competitorInput');
const competitorBtn = $('#competitorBtn');
const competitorSpinner = $('#competitorSpinner');
const competitorResult = $('#competitorResult');

// 侧栏工具
const toolSuggest = $('#toolSuggest');
const toolCompetitor = $('#toolCompetitor');
const toolVisual = $('#toolVisual');

// ===================== 验证 =====================

function validateForm() {
    if (!productName.value.trim()) {
        showError('请填写商品名称');
        productName.focus();
        return false;
    }
    if (productName.value.trim().length > 200) {
        showError('商品名称过长');
        return false;
    }
    return true;
}

/** 构建请求体 */
function buildPayload() {
    const payload = {
        product_name: productName.value.trim(),
        price: productPrice.value.trim() || null,
        features: productFeatures.value.trim() || null,
        target_users: targetUsers.value.trim() || null,
        platform: 'xiaohongshu',
    };
    Object.keys(payload).forEach((k) => {
        if (payload[k] === null) delete payload[k];
    });
    return payload;
}

// ===================== 状态 =====================

function setLoading(loading) {
    startBtn.disabled = loading;
    if (loading) {
        startBtn.textContent = '分析中...';
    } else {
        startBtn.innerHTML =
            '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2V14M2 8H14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg> 生成运营方案';
    }
}

function showError(msg) {
    errorCard.style.display = 'flex';
    errorText.textContent = msg;
    setLoading(false);
}

function hideError() {
    errorCard.style.display = 'none';
}

function resetResults() {
    resultCard.style.display = 'none';
    hideError();
}

// ===================== 点击事件 =====================

startBtn.addEventListener('click', async () => {
    if (!validateForm()) return;
    await startFullStream();
});

// ===================== 提示词一键优化 =====================

suggestBtn.addEventListener('click', async () => {
    const name = productName.value.trim();
    if (!name) {
        showError('请先填写商品名称');
        productName.focus();
        return;
    }
    suggestBtn.disabled = true;
    suggestBtn.textContent = '分析中...';
    hideError();

    try {
        const resp = await fetch(API_BASE + '/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_name: name }),
        });
        if (!resp.ok) throw new Error('请求失败');
        const data = await resp.json();
        productPrice.value = data.price || '';
        targetUsers.value = data.target_users || '';
        productFeatures.value = data.features || '';
    } catch (err) {
        showError('智能补全失败: ' + err.message);
    } finally {
        suggestBtn.disabled = false;
        suggestBtn.textContent = '✨ AI 帮我填';
    }
});

// ===================== 竞品分析 =====================

competitorToggle.addEventListener('click', () => {
    competitorToggle.classList.toggle('open');
    competitorBody.classList.toggle('open');
});

competitorBtn.addEventListener('click', async () => {
    const competitor = competitorInput.value.trim();
    if (!competitor) {
        competitorResult.style.display = 'block';
        competitorResult.innerHTML =
            '<p style="color:#dc2626;font-size:13px;">请描述竞品信息</p>';
        return;
    }

    competitorBtn.disabled = true;
    competitorBtn.querySelector('span').textContent = '分析中...';
    competitorSpinner.style.display = 'inline-block';
    competitorResult.style.display = 'none';

    const payload = {
        product_name: productName.value.trim() || '未知商品',
        competitor,
    };
    const price = productPrice.value.trim();
    const features = productFeatures.value.trim();
    const users = targetUsers.value.trim();
    if (price) payload.price = price;
    if (features) payload.features = features;
    if (users) payload.target_users = users;

    try {
        const resp = await fetch(API_BASE + '/competitive-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!resp.ok) throw new Error('请求失败');
        const data = await resp.json();
        renderCompetitorResult(data);
    } catch (err) {
        competitorResult.style.display = 'block';
        competitorResult.innerHTML =
            '<p style="color:#dc2626;font-size:13px;">竞品分析失败: ' +
            err.message +
            '</p>';
    } finally {
        competitorBtn.disabled = false;
        competitorBtn.querySelector('span').textContent = '开始竞品分析';
        competitorSpinner.style.display = 'none';
    }
});

function renderCompetitorResult(data) {
    const html = `
        <div class="competitor-section-label">🎯 竞品定位</div>
        <p>${esc(data.competitor_positioning)}</p>

        <div class="competitor-section-label">💪 竞品优势</div>
        <ul>${data.competitor_strengths.map((s) => `<li>${esc(s)}</li>`).join('')}</ul>

        <div class="competitor-section-label">🔑 我们的差异点</div>
        <p>${esc(data.our_differentiation)}</p>

        <div class="competitor-section-label">📝 建议切入角度</div>
        <p>${esc(data.suggested_angle)}</p>

        <div class="competitor-section-label">👀 可借鉴的点</div>
        <ul>${data.learnable_points.map((p) => `<li>${esc(p)}</li>`).join('')}</ul>
    `;
    competitorResult.innerHTML = html;
    competitorResult.style.display = 'block';
}

// ===================== 侧栏工具快捷入口 =====================

toolSuggest.addEventListener('click', () => {
    document
        .querySelector('.create-card')
        ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => productName.focus(), 300);
});

toolCompetitor.addEventListener('click', () => {
    document
        .querySelector('.create-card')
        ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(() => {
        competitorToggle.classList.add('open');
        competitorBody.classList.add('open');
        competitorInput.focus();
    }, 300);
});

toolVisual.addEventListener('click', () => {
    document
        .getElementById('visualCard')
        ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

// ===================== SSE 流式全流程 =====================

async function startFullStream() {
    const data = buildPayload();
    const url = API_BASE + '/full-analysis/stream';

    resultContent.innerHTML = '';
    resultCard.style.display = 'block';
    setLoading(true);
    hideError();

    try {
        const resp = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!resp.ok) throw new Error('请求失败 (' + resp.status + ')');

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const parts = buffer.split('\n\n');
            buffer = parts.pop() || '';
            for (const part of parts) {
                for (const line of part.split('\n')) {
                    if (line.startsWith('data: ')) {
                        try {
                            handleStreamEvent(JSON.parse(line.slice(6)));
                        } catch (_) {}
                    }
                }
            }
        }

        setLoading(false);
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
        showError(err.message || '流式请求失败');
        setLoading(false);
    }
}

/** SSE 事件分发 */
function handleStreamEvent(event) {
    const step = event.step;
    const div = resultContent;

    if (event.type === 'step_start') {
        const html = `
            <div class="full-step processing" id="step-${step}" data-step="${step}">
                <div class="full-step-header">
                    <span class="full-step-icon">${event.icon}</span>
                    <span class="full-step-name">${esc(event.name)}</span>
                    <span class="full-step-badge pending">处理中</span>
                </div>
                <div class="full-step-loading">
                    <div class="processing-dot">
                        <span></span><span></span><span></span>
                        正在分析...
                    </div>
                </div>
            </div>`;
        const el = document.getElementById('step-' + step);
        if (el) el.outerHTML = html;
        else div.insertAdjacentHTML('beforeend', html);
    } else if (event.type === 'step_end') {
        const el = document.getElementById('step-' + step);
        if (!el) return;

        if (event.success) {
            el.className = 'full-step success';
            el.setAttribute('data-step', step);
            el.querySelector('.full-step-badge').className =
                'full-step-badge success';
            el.querySelector('.full-step-badge').textContent = '完成';
            // 渲染内容：自由文本或结构化 JSON
            let contentHtml = '';
            const d = event.data;
            if (d && typeof d === 'object') {
                if (d.json) {
                    // step 6: 用解析后的 JSON 对象渲染
                    contentHtml = renderAgentJson(d.json);
                } else if (d.text) {
                    contentHtml = `<div class="result-text" style="white-space:pre-wrap;line-height:1.8;font-size:13px;">${renderMarkdown(d.text)}</div>`;
                }
            }
            const loading = el.querySelector('.full-step-loading');
            if (loading) {
                const openAttr = step === 6 ? ' open' : '';
                const summaryText = step === 6 ? '📋 查看结果 ▾' : '展开查看 ▸';
                loading.outerHTML =
                    `<details class="full-step-details"${openAttr}><summary class="full-step-summary">${summaryText}</summary><div class="full-step-content">${contentHtml}</div></details>`;
            }
        } else {
            el.className = 'full-step error';
            el.setAttribute('data-step', step);
            el.querySelector('.full-step-badge').className =
                'full-step-badge error';
            el.querySelector('.full-step-badge').textContent = '失败';
            el.querySelector('.full-step-loading').outerHTML =
                '<div class="full-step-error"> ⚠ ' +
                esc(event.error || '未知错误') +
                '</div>';
        }
    } else if (event.type === 'complete') {
        const summaryHtml = `
            <div class="full-summary">
                <div class="full-summary-text">全流程分析完成</div>
                <div class="full-summary-count">
                    <span>成功 <span class="count-success">${event.success}</span>/${event.total}</span>
                    ${
                        event.success < event.total
                            ? '<span>失败 <span class="count-error">' +
                              (event.total - event.success) +
                              '</span></span>'
                            : ''
                    }
                </div>
            </div>`;
        div.insertAdjacentHTML('afterbegin', summaryHtml);
        loadHistory();
    }
}

/** 渲染单步结果 */
function renderStepContent(step, data) {
    if (!data) return '';
    // Agent 6: 用 json 字段渲染
    if (data.json) return renderAgentJson(data.json);
    // Agent 1-5: 自由文本（用 hasOwnProperty 而非 truthy 检查，避免空字符串被跳过进入旧 renderAnalyze）
    if (Object.prototype.hasOwnProperty.call(data, 'text')) {
        return `<div class="result-text" style="white-space:pre-wrap;line-height:1.8;">${renderMarkdown(data.text)}</div>`;
    }
    // Agent 6 / 旧格式：直接传入解析后的结构化对象
    if (data.title !== undefined || data.positioning !== undefined) {
        return renderAgentJson(data);
    }
    // 兼容旧 4 步格式（无 text 包装的原始结构化数据）
    switch (step) {
        case 1: return renderAnalyze(data);
        case 2: return renderTitle(data);
        case 3: return renderContent(data);
        case 4: return renderStrategy(data);
        default: return `<div class="result-text">${esc(JSON.stringify(data, null, 2))}</div>`;
    }
}

/** 渲染 Agent 6 的 JSON 输出
 *
 *  新 Schema 优先；旧 Schema 兼容降级。
 *  检测规则：新 Schema 的 xiaohongshu 是对象（含 titles/note/tags），旧的是数组。
 */
function renderAgentJson(data) {
    if (!data) return '';

    // 新 Schema：xiaohongshu 为对象
    if (data.xiaohongshu && typeof data.xiaohongshu === 'object' && !Array.isArray(data.xiaohongshu)) {
        return renderNewSchema(data);
    }
    // 旧 Schema 兼容
    return renderOldSchema(data);
}

// ===================== 新 Schema 渲染 =====================

function renderNewSchema(data) {
    let html = '';

    // 洞察区域
    if (data.user_profile || data.pain_points || data.usage_scenarios) {
        html += '<details class="module-details" open>';
        html += '<summary class="module-summary">🔍 商品洞察</summary>';
        html += '<div class="module-body">';
        if (data.user_profile) {
            html += '<div class="module-field"><span class="field-label">用户画像</span><div class="field-value">' + esc(data.user_profile) + '</div></div>';
        }
        if (data.pain_points?.length) {
            html += '<div class="module-field"><span class="field-label">消费痛点</span><ul class="result-list">' + data.pain_points.map(p => '<li>' + esc(p) + '</li>').join('') + '</ul></div>';
        }
        if (data.purchase_motivation) {
            html += '<div class="module-field"><span class="field-label">购买动机</span><div class="field-value">' + esc(data.purchase_motivation) + '</div></div>';
        }
        if (data.usage_scenarios?.length) {
            html += '<div class="module-field"><span class="field-label">使用场景</span><ul class="result-list">' + data.usage_scenarios.map(s => '<li>' + esc(s) + '</li>').join('') + '</ul></div>';
        }
        html += '</div></details>';
    }

    // 增长策略
    if (data.core_positioning || data.recommended_channels || data.purchase_reason) {
        html += '<details class="module-details" open>';
        html += '<summary class="module-summary">📈 增长策略</summary>';
        html += '<div class="module-body">';
        if (data.core_positioning) {
            html += '<div class="module-field"><span class="field-label">核心定位</span><div class="field-value">' + esc(data.core_positioning) + '</div></div>';
        }
        if (data.recommended_channels?.length) {
            html += '<div class="module-field"><span class="field-label">推荐渠道</span><div class="field-value">' + data.recommended_channels.map(c => '<span class="tag">' + esc(c) + '</span>').join(' ') + '</div></div>';
        }
        if (data.marketing_angle) {
            html += '<div class="module-field"><span class="field-label">营销角度</span><div class="field-value">' + esc(data.marketing_angle) + '</div></div>';
        }
        if (data.purchase_reason) {
            html += '<div class="module-field"><span class="field-label">🎯 为什么现在买</span><div class="field-value purchase-reason">' + esc(data.purchase_reason) + '</div></div>';
        }
        html += '</div></details>';
    }

    // 小红书模块
    if (data.xiaohongshu && typeof data.xiaohongshu === 'object') {
        html += renderXiaohongshuSection(data.xiaohongshu);
    }

    // 抖音模块
    if (data.douyin && typeof data.douyin === 'object') {
        html += renderDouyinSection(data.douyin);
    }

    // 详情页模块
    if (data.detail_page && typeof data.detail_page === 'object') {
        html += renderDetailPageSection(data.detail_page);
    }

    // 发布节奏
    if (data.publish_rhythm) {
        html += '<details class="module-details">';
        html += '<summary class="module-summary">📅 发布节奏</summary>';
        html += '<div class="module-body"><div class="field-value">' + esc(data.publish_rhythm) + '</div></div></details>';
    }

    return html || ('<div class="result-text">' + esc(JSON.stringify(data)) + '</div>');
}

/** 小红书模块 */
function renderXiaohongshuSection(xhs) {
    let html = '<details class="module-details" open>';
    html += '<summary class="module-summary">📕 小红书运营方案</summary>';
    html += '<div class="module-body">';

    // 标题
    if (xhs.titles?.length) {
        html += '<div class="module-field"><span class="field-label">爆款标题（5个）</span>';
        html += '<ol class="xhs-title-list">' + xhs.titles.map(t => '<li>' + esc(t) + '</li>').join('') + '</ol></div>';
    }

    // 封面文案
    if (xhs.cover_texts?.length) {
        html += '<div class="module-field"><span class="field-label">封面文案</span>';
        html += '<div class="cover-text-list">' + xhs.cover_texts.map(t => '<span class="cover-text-item">' + esc(t) + '</span>').join('') + '</div></div>';
    }

    // 笔记正文
    if (xhs.note && typeof xhs.note === 'object') {
        html += '<div class="module-field"><span class="field-label">种草笔记</span>';
        html += '<div class="xhs-note">';
        if (xhs.note.hook) {
            html += '<div class="note-hook"><span class="note-label">📌 开头</span>' + esc(xhs.note.hook) + '</div>';
        }
        if (xhs.note.body_sections?.length) {
            html += '<div class="note-body">' + xhs.note.body_sections.map((s, i) => '<p class="note-para">' + esc(s) + '</p>').join('') + '</div>';
        }
        if (xhs.note.ending) {
            html += '<div class="note-ending"><span class="note-label">💬 结尾</span>' + esc(xhs.note.ending) + '</div>';
        }
        html += '</div></div>';
    } else if (xhs.note && typeof xhs.note === 'string') {
        // 兼容旧格式：note 是单个字符串
        html += '<div class="module-field"><span class="field-label">种草笔记</span><div class="field-value">' + esc(xhs.note) + '</div></div>';
    }

    // 标签
    if (xhs.tags?.length) {
        html += '<div class="module-field"><span class="field-label">话题标签</span>';
        html += '<div class="tag-list">' + xhs.tags.map(t => '<span class="tag">#' + esc(t) + '</span>').join('') + '</div></div>';
    }

    html += '</div></details>';
    return html;
}

/** 抖音模块 */
function renderDouyinSection(douyin) {
    let html = '<details class="module-details" open>';
    html += '<summary class="module-summary">🎬 抖音运营方案</summary>';
    html += '<div class="module-body">';

    if (douyin.video_direction) {
        html += '<div class="module-field"><span class="field-label">视频方向</span><div class="field-value direction-tag">' + esc(douyin.video_direction) + '</div></div>';
    }

    if (douyin.hook) {
        html += '<div class="module-field"><span class="field-label">⚡ 3秒开场钩子</span><div class="field-value hook-text">' + esc(douyin.hook) + '</div></div>';
    }

    // 分镜脚本
    if (douyin.script?.length) {
        html += '<div class="module-field"><span class="field-label">分镜脚本</span>';
        html += '<div class="script-timeline">';
        douyin.script.forEach((seg, i) => {
            html += '<div class="script-shot">';
            html += '<div class="shot-header"><span class="shot-time">' + esc(seg.time || '') + '</span>';
            if (seg.shot_type) {
                html += '<span class="shot-type">' + esc(seg.shot_type) + '</span>';
            }
            html += '</div>';
            html += '<div class="shot-body">';
            if (seg.visual) html += '<div class="shot-line"><span class="shot-label">画面</span>' + esc(seg.visual) + '</div>';
            if (seg.narration) html += '<div class="shot-line"><span class="shot-label">旁白</span>' + esc(seg.narration) + '</div>';
            if (seg.subtitle) html += '<div class="shot-line"><span class="shot-label">字幕</span>' + esc(seg.subtitle) + '</div>';
            html += '</div></div>';
        });
        html += '</div></div>';
    }

    // 拍摄建议
    if (douyin.shooting_tips && typeof douyin.shooting_tips === 'object') {
        const tips = douyin.shooting_tips;
        html += '<div class="module-field"><span class="field-label">🎥 拍摄建议</span>';
        html += '<div class="shooting-tips">';
        if (tips.scene) html += '<div class="tip-row"><span>场景</span>' + esc(tips.scene) + '</div>';
        if (tips.camera) html += '<div class="tip-row"><span>镜头</span>' + esc(tips.camera) + '</div>';
        if (tips.props) html += '<div class="tip-row"><span>道具</span>' + esc(tips.props) + '</div>';
        if (tips.pace) html += '<div class="tip-row"><span>节奏</span>' + esc(tips.pace) + '</div>';
        html += '</div></div>';
    }

    // 转化话术
    if (douyin.conversion_script) {
        html += '<div class="module-field"><span class="field-label">💰 转化话术</span><div class="field-value conversion-text">' + esc(douyin.conversion_script) + '</div></div>';
    }

    html += '</div></details>';
    return html;
}

/** 商品详情页模块 */
function renderDetailPageSection(dp) {
    let html = '<details class="module-details">';
    html += '<summary class="module-summary">🛒 商品详情页素材</summary>';
    html += '<div class="module-body">';

    if (dp.main_title) {
        html += '<div class="module-field"><span class="field-label">主标题</span><div class="field-value" style="font-size:16px;font-weight:700;">' + esc(dp.main_title) + '</div></div>';
    }

    if (dp.selling_points_ranked?.length) {
        html += '<div class="module-field"><span class="field-label">核心卖点排序</span><ol class="sp-ranked-list">' + dp.selling_points_ranked.map((sp, i) => '<li><span class="sp-rank">' + (i + 1) + '</span>' + esc(sp) + '</li>').join('') + '</ol></div>';
    }

    if (dp.five_point_descriptions?.length) {
        html += '<div class="module-field"><span class="field-label">五点描述</span><ul class="five-point-list">' + dp.five_point_descriptions.map(p => '<li>' + esc(p) + '</li>').join('') + '</ul></div>';
    }

    if (dp.main_image_copy) {
        html += '<div class="module-field"><span class="field-label">主图卖点文案</span><div class="field-value image-copy">' + esc(dp.main_image_copy) + '</div></div>';
    }

    html += '</div></details>';
    return html;
}

// ===================== 旧 Schema 兼容渲染 =====================

/** 旧 Schema 降级渲染（保留完整兼容） */
function renderOldSchema(data) {
    let html = '';
    if (data.title) {
        html += '<div class="result-section"><div class="result-section-title">📌 方案标题</div><div class="result-text" style="font-size:16px;font-weight:700;">' + esc(data.title) + '</div></div>';
    }
    if (data.positioning) {
        html += '<div class="result-section"><div class="result-section-title">🎯 商品定位</div><div class="result-text">' + renderMarkdown(data.positioning) + '</div></div>';
    }
    if (data.user_profile) {
        html += '<div class="result-section"><div class="result-section-title">👤 用户画像</div><div class="result-text">' + renderMarkdown(data.user_profile) + '</div></div>';
    }
    if (data.selling_points?.length) {
        html += '<div class="result-section"><div class="result-section-title">⭐ 核心卖点</div>';
        data.selling_points.forEach(sp => {
            html += '<div class="title-optimize-item"><div class="optimized-title">' + esc(sp.feature || '') + '</div><div class="optimize-reason">用户价值：' + esc(sp.value || '') + '</div></div>';
        });
        html += '</div>';
    }
    if (data.xiaohongshu_titles?.length) {
        html += '<div class="result-section"><div class="result-section-title">📕 小红书标题</div><ul class="result-list">' + data.xiaohongshu_titles.map(t => '<li>' + esc(t) + '</li>').join('') + '</ul></div>';
    }
    if (data.video_topics?.length) {
        html += '<div class="result-section"><div class="result-section-title">🎬 短视频选题</div><ul class="result-list">' + data.video_topics.map(t => '<li>' + esc(t) + '</li>').join('') + '</ul></div>';
    }
    if (data.promotion_strategy) {
        html += '<div class="result-section" style="margin-bottom:0;"><div class="result-section-title">🚀 推广策略</div><div class="result-text">' + renderMarkdown(data.promotion_strategy) + '</div></div>';
    }
    return html || ('<div class="result-text">' + esc(JSON.stringify(data)) + '</div>');
}

// ===================== 各步骤渲染 =====================

function renderAnalyze(data) {
    let html = `
        <div class="result-section">
            <div class="result-section-title">🎯 商品定位</div>
            <div class="result-text">
                <strong>目标用户：</strong>${esc(data.positioning?.target_users || '')}<br>
                <strong>消费场景：</strong>${esc(data.positioning?.scenario || '')}
            </div>
        </div>
        <div class="result-section">
            <div class="result-section-title">💡 用户痛点</div>
            <ul class="result-list">
                ${(data.pain_points || []).map((p) => `<li>${esc(p)}</li>`).join('')}
            </ul>
        </div>
        <div class="result-section" style="margin-bottom:0;">
            <div class="result-section-title">⭐ 核心卖点</div>
            <div>
                ${(data.selling_points || [])
                    .sort((a, b) => a.rank - b.rank)
                    .map(
                        (p) =>
                            `<span class="selling-point"><span class="point-rank">${p.rank}</span>${esc(p.point)}</span>`
                    )
                    .join('')}
            </div>
        </div>`;
    html += renderReasoning(data.reasoning);
    return html;
}

function renderTitle(data) {
    let html = `
        <div class="result-section" style="margin-bottom:0;">
            ${(data.optimized_titles || [])
                .map(
                    (t) =>
                        `<div class="title-optimize-item"><div class="optimized-title">${esc(t.title)}</div><div class="optimize-reason">${esc(t.reason)}</div></div>`
                )
                .join('')}
        </div>`;
    html += renderReasoning(data.reasoning);
    return html;
}

function renderContent(data) {
    const versions = data.versions || [];
    let html = '';
    if (versions.length > 0) {
        html +=
            '<div class="result-section" style="margin-bottom:0;"><div class="result-section-title">📝 内容版本（3个角度）</div>';
        html += '<div class="version-grid">';
        versions.forEach((v) => {
            let dimColors = ['version-score conversion', 'version-score memory', 'version-score real'];
            let dimLabels = ['转化力', '记忆点', '真实感'];
            let dimKeys = ['转化力', '记忆点', '真实感'];
            let scoresHtml = '';
            dimKeys.forEach((k, i) => {
                scoresHtml += `<span class="${dimColors[i]}">${k} ${v.scores?.[k] || '?'}</span>`;
            });
            html += `
                <div class="version-card">
                    <div class="version-header">
                        <span class="version-angle">${esc(v.angle || '')}</span>
                        <div class="version-scores">${scoresHtml}</div>
                    </div>
                    <div class="version-content-wrap">
                        <div class="content-block" style="font-size:13px;font-weight:600;">${esc(v.title || '')}</div>
                        <div class="content-block" style="font-size:12px;">${esc(v.content || '')}</div>
                        ${v.tags ? '<div class="tag-list">' + v.tags.map((t) => `<span class="tag">${esc(t)}</span>`).join('') + '</div>' : ''}
                    </div>
                </div>`;
        });
        html += '</div></div>';
    } else {
        // fallback for old format
        html = `
            <div style="margin-bottom:8px;">
                <span style="font-size:12px;color:var(--text-secondary);">标题</span>
                <div class="content-block" style="font-size:15px;font-weight:600;">${esc(data.title || '')}</div>
            </div>
            <div style="margin-bottom:8px;">
                <span style="font-size:12px;color:var(--text-secondary);">正文</span>
                <div class="content-block">${esc(data.content || '')}</div>
            </div>
            <div style="margin-bottom:0;">
                <span style="font-size:12px;color:var(--text-secondary);">标签</span>
                <div class="tag-list" style="margin-top:6px;">
                    ${(data.tags || []).map((t) => `<span class="tag">${esc(t)}</span>`).join('')}
                </div>
            </div>`;
    }
    html += renderReasoning(data.reasoning);
    return html;
}

function renderStrategy(data) {
    let html = `
        <div class="result-section">
            <div class="result-section-title">👤 推荐目标用户</div>
            <div class="result-text">${esc(data.target_users || '')}</div>
        </div>
        <div class="result-section">
            <div class="result-section-title">📝 内容方向</div>
            ${(data.content_directions || [])
                .map(
                    (d) =>
                        `<div class="title-optimize-item"><div class="optimized-title">${esc(d.title)}</div><div class="optimize-reason">${esc(d.description)}</div></div>`
                )
                .join('')}
        </div>
        <div class="result-section" style="margin-bottom:0;">
            <div class="result-section-title">📊 平台运营建议</div>
            ${(data.platform_suggestions || [])
                .map(
                    (p) =>
                        `<div class="platform-card"><span class="platform-name">${esc(p.platform)}</span><span class="platform-desc">${esc(p.strategy)}</span></div>`
                )
                .join('')}
        </div>`;
    html += renderReasoning(data.reasoning);
    return html;
}

/** 渲染推理链条 */
function renderReasoning(reasoning) {
    if (!reasoning || !reasoning.chain) return '';
    return `
        <div class="reasoning-block">
            <div class="reasoning-label">🧠 推理过程</div>
            <span class="reasoning-text">${esc(reasoning.chain)}</span>
        </div>`;
}

// ===================== 历史记录 =====================

const historyList = $('#historyList');

async function loadHistory() {
    try {
        const resp = await fetch(API_BASE + '/history');
        const data = await resp.json();
        renderHistory(data.history || []);
    } catch (_) {
        renderHistory([]);
    }
}

function renderHistory(history) {
    if (!historyList) return;
    if (!history.length) {
        historyList.innerHTML = '<p class="history-empty">暂无记录</p>';
        return;
    }

    const typeLabels = { full: '📋', visual: '🎨', onboarding: '📦' };

    historyList.innerHTML = history
        .map(
            (h, i) => `
        <div class="history-item" data-idx="${i}">
            <button class="history-item-del" data-idx="${i}" title="删除此条">✕</button>
            <span class="history-item-title">${typeLabels[h.type] || '📋'} ${esc(h.product_name || '')}</span>
            <span class="history-item-time">${esc(h.timestamp || '')}</span>
            <span class="history-item-summary">${esc(h.summary || '')}</span>
        </div>`
        )
        .join('');

    // 单个删除
    $$('.history-item-del').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const idx = parseInt(btn.dataset.idx);
            await fetch(API_BASE + '/history?index=' + idx, { method: 'DELETE' });
            loadHistory();
        });
    });

    // 点击加载历史结果
    $$('.history-item').forEach((item) => {
        item.addEventListener('click', () => {
            const idx = parseInt(item.dataset.idx);
            const entry = history[idx];
            if (!entry) return;
            resultContent.innerHTML = '';
            resultCard.style.display = 'block';

            // 关闭按钮
            const closeBtn =
                '<button class="history-close-btn" onclick="closeHistoryDetail()" title="关闭">✕</button>';

            if (entry.type === 'full' && entry.steps) {
                resultContent.insertAdjacentHTML(
                    'afterbegin',
                    `<div class="full-summary"><div class="full-summary-text">${esc(entry.product_name)} · ${esc(entry.timestamp)}${closeBtn}</div><div class="full-summary-count"><span>${esc(entry.summary)}</span></div></div>`
                );
                entry.steps.forEach((s) => {
                    const stepHtml = `
                    <div class="full-step ${s.success ? 'success' : 'error'}" data-step="${s.step}">
                        <div class="full-step-header">
                            <span class="full-step-icon">${s.icon}</span>
                            <span class="full-step-name">${esc(s.name)}</span>
                            <span class="full-step-badge ${s.success ? 'success' : 'error'}">${s.success ? '完成' : '失败'}</span>
                        </div>
                        ${s.success ? '<div>' + renderStepContent(s.step, s.data) + '</div>' : '<div class="full-step-error">⚠ ' + esc(s.error || '未知错误') + '</div>'}
                    </div>`;
                    resultContent.insertAdjacentHTML('beforeend', stepHtml);
                });
            } else if (entry.type === 'visual') {
                resultContent.insertAdjacentHTML(
                    'afterbegin',
                    `<div class="full-summary"><div class="full-summary-text">${esc(entry.product_name)} · ${esc(entry.timestamp)}${closeBtn}</div><div class="full-summary-count"><span>${esc(entry.summary)}</span></div></div>`
                );
                // 渲染视觉分析摘要 + Prompt 卡片
                const a = entry.visual_analysis || {};
                let html = `<div class="visual-analysis-card">
                    <div class="report-block-label">📷 视觉分析结果</div>
                    <div class="report-block-content">
                        <strong>类别：</strong>${esc(a.category || '')}<br>
                        <strong>颜色：</strong>${esc(a.color || '')}<br>
                        <strong>材质：</strong>${esc(a.material || '')}<br>
                        <strong>质感：</strong>${esc(a.texture || '')}
                    </div>
                </div>`;
                (entry.prompts || []).forEach((p, i) => {
                    html += `<div class="prompt-card"><div class="prompt-card-header">
                        <span class="prompt-card-scene">${esc(p.scene)}</span>
                    </div><div class="prompt-card-body">
                        <div class="prompt-text">${esc(p.prompt)}</div>
                        <button class="btn-copy" onclick="copyPromptText(this, '${esc(p.prompt)}')">📋 复制</button>
                    </div></div>`;
                });
                resultContent.insertAdjacentHTML('beforeend', html);
            } else if (entry.type === 'onboarding') {
                resultContent.insertAdjacentHTML(
                    'afterbegin',
                    `<div class="full-summary"><div class="full-summary-text">${esc(entry.product_name)} · ${esc(entry.timestamp)}${closeBtn}</div></div>`
                );
                const reports = entry.reports || [];
                if (typeof renderOnboardingReports === 'function') {
                    const wrapper = document.createElement('div');
                    wrapper.innerHTML = '';
                    resultContent.appendChild(wrapper);
                    renderOnboardingReports(reports, wrapper);
                } else {
                    reports.forEach((r) => {
                        resultContent.insertAdjacentHTML('beforeend',
                            `<div class="report-card"><div class="report-card-header"><h3>${esc(r.product_name)}</h3></div>
                            <p>${esc(r.positioning || '')}</p></div>`);
                    });
                }
            }
            resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });
}

function closeHistoryDetail() {
    resultCard.style.display = 'none';
}

function copyPromptText(btn, text) {
    navigator.clipboard.writeText(text).then(() => {
        btn.textContent = '✅ 已复制';
        setTimeout(() => { btn.textContent = '📋 复制'; }, 2000);
    });
}

// 清空全部历史
$('#clearHistoryBtn')?.addEventListener('click', async () => {
    if (!confirm('确定清空全部历史记录？')) return;
    await fetch(API_BASE + '/history', { method: 'DELETE' });
    loadHistory();
});

// 初始加载历史
loadHistory();

// ===================== 商品 Excel 上传 =====================

const uploadBtn = $('#uploadBtn');
const uploadModal = $('#uploadModal');
const modalClose = $('#modalClose');
const fileInput = $('#fileInput');
const uploadZone = $('#uploadZone');
const fileHint = $('#fileHint');
const analyzeUploadBtn = $('#analyzeUploadBtn');
const uploadStatus = $('#uploadStatus');
const onboardingResults = $('#onboardingResults');
const onboardingContent = $('#onboardingContent');
const onboardingCount = $('#onboardingCount');

let uploadedProducts = [];

// 打开/关闭弹层
uploadBtn.addEventListener('click', () => {
    uploadModal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
});

modalClose.addEventListener('click', closeModal);
uploadModal.addEventListener('click', (e) => {
    if (e.target === uploadModal) closeModal();
});

function closeModal() {
    uploadModal.style.display = 'none';
    document.body.style.overflow = '';
    uploadStatus.style.display = 'none';
    analyzeUploadBtn.disabled = true;
    fileInput.value = '';
    fileHint.textContent = '未选择文件';
    uploadedProducts = [];
}

// 拖拽上传
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});
uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
});
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect(e.dataTransfer.files[0]);
    }
});

uploadZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
    if (fileInput.files.length) handleFileSelect(fileInput.files[0]);
});

function handleFileSelect(file) {
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls') && !file.name.endsWith('.csv')) {
        fileHint.textContent = '❌ 仅支持 .xlsx / .xls / .csv 格式';
        analyzeUploadBtn.disabled = true;
        return;
    }
    fileHint.textContent = '已选择: ' + file.name;
    analyzeUploadBtn.disabled = false;
}

// 上传并分析
analyzeUploadBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    uploadStatus.style.display = 'block';
    uploadStatus.className = 'upload-status loading';
    uploadStatus.textContent = '⏳ 上传中...';
    analyzeUploadBtn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('file', file);
        const resp = await fetch(API_BASE + '/upload-products', {
            method: 'POST',
            body: formData,
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || '上传失败');
        }
        const data = await resp.json();
        uploadedProducts = data.products;

        uploadStatus.textContent =
            '✅ 解析成功！共 ' + data.count + ' 件商品，正在生成运营报告...';

        // 调用上新分析
        const anaResp = await fetch(API_BASE + '/product-onboarding', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ products: uploadedProducts }),
        });
        if (!anaResp.ok) {
            const err = await anaResp.json();
            throw new Error(err.detail || '分析失败');
        }
        const anaData = await anaResp.json();

        uploadStatus.textContent =
            '✅ 完成！共生成 ' + anaData.reports.length + ' 件商品的运营报告';
        uploadStatus.className = 'upload-status success';

        renderOnboardingReports(anaData.reports);
        closeModal();
        onboardingResults.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (err) {
        uploadStatus.textContent = '❌ ' + err.message;
        uploadStatus.className = 'upload-status error';
        analyzeUploadBtn.disabled = false;
    }
});

// 下载模板
$('#downloadTemplate')?.addEventListener('click', () => {
    const csv =
        '商品名称,价格,分类,商品描述,规格参数,卖点\n无线降噪耳机,299,数码配件,适合学生和上班族,蓝牙5.3 40小时续航 Type-C充电,主动降噪 超长续航 轻量舒适\n滋润护手霜,59,美妆个护,办公室护手霜,乳木果油 30ml随身装,快速吸收 不油腻 便携\n';
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '商品上新模板.csv';
    a.click();
});

// ===================== 商品运营报告渲染 =====================

function renderOnboardingReports(reports) {
    onboardingContent.innerHTML = '';
    onboardingCount.textContent = reports.length + ' 件商品';
    onboardingResults.style.display = 'block';

    reports.forEach((r, idx) => {
        let html = `
<div class="report-card">
    <div class="report-card-header">
        <div class="report-product-icon">📦</div>
        <div class="report-product-info">
            <h3>${esc(r.product_name)}</h3>
            <span class="report-meta">报告 #${idx + 1}</span>
        </div>
    </div>
    <div class="report-grid">
        <div class="report-block">
            <div class="report-block-label">🎯 商品定位</div>
            <div class="report-block-content">${esc(r.positioning)}</div>
        </div>
        <div class="report-block">
            <div class="report-block-label">👤 目标用户</div>
            <div class="report-block-content">${esc(r.target_users)}</div>
        </div>
        <div class="report-block">
            <div class="report-block-label">💡 消费痛点</div>
            <div class="report-block-content">
                ${(r.pain_points || []).map((p) => '<span style="display:block;padding:2px 0;">• ' + esc(p) + '</span>').join('')}
            </div>
        </div>
        <div class="report-block">
            <div class="report-block-label">⭐ 核心卖点</div>
            <div class="report-block-content">
                ${(r.selling_points || []).map((p) => '<span style="display:block;padding:2px 0;">• ' + esc(p) + '</span>').join('')}
            </div>
        </div>
        <div class="report-block full">
            <div class="report-block-label">🔍 搜索关键词</div>
            <div class="report-keyword-list">
                ${(r.search_keywords || []).map((k) => '<span class="report-keyword">' + esc(k) + '</span>').join('')}
            </div>
        </div>
        <div class="report-block full">
            <div class="report-block-label">✏️ 电商标题方案</div>
            <ul class="report-title-list">
                ${(r.ecommerce_titles || []).map((t) => '<li>' + esc(t) + '</li>').join('')}
            </ul>
        </div>
        <div class="report-block full">
            <div class="report-block-label">📋 详情页结构建议</div>
            <div class="report-block-content">${esc(r.detail_page_structure)}</div>
        </div>
        <div class="report-block full">
            <div class="report-block-label">📕 小红书内容建议</div>
            <div class="report-xhs">${esc(r.xiaohongshu_content)}</div>
        </div>
    </div>
</div>`;
        onboardingContent.insertAdjacentHTML('beforeend', html);
    });
}

// ===================== AI 商品视觉策划 =====================

const visualUploadZone = $('#visualUploadZone');
const visualFileInput = $('#visualFileInput');
const visualPreviews = $('#visualPreviews');
const visualProductName = $('#visualProductName');
const visualAnalyzeBtn = $('#visualAnalyzeBtn');
const visualResults = $('#visualResults');

let visualFiles = [];

// 图片选择
visualUploadZone.addEventListener('click', () => visualFileInput.click());
visualFileInput.addEventListener('change', () => {
    visualFiles = Array.from(visualFileInput.files);
    if (visualFiles.length > 3) {
        visualFiles = visualFiles.slice(0, 3);
        showError('最多上传 3 张图片，已自动选取前 3 张');
    }
    renderVisualPreviews();
    visualAnalyzeBtn.disabled = visualFiles.length === 0;
});

function renderVisualPreviews() {
    visualPreviews.innerHTML = '';
    visualFiles.forEach((f, i) => {
        const url = URL.createObjectURL(f);
        const img = document.createElement('img');
        img.src = url;
        img.className = 'visual-preview-item';
        img.title = f.name;
        visualPreviews.appendChild(img);
    });
}

// 分析
visualAnalyzeBtn.addEventListener('click', async () => {
    if (!visualFiles.length) return;

    visualAnalyzeBtn.disabled = true;
    visualAnalyzeBtn.textContent = '分析中...';
    visualResults.style.display = 'none';
    hideError();

    try {
        const formData = new FormData();
        visualFiles.forEach((f) => formData.append('images', f));
        formData.append('product_name', visualProductName.value.trim());

        const resp = await fetch(API_BASE + '/visual-analysis', {
            method: 'POST',
            body: formData,
        });
        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || '请求失败');
        }
        const data = await resp.json();
        renderVisualResults(data);
        visualResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
        showError('视觉分析失败: ' + err.message);
    } finally {
        visualAnalyzeBtn.disabled = false;
        visualAnalyzeBtn.textContent = '开始视觉分析';
    }
});

function renderVisualResults(data) {
    const a = data.visual_analysis;
    let html = '';

    // 视觉分析摘要
    html += `<div class="visual-analysis-card">
        <div class="report-block-label">📷 视觉分析结果</div>
        <div class="report-block-content">
            <strong>类别：</strong>${esc(a.category)}<br>
            <strong>颜色：</strong>${esc(a.color)}<br>
            <strong>材质：</strong>${esc(a.material)}<br>
            <strong>质感：</strong>${esc(a.texture)}<br>
            <strong>形态：</strong>${esc(a.shape_features)}<br>
            <strong>视觉卖点：</strong>${esc(a.selling_point_visual)}<br>
            <strong>目标用户：</strong>${esc(a.target_users)}
        </div>
    </div>`;

    // 一致性约束
    if (data.consistency_constraint) {
        html += `<div class="visual-analysis-card" style="border-left:3px solid var(--warm);background:var(--warm-light);">
            <div class="report-block-label">🔒 商品一致性约束</div>
            <div class="report-block-content">${esc(data.consistency_constraint)}</div>
        </div>`;
    }

    // Prompt 卡片
    html += '<div class="prompt-cards">';
    data.prompts.forEach((p, i) => {
        html += `<div class="prompt-card">
            <div class="prompt-card-header">
                <span class="prompt-card-scene">${esc(p.scene)}</span>
                <span class="prompt-card-goal">${esc(p.marketing_goal)}</span>
            </div>
            <div class="prompt-card-body">
                <div class="prompt-label">用途：${esc(p.purpose)}</div>
                <div class="prompt-label" style="margin-top:8px;">正向 Prompt</div>
                <div class="prompt-text" id="prompt-${i}">${esc(p.prompt)}</div>
                <div class="prompt-label">负向 Prompt</div>
                <div class="prompt-text" id="neg-${i}" style="max-height:100px;">${esc(p.negative_prompt)}</div>
                <div class="prompt-label" style="margin-top:6px;">⚠ 一致性要点：${esc(p.consistency_note)}</div>
                <div class="prompt-card-actions">
                    <button class="btn-copy" onclick="copyPrompt('prompt-${i}', this)">📋 复制正向 Prompt</button>
                    <button class="btn-copy" onclick="copyPrompt('neg-${i}', this)">📋 复制负向 Prompt</button>
                </div>
            </div>
        </div>`;
    });
    html += '</div>';

    visualResults.innerHTML = html;
    visualResults.style.display = 'block';
}

function copyPrompt(divId, btn) {
    const el = document.getElementById(divId);
    if (!el) return;
    navigator.clipboard.writeText(el.textContent).then(() => {
        btn.classList.add('copied');
        btn.textContent = '✅ 已复制';
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.textContent = '📋 复制' + (divId.startsWith('neg') ? '负向' : '正向') + ' Prompt';
        }, 2000);
    }).catch(() => {
        // 兼容旧浏览器
        const ta = document.createElement('textarea');
        ta.value = el.textContent;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.classList.add('copied');
        btn.textContent = '✅ 已复制';
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.textContent = '📋 复制' + (divId.startsWith('neg') ? '负向' : '正向') + ' Prompt';
        }, 2000);
    });
}

// ===================== 工具 =====================

/** 轻量 Markdown → HTML，处理 **、###、---、- 列表 */
function renderMarkdown(text) {
    if (!text) return '';
    // 先处理 Markdown 符号（在 raw text 上操作），再对匹配的内容单独 esc()
    let html = text;
    // 水平线（独立行 ---）
    html = html.replace(/^---\s*$/gm, '<hr class="md-hr">');
    // 标题（行首 # / ## / ### / ####）
    html = html.replace(/^#### (.+)$/gm, (_, c) => `<h5 class="md-h5">${esc(c)}</h5>`);
    html = html.replace(/^### (.+)$/gm, (_, c) => `<h4 class="md-h4">${esc(c)}</h4>`);
    html = html.replace(/^## (.+)$/gm, (_, c) => `<h3 class="md-h3">${esc(c)}</h3>`);
    html = html.replace(/^# (.+)$/gm, (_, c) => `<h2 class="md-h2">${esc(c)}</h2>`);
    // 粗体 **text**
    html = html.replace(/\*\*(.+?)\*\*/g, (_, c) => `<strong>${esc(c)}</strong>`);
    // 无序列表（行首 - text → • text）
    html = html.replace(/^- (.+)$/gm, (_, c) => `<span class="md-li">• ${esc(c)}</span>`);
    // 段落：连续两个换行
    html = html.replace(/\n\n+/g, '<br><br>');
    return html;
}

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
