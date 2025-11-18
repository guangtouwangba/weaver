"""
运行时 RAGAS 评估服务

提供多种评估策略：
1. 采样评估 - 按比例评估部分查询
2. 异步评估 - 后台评估，不阻塞响应
3. 定期批量评估 - 定时收集数据批量评估
"""

import asyncio
import json
import logging
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .dataset import EvaluationDataset, EvaluationSample
from .ragas_evaluator import EvaluationMetrics, RAGASEvaluator

# 配置日志
logger = logging.getLogger(__name__)


class EvaluationMode(str, Enum):
    """评估模式"""

    DISABLED = "disabled"  # 禁用评估
    SAMPLING = "sampling"  # 采样评估（推荐）
    ASYNC_ALL = "async_all"  # 异步评估所有查询
    BATCH = "batch"  # 批量评估模式


@dataclass
class RuntimeEvaluationConfig:
    """运行时评估配置"""

    # 评估模式
    mode: EvaluationMode = EvaluationMode.SAMPLING

    # 采样率 (0.0-1.0)
    sampling_rate: float = 0.1  # 默认评估 10% 的查询

    # 评估指标
    metrics: List[EvaluationMetrics] = None

    # 批量评估配置
    batch_size: int = 10  # 收集多少个样本后批量评估
    batch_interval: int = 3600  # 批量评估间隔（秒）

    # 存储配置
    storage_dir: Path = Path("data/evaluation/runtime")
    max_samples_in_memory: int = 1000  # 内存中最多保留样本数

    # 结果存储
    save_results: bool = True
    results_file: str = "runtime_evaluation_results.jsonl"

    def __post_init__(self):
        """初始化后处理"""
        if self.metrics is None:
            # 默认使用快速评估指标（不需要 ground truth）
            self.metrics = [
                EvaluationMetrics.FAITHFULNESS,
                EvaluationMetrics.ANSWER_RELEVANCY,
            ]

        # 确保存储目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class QueryRecord:
    """查询记录"""

    query_id: str
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None
    metadata: Optional[Dict] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class RuntimeEvaluator:
    """运行时评估器"""

    def __init__(
        self,
        config: RuntimeEvaluationConfig,
        evaluator: RAGASEvaluator,
        on_evaluation_complete: Optional[Callable] = None,
    ):
        """
        初始化运行时评估器。

        Args:
            config: 评估配置
            evaluator: RAGAS 评估器实例
            on_evaluation_complete: 评估完成后的回调函数
        """
        self.config = config
        self.evaluator = evaluator
        self.on_evaluation_complete = on_evaluation_complete

        # 待评估的查询队列
        self.pending_queries: List[QueryRecord] = []

        # 评估结果缓存
        self.recent_results: List[Dict] = []

        # 统计信息
        self.stats = {
            "total_queries": 0,
            "evaluated_queries": 0,
            "skipped_queries": 0,
            "evaluation_errors": 0,
        }

        # 后台任务
        self._background_task: Optional[asyncio.Task] = None
        self._is_running = False

        logger.info("=" * 60)
        logger.info("✅ RuntimeEvaluator 初始化完成")
        logger.info(f"   模式: {config.mode.value}")
        logger.info(f"   采样率: {config.sampling_rate * 100:.1f}%")
        logger.info(f"   指标: {[m.value for m in config.metrics]}")
        logger.info(f"   存储目录: {config.storage_dir}")
        logger.info(f"   批量大小: {config.batch_size}")
        logger.info("=" * 60)

    async def start(self):
        """启动后台评估任务"""
        if self._is_running:
            return

        self._is_running = True

        if self.config.mode == EvaluationMode.BATCH:
            # 启动定期批量评估任务
            self._background_task = asyncio.create_task(self._batch_evaluation_loop())
            logger.info(f"🚀 已启动批量评估任务（间隔: {self.config.batch_interval}s）")

    async def stop(self):
        """停止后台评估任务"""
        self._is_running = False

        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

        # 评估剩余的查询
        if self.pending_queries:
            logger.info(f"🔄 评估剩余的 {len(self.pending_queries)} 个查询...")
            await self._evaluate_batch(self.pending_queries)
            self.pending_queries.clear()

        logger.info("🛑 RuntimeEvaluator 已停止")

    def should_evaluate(self) -> bool:
        """判断是否应该评估当前查询（用于采样）"""
        if self.config.mode == EvaluationMode.DISABLED:
            return False
        elif self.config.mode == EvaluationMode.ASYNC_ALL:
            return True
        elif self.config.mode == EvaluationMode.SAMPLING:
            return random.random() < self.config.sampling_rate
        elif self.config.mode == EvaluationMode.BATCH:
            return True  # 批量模式先收集，后评估
        return False

    async def record_query(
        self,
        query_id: str,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        记录一次查询，并根据配置决定是否评估。

        Args:
            query_id: 查询唯一 ID
            question: 用户问题
            answer: RAG 系统的答案
            contexts: 检索到的上下文
            ground_truth: 参考答案（可选）
            metadata: 额外元数据（可选）
        """
        self.stats["total_queries"] += 1

        logger.debug(f"📝 记录查询: query_id={query_id}, question_len={len(question)}, contexts={len(contexts)}")

        # 创建查询记录
        record = QueryRecord(
            query_id=query_id,
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth,
            metadata=metadata or {},
        )

        # 判断是否应该评估
        should_eval = self.should_evaluate()
        if not should_eval:
            self.stats["skipped_queries"] += 1
            logger.debug(f"⏭️  跳过评估: query_id={query_id} (采样未选中)")
            return

        logger.info(f"✅ 选中评估: query_id={query_id}, mode={self.config.mode.value}")

        # 根据模式处理
        if self.config.mode == EvaluationMode.BATCH:
            # 批量模式：加入队列
            self.pending_queries.append(record)
            logger.debug(f"📦 加入批量队列: {len(self.pending_queries)}/{self.config.batch_size}")

            # 如果队列满了，立即评估
            if len(self.pending_queries) >= self.config.batch_size:
                logger.info(f"🎯 批量队列已满，开始评估...")
                await self._evaluate_batch(self.pending_queries)
                self.pending_queries.clear()

        else:
            # 采样/异步模式：立即异步评估
            logger.debug(f"🚀 启动异步评估: query_id={query_id}")
            asyncio.create_task(self._evaluate_single(record))

    async def _evaluate_single(self, record: QueryRecord):
        """评估单个查询"""
        logger.info(f"🎯 开始单个评估: query_id={record.query_id}")

        try:
            # 创建临时数据集
            dataset = EvaluationDataset(name="runtime_single")
            dataset.add_sample(
                question=record.question,
                answer=record.answer,
                contexts=record.contexts,
                ground_truth=record.ground_truth,
                metadata=record.metadata,
            )

            logger.debug(f"   指标: {[m.value for m in self.config.metrics]}")

            # 评估 - 在线程池中运行以避免 uvloop 嵌套事件循环问题
            logger.debug(f"   开始 RAGAS 评估...")
            loop = asyncio.get_event_loop()

            # 使用线程池执行同步的 evaluate 调用
            results = await loop.run_in_executor(
                None,  # 使用默认线程池
                lambda: self.evaluator.evaluate_sync(dataset, metrics=self.config.metrics),
            )

            logger.info(f"   ✅ 评估完成: {results.scores}")

            # 记录结果
            result = {
                "query_id": record.query_id,
                "timestamp": record.timestamp,
                "scores": results.scores,
                "question": record.question[:100] + "..." if len(record.question) > 100 else record.question,
            }

            self._store_result(result)
            self.stats["evaluated_queries"] += 1

            logger.info(f"💾 结果已保存: query_id={record.query_id}")

            # 调用回调
            if self.on_evaluation_complete:
                logger.debug(f"🔔 触发回调: query_id={record.query_id}")
                await self.on_evaluation_complete(result)

        except Exception as e:
            logger.error(f"❌ 评估失败 (query_id={record.query_id}): {e}", exc_info=True)
            self.stats["evaluation_errors"] += 1

    async def _evaluate_batch(self, records: List[QueryRecord]):
        """批量评估多个查询"""
        if not records:
            return

        logger.info("=" * 60)
        logger.info(f"🎯 开始批量评估 {len(records)} 个查询...")
        logger.info(f"   指标: {[m.value for m in self.config.metrics]}")

        try:
            # 创建数据集
            logger.debug(f"   创建评估数据集...")
            dataset = EvaluationDataset(name="runtime_batch")
            for i, record in enumerate(records, 1):
                dataset.add_sample(
                    question=record.question,
                    answer=record.answer,
                    contexts=record.contexts,
                    ground_truth=record.ground_truth,
                    metadata={**record.metadata, "query_id": record.query_id},
                )
                logger.debug(f"      [{i}/{len(records)}] query_id={record.query_id}")

            # 批量评估
            logger.info(f"   开始 RAGAS 批量评估...")
            results = await self.evaluator.evaluate(dataset, metrics=self.config.metrics)

            logger.info(f"✅ 批量评估完成！")
            logger.info(f"   平均分数:")
            for metric, score in results.scores.items():
                logger.info(f"      {metric}: {score:.3f}")

            # 记录结果
            batch_result = {
                "batch_timestamp": datetime.now().isoformat(),
                "batch_size": len(records),
                "avg_scores": results.scores,
                "queries": [r.query_id for r in records],
            }

            self._store_result(batch_result)
            self.stats["evaluated_queries"] += len(records)

            logger.info(f"💾 批量结果已保存")
            logger.info("=" * 60)

            # 调用回调
            if self.on_evaluation_complete:
                logger.debug(f"🔔 触发批量回调")
                await self.on_evaluation_complete(batch_result)

        except Exception as e:
            logger.error(f"❌ 批量评估失败: {e}", exc_info=True)
            self.stats["evaluation_errors"] += len(records)

    async def _batch_evaluation_loop(self):
        """批量评估循环（后台任务）"""
        logger.info(f"🔁 批量评估循环已启动，间隔: {self.config.batch_interval}s")

        while self._is_running:
            try:
                # 等待指定间隔
                logger.debug(f"⏰ 等待下次批量评估...")
                await asyncio.sleep(self.config.batch_interval)

                # 如果有待评估的查询，执行评估
                if self.pending_queries:
                    logger.info(f"⏰ 定时批量评估触发 (队列: {len(self.pending_queries)} 个查询)")
                    await self._evaluate_batch(self.pending_queries)
                    self.pending_queries.clear()
                else:
                    logger.debug(f"⏰ 定时触发，但队列为空，跳过")

            except asyncio.CancelledError:
                logger.info("🛑 批量评估循环被取消")
                break
            except Exception as e:
                logger.error(f"❌ 批量评估循环错误: {e}", exc_info=True)

    def _store_result(self, result: Dict):
        """存储评估结果"""
        # 添加到缓存
        self.recent_results.append(result)
        logger.debug(f"💾 结果添加到缓存 (当前缓存: {len(self.recent_results)})")

        # 限制内存中的结果数量
        if len(self.recent_results) > 100:
            self.recent_results = self.recent_results[-100:]
            logger.debug(f"   缓存已裁剪到 100 条")

        # 保存到文件
        if self.config.save_results:
            try:
                results_path = self.config.storage_dir / self.config.results_file
                with open(results_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                logger.debug(f"   已保存到文件: {results_path}")
            except Exception as e:
                logger.error(f"   ❌ 保存文件失败: {e}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()

        # 计算评估率
        if stats["total_queries"] > 0:
            stats["evaluation_rate"] = stats["evaluated_queries"] / stats["total_queries"]
        else:
            stats["evaluation_rate"] = 0.0

        # 添加最近的评估结果摘要
        if self.recent_results:
            recent_scores = [r.get("scores", {}) for r in self.recent_results if "scores" in r]
            if recent_scores:
                # 计算平均分
                avg_scores = {}
                for metric in self.config.metrics:
                    metric_name = metric.value
                    scores = [s.get(metric_name, 0) for s in recent_scores if metric_name in s]
                    if scores:
                        avg_scores[metric_name] = sum(scores) / len(scores)

                stats["recent_avg_scores"] = avg_scores

        return stats

    def get_recent_results(self, limit: int = 10) -> List[Dict]:
        """获取最近的评估结果"""
        return self.recent_results[-limit:]


# ========================================
# 便捷函数
# ========================================


def create_runtime_evaluator(
    llm, embeddings, mode: str = "sampling", sampling_rate: float = 0.1, metrics: Optional[List[str]] = None
) -> RuntimeEvaluator:
    """
    创建运行时评估器的便捷函数。

    Args:
        llm: LLM 实例
        embeddings: Embeddings 实例
        mode: 评估模式 (disabled/sampling/async_all/batch)
        sampling_rate: 采样率 (0.0-1.0)
        metrics: 评估指标列表

    Returns:
        RuntimeEvaluator 实例
    """
    # 转换指标
    metric_enums = []
    if metrics:
        for m in metrics:
            try:
                metric_enums.append(EvaluationMetrics(m))
            except ValueError:
                logger.warning(f"⚠️  未知指标: {m}，已跳过")

    # 创建配置
    config = RuntimeEvaluationConfig(
        mode=EvaluationMode(mode), sampling_rate=sampling_rate, metrics=metric_enums if metric_enums else None
    )

    # 创建评估器
    ragas_evaluator = RAGASEvaluator(llm=llm, embeddings=embeddings)

    return RuntimeEvaluator(config=config, evaluator=ragas_evaluator)
