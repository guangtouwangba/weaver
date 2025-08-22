#!/usr/bin/env python3
"""
Worker 监控脚本

实时监控 Celery Workers 的状态、性能和队列情况
"""

import os
import sys
import time
import json
import signal
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from celery import Celery
    from config import get_config
    import psutil
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请安装必要的依赖: pip install celery psutil")
    sys.exit(1)


class WorkerMonitor:
    """Worker 监控器"""

    def __init__(self):
        self.config = get_config()
        self.app = Celery(
            self.config.celery.app_name,
            broker=self.config.celery.broker_url,
            backend=self.config.celery.result_backend,
        )
        self.running = True

        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print("\n🛑 收到停止信号，正在退出...")
        self.running = False

    def get_worker_stats(self):
        """获取 Worker 统计信息"""
        try:
            inspect = self.app.control.inspect()

            # 获取活跃的 workers
            active_workers = inspect.active()
            reserved_tasks = inspect.reserved()
            scheduled_tasks = inspect.scheduled()
            worker_stats = inspect.stats()

            return {
                "active": active_workers or {},
                "reserved": reserved_tasks or {},
                "scheduled": scheduled_tasks or {},
                "stats": worker_stats or {},
            }
        except Exception as e:
            return {"error": str(e)}

    def get_queue_lengths(self):
        """获取队列长度"""
        try:
            # 这里需要根据实际的消息代理实现
            # Redis 示例
            import redis

            r = redis.from_url(self.config.celery.broker_url)

            queues = [
                "default",
                "document_queue",
                "rag_queue",
                "file_queue",
                "workflow_queue",
                "notification_queue",
            ]

            queue_info = {}
            for queue in queues:
                try:
                    length = r.llen(queue)
                    queue_info[queue] = length
                except:
                    queue_info[queue] = "N/A"

            return queue_info
        except Exception as e:
            return {"error": str(e)}

    def get_process_info(self):
        """获取进程信息"""
        process_info = []

        # 查找 worker 进程的 PID 文件
        logs_dir = Path("logs")
        if logs_dir.exists():
            for pid_file in logs_dir.glob("worker_*.pid"):
                try:
                    with open(pid_file, "r") as f:
                        pid = int(f.read().strip())

                    if psutil.pid_exists(pid):
                        process = psutil.Process(pid)

                        # 获取进程信息
                        info = {
                            "name": pid_file.stem,
                            "pid": pid,
                            "status": process.status(),
                            "cpu_percent": process.cpu_percent(),
                            "memory_percent": process.memory_percent(),
                            "memory_info": process.memory_info()._asdict(),
                            "create_time": datetime.fromtimestamp(
                                process.create_time()
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                            "num_threads": process.num_threads(),
                        }
                        process_info.append(info)
                    else:
                        # PID 文件存在但进程不存在，删除 PID 文件
                        pid_file.unlink()

                except (ValueError, psutil.NoSuchProcess, FileNotFoundError):
                    continue

        return process_info

    def print_dashboard(self, stats, queue_info, process_info):
        """打印监控面板"""
        # 清屏
        os.system("clear" if os.name == "posix" else "cls")

        # 标题
        print("🔍 Celery Worker 监控面板 - 架构优化版")
        print("=" * 80)
        print(f"🕒 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Worker 状态
        if "error" in stats:
            print(f"❌ Worker 状态获取失败: {stats['error']}")
        else:
            print("👥 Worker 状态:")
            active_count = len(stats["active"])
            if active_count > 0:
                print(f"  ✅ 活跃 Workers: {active_count}")

                # 显示每个 worker 的任务
                for worker_name, tasks in stats["active"].items():
                    print(f"    📋 {worker_name}: {len(tasks)} 个活跃任务")

                    if tasks:
                        for task in tasks[:3]:  # 只显示前3个任务
                            task_name = task.get("name", "Unknown")
                            task_id = task.get("id", "Unknown")[:8]
                            print(f"      🔧 {task_name} ({task_id}...)")

                        if len(tasks) > 3:
                            print(f"      ⏳ 还有 {len(tasks) - 3} 个任务...")
            else:
                print("  ⏸️  没有活跃的 Workers")

        print()

        # 队列状态
        print("📂 队列状态:")
        if "error" in queue_info:
            print(f"  ❌ 队列状态获取失败: {queue_info['error']}")
        else:
            total_pending = 0
            for queue, length in queue_info.items():
                if isinstance(length, int):
                    total_pending += length
                    status_icon = "📋" if length > 0 else "✅"
                    print(f"  {status_icon} {queue}: {length} 个待处理任务")
                else:
                    print(f"  ❓ {queue}: {length}")
            print(f"  📊 总待处理任务: {total_pending}")

        print()

        # 进程信息
        print("💻 进程信息:")
        if process_info:
            for info in process_info:
                status_icon = "🟢" if info["status"] == "running" else "🟡"
                memory_mb = info["memory_info"]["rss"] / 1024 / 1024

                print(f"  {status_icon} {info['name']} (PID: {info['pid']})")
                print(
                    f"    📊 CPU: {info['cpu_percent']:.1f}% | 内存: {info['memory_percent']:.1f}% ({memory_mb:.1f}MB)"
                )
                print(
                    f"    🧵 线程数: {info['num_threads']} | 启动时间: {info['create_time']}"
                )
        else:
            print("  ⏸️  没有运行中的 Worker 进程")

        print()

        # Worker 性能统计
        if "stats" in stats and stats["stats"]:
            print("📈 Worker 性能统计:")
            for worker_name, worker_stats in stats["stats"].items():
                if worker_stats:
                    pool_info = worker_stats.get("pool", {})
                    total_tasks = worker_stats.get("total", "N/A")

                    print(f"  📋 {worker_name}:")
                    print(f"    📊 总处理任务: {total_tasks}")

                    if pool_info:
                        processes = pool_info.get("processes", "N/A")
                        print(f"    🔧 进程数: {processes}")

        print()
        print("💡 按 Ctrl+C 退出监控")
        print("=" * 80)

    def run_continuous_monitoring(self, interval=5):
        """运行连续监控"""
        print("🚀 启动 Worker 监控...")
        print(f"📊 监控间隔: {interval} 秒")
        print("💡 按 Ctrl+C 停止监控")
        print()

        while self.running:
            try:
                # 获取统计信息
                stats = self.get_worker_stats()
                queue_info = self.get_queue_lengths()
                process_info = self.get_process_info()

                # 打印面板
                self.print_dashboard(stats, queue_info, process_info)

                # 等待下次更新
                time.sleep(interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 监控出错: {e}")
                time.sleep(interval)

        print("\n👋 监控已停止")

    def run_single_check(self):
        """运行单次检查"""
        print("🔍 执行单次 Worker 状态检查...")
        print()

        stats = self.get_worker_stats()
        queue_info = self.get_queue_lengths()
        process_info = self.get_process_info()

        self.print_dashboard(stats, queue_info, process_info)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Celery Worker 监控脚本")
    parser.add_argument(
        "--interval", "-i", type=int, default=5, help="监控间隔（秒）, 默认: 5"
    )
    parser.add_argument(
        "--once", "-o", action="store_true", help="只执行一次检查，不连续监控"
    )
    parser.add_argument("--json", "-j", action="store_true", help="以JSON格式输出结果")

    args = parser.parse_args()

    monitor = WorkerMonitor()

    if args.once:
        if args.json:
            # JSON 输出模式
            stats = monitor.get_worker_stats()
            queue_info = monitor.get_queue_lengths()
            process_info = monitor.get_process_info()

            result = {
                "timestamp": datetime.now().isoformat(),
                "worker_stats": stats,
                "queue_info": queue_info,
                "process_info": process_info,
            }

            print(json.dumps(result, indent=2, default=str))
        else:
            monitor.run_single_check()
    else:
        monitor.run_continuous_monitoring(args.interval)


if __name__ == "__main__":
    main()
