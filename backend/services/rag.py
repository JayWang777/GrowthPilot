"""RAG 检索服务

混合检索策略：语义向量（SentenceTransformer）+ 关键词加权。
使用 BGE-small-zh 中文 embedding 模型，首次使用自动下载缓存到 W 盘。

设计思路：
- 轻量级，不依赖 ChromaDB 等外部服务
- 预计算 + 缓存文档向量，运行时直接做余弦相似度
- 语义匹配为主（70%），关键词匹配为辅（30%），兼顾泛化与精准
"""

import os
import re
import hashlib
from pathlib import Path

import numpy as np

# 强制 HF 缓存到 W 盘（避免写 C 盘）
os.environ.setdefault("HF_HOME", "W:\\Claude\\cache\\huggingface")

# 知识库路径
KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"
# 向量缓存路径
CACHE_DIR = KNOWLEDGE_DIR / ".cache"


class KnowledgeDocument:
    """知识文档片段"""

    def __init__(self, content: str, source: str, section: str = ""):
        self.content = content
        self.source = source
        self.section = section


class RAGService:
    """混合检索 RAG 服务

    语义检索（embedding 余弦相似度）+ 关键词加权。
    """

    def __init__(self):
        self.documents: list[KnowledgeDocument] = []
        self._embeddings: np.ndarray | None = None  # shape: (n_docs, dim)
        self._model = None  # SentenceTransformer 延迟加载
        self._cache_key = ""  # 缓存有效性标记

        self._load_knowledge()

    # ===================== 知识加载 =====================

    def _load_knowledge(self):
        """加载知识库文件，按标题切分为片段"""
        if not KNOWLEDGE_DIR.exists():
            return

        for md_file in sorted(KNOWLEDGE_DIR.glob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            source = md_file.stem

            # 按二级标题 (## ) 切分章节
            sections = re.split(r"\n(?=## )", content)
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                title_match = re.match(r"##?\s+(.+)", section)
                section_title = title_match.group(1) if title_match else "概述"
                self.documents.append(
                    KnowledgeDocument(
                        content=section,
                        source=source,
                        section=section_title,
                    )
                )

        # 计算缓存 key（基于文件内容 hash）
        self._cache_key = self._compute_cache_key()

    def _compute_cache_key(self) -> str:
        """基于所有文档内容生成缓存标记"""
        combined = "".join(
            f"{d.source}:{d.section}:{d.content[:50]}" for d in self.documents
        )
        return hashlib.md5(combined.encode()).hexdigest()

    # ===================== 模型加载 =====================

    def _get_model(self):
        """延迟加载 embedding 模型（CPU only）"""
        if self._model is None:
            # 限制使用 CPU，避免 GPU VRAM 不足
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                "BAAI/bge-small-zh-v1.5",
                device="cpu",
            )
        return self._model

    # ===================== 向量计算 =====================

    def _ensure_embeddings(self):
        """确保文档向量已计算，优先加载缓存"""
        if self._embeddings is not None:
            return

        cache_file = CACHE_DIR / f"{self._cache_key}.npy"
        meta_file = CACHE_DIR / f"{self._cache_key}.meta"

        if cache_file.exists() and meta_file.exists():
            self._embeddings = np.load(str(cache_file))
            return

        # 计算向量
        model = self._get_model()
        texts = [d.content for d in self.documents]
        self._embeddings = model.encode(
            texts,
            normalize_embeddings=True,  # L2 归一化，方便点积算相似度
            show_progress_bar=False,
        )

        # 缓存到磁盘
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.save(str(cache_file), self._embeddings)
        # 写入元数据标记
        meta_file.write_text(f"docs={len(self.documents)}\nkey={self._cache_key}")

    def _invalidate_cache(self):
        """清理过期缓存"""
        if CACHE_DIR.exists():
            for f in CACHE_DIR.iterdir():
                if f.suffix == ".npy" or f.suffix == ".meta":
                    f.unlink()

    # ===================== 检索 =====================

    def _keyword_score(self, text: str, query: str) -> int:
        """计算文本与查询的关键词匹配得分"""
        text_lower = text.lower()
        query_lower = query.lower()
        keywords = set(re.findall(r"[\w一-鿿]+", query_lower))
        if not keywords:
            return 0
        # 标题匹配权重更高
        return sum(2 if kw in text_lower else 0 for kw in keywords)

    def search(self, query: str, top_k: int = 2) -> str:
        """混合检索：语义相似度（70%）+ 关键词匹配（30%）

        Args:
            query: 检索查询
            top_k: 返回最相关的前 k 个片段

        Returns:
            格式化的上下文文本（直接注入 Prompt）
        """
        if not self.documents:
            return ""

        self._ensure_embeddings()

        # 1. 语义检索：余弦相似度
        model = self._get_model()
        q_vec = model.encode(query, normalize_embeddings=True)
        semantic_scores = np.dot(self._embeddings, q_vec)  # 已归一化，点积 = 余弦

        # 2. 关键词加权
        keyword_scores = np.array(
            [self._keyword_score(d.content + d.section, query) for d in self.documents],
            dtype=float,
        )

        # 3. 混合归一化 + 加权融合
        # 语义分数归一化到 [0, 1]
        sem_min, sem_max = semantic_scores.min(), semantic_scores.max()
        if sem_max > sem_min:
            semantic_norm = (semantic_scores - sem_min) / (sem_max - sem_min)
        else:
            semantic_norm = np.zeros_like(semantic_scores)

        # 关键词分数归一化到 [0, 1]
        kw_max = keyword_scores.max()
        if kw_max > 0:
            keyword_norm = keyword_scores / kw_max
        else:
            keyword_norm = np.zeros_like(keyword_scores)

        # 融合：70% 语义 + 30% 关键词
        combined = 0.7 * semantic_norm + 0.3 * keyword_norm

        # 4. 取 top_k
        top_indices = np.argsort(combined)[-top_k:][::-1]
        top_docs = [self.documents[i] for i in top_indices]

        # 5. 格式化输出
        context_parts = []
        for doc in top_docs:
            context_parts.append(f"【{doc.source} - {doc.section}】\n{doc.content}")

        return "\n\n---\n\n".join(context_parts)


# 全局单例
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """获取 RAG 服务单例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
