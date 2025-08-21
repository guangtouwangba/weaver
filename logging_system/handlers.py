"""
日志处理器模块

提供各种特殊用途的日志处理器，支持异步、轮转、远程存储等。
"""

import asyncio
import logging
import logging.handlers
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from logging import LogRecord


class AsyncFileHandler(logging.Handler):
    """异步文件处理器 - 不阻塞主线程的文件写入"""
    
    def __init__(self, 
                 filename: str,
                 mode: str = 'a',
                 encoding: str = 'utf-8',
                 queue_size: int = 1000,
                 flush_interval: float = 1.0):
        super().__init__()
        
        self.filename = filename
        self.mode = mode
        self.encoding = encoding
        self.flush_interval = flush_interval
        
        # 确保目录存在
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        # 创建队列和后台线程
        self.queue = queue.Queue(maxsize=queue_size)
        self.stop_event = threading.Event()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        self._file_handle = None
        self._lock = threading.Lock()
    
    def _get_file_handle(self):
        """获取文件句柄"""
        if self._file_handle is None or self._file_handle.closed:
            self._file_handle = open(self.filename, self.mode, encoding=self.encoding)
        return self._file_handle
    
    def _worker(self):
        """后台工作线程"""
        last_flush = time.time()
        pending_records = []
        
        while not self.stop_event.is_set():
            try:
                # 尝试从队列获取记录
                try:
                    record = self.queue.get(timeout=0.1)
                    if record is None:  # 停止信号
                        break
                    pending_records.append(record)
                except queue.Empty:
                    pass
                
                # 检查是否需要刷新
                current_time = time.time()
                should_flush = (
                    pending_records and 
                    (current_time - last_flush >= self.flush_interval or len(pending_records) >= 10)
                )
                
                if should_flush:
                    self._flush_records(pending_records)
                    pending_records.clear()
                    last_flush = current_time
                    
            except Exception as e:
                # 记录错误到stderr，避免递归
                import sys
                sys.stderr.write(f"AsyncFileHandler error: {e}\n")
        
        # 处理剩余记录
        if pending_records:
            self._flush_records(pending_records)
    
    def _flush_records(self, records: list):
        """批量刷新记录到文件"""
        try:
            with self._lock:
                file_handle = self._get_file_handle()
                for record in records:
                    formatted = self.format(record)
                    file_handle.write(formatted + '\n')
                file_handle.flush()
        except Exception as e:
            import sys
            sys.stderr.write(f"Failed to write log records: {e}\n")
    
    def emit(self, record: LogRecord):
        """发射日志记录"""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # 队列满了，丢弃最旧的记录
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(record)
            except queue.Empty:
                pass
    
    def close(self):
        """关闭处理器"""
        # 发送停止信号
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            pass
        
        self.stop_event.set()
        
        # 等待工作线程结束
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        
        # 关闭文件
        with self._lock:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.close()
        
        super().close()


class RotatingFileHandler(logging.handlers.RotatingFileHandler):
    """增强的轮转文件处理器"""
    
    def __init__(self, 
                 filename: str,
                 mode: str = 'a',
                 maxBytes: int = 10 * 1024 * 1024,  # 10MB
                 backupCount: int = 5,
                 encoding: str = 'utf-8',
                 delay: bool = False,
                 compress: bool = True):
        
        # 确保目录存在
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compress = compress
    
    def doRollover(self):
        """执行日志轮转"""
        super().doRollover()
        
        # 压缩旧日志文件
        if self.compress and self.backupCount > 0:
            self._compress_backup_files()
    
    def _compress_backup_files(self):
        """压缩备份文件"""
        import gzip
        import os
        
        for i in range(1, self.backupCount + 1):
            backup_name = f"{self.baseFilename}.{i}"
            compressed_name = f"{backup_name}.gz"
            
            if os.path.exists(backup_name) and not os.path.exists(compressed_name):
                try:
                    with open(backup_name, 'rb') as f_in:
                        with gzip.open(compressed_name, 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    # 删除原文件
                    os.remove(backup_name)
                except Exception as e:
                    # 压缩失败，保留原文件
                    import sys
                    sys.stderr.write(f"Failed to compress {backup_name}: {e}\n")


class ElasticsearchHandler(logging.Handler):
    """Elasticsearch日志处理器"""
    
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 9200,
                 index: str = 'logs',
                 doc_type: str = '_doc',
                 username: str = None,
                 password: str = None,
                 use_ssl: bool = False,
                 verify_certs: bool = True,
                 buffer_size: int = 100,
                 flush_interval: float = 5.0):
        
        super().__init__()
        
        self.host = host
        self.port = port
        self.index = index
        self.doc_type = doc_type
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # 连接配置
        self.connection_config = {
            'host': host,
            'port': port,
            'use_ssl': use_ssl,
            'verify_certs': verify_certs
        }
        
        if username and password:
            self.connection_config.update({
                'http_auth': (username, password)
            })
        
        # 缓冲区和定时器
        self.buffer = []
        self.buffer_lock = threading.Lock()
        self.timer = None
        
        # 延迟初始化ES客户端
        self.es_client = None
    
    def _get_es_client(self):
        """获取Elasticsearch客户端"""
        if self.es_client is None:
            try:
                from elasticsearch import Elasticsearch
                self.es_client = Elasticsearch([self.connection_config])
            except ImportError:
                raise ImportError("elasticsearch package is required for ElasticsearchHandler")
        return self.es_client
    
    def _create_document(self, record: LogRecord) -> Dict[str, Any]:
        """创建ES文档"""
        doc = {
            '@timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }
        
        # 添加异常信息
        if record.exc_info:
            doc['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1])
            }
        
        # 添加extra字段
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'message', 'stack_info', 'exc_info', 'exc_text']:
                doc[key] = value
        
        return doc
    
    def emit(self, record: LogRecord):
        """发射日志记录"""
        try:
            doc = self._create_document(record)
            
            with self.buffer_lock:
                self.buffer.append(doc)
                
                # 检查是否需要刷新
                if len(self.buffer) >= self.buffer_size:
                    self._flush_buffer()
                elif self.timer is None:
                    # 启动定时刷新
                    self._start_timer()
                    
        except Exception:
            self.handleError(record)
    
    def _flush_buffer(self):
        """刷新缓冲区到ES"""
        if not self.buffer:
            return
        
        try:
            es = self._get_es_client()
            
            # 构建批量请求
            body = []
            for doc in self.buffer:
                body.append({'index': {'_index': self.index, '_type': self.doc_type}})
                body.append(doc)
            
            # 批量索引
            es.bulk(body=body)
            
            self.buffer.clear()
            
        except Exception as e:
            # 记录错误到stderr
            import sys
            sys.stderr.write(f"ElasticsearchHandler error: {e}\n")
            
            # 清空缓冲区以避免内存泄漏
            self.buffer.clear()
        
        finally:
            # 重置定时器
            self.timer = None
    
    def _start_timer(self):
        """启动定时刷新"""
        if self.timer is None:
            self.timer = threading.Timer(self.flush_interval, self._flush_buffer)
            self.timer.start()
    
    def flush(self):
        """立即刷新"""
        with self.buffer_lock:
            self._flush_buffer()
    
    def close(self):
        """关闭处理器"""
        # 取消定时器
        if self.timer:
            self.timer.cancel()
        
        # 刷新剩余记录
        with self.buffer_lock:
            self._flush_buffer()
        
        super().close()


class CallbackHandler(logging.Handler):
    """回调处理器 - 支持自定义处理逻辑"""
    
    def __init__(self, callback: Callable[[LogRecord], None]):
        super().__init__()
        self.callback = callback
    
    def emit(self, record: LogRecord):
        """发射日志记录"""
        try:
            self.callback(record)
        except Exception:
            self.handleError(record)


class MemoryHandler(logging.handlers.MemoryHandler):
    """增强的内存处理器"""
    
    def __init__(self, 
                 capacity: int = 1000,
                 flushLevel: int = logging.ERROR,
                 target: logging.Handler = None,
                 flushOnClose: bool = True):
        super().__init__(capacity, flushLevel, target, flushOnClose)
        
        # 添加统计信息
        self.stats = {
            'records_buffered': 0,
            'records_flushed': 0,
            'flush_count': 0
        }
    
    def emit(self, record: LogRecord):
        """发射日志记录"""
        super().emit(record)
        self.stats['records_buffered'] += 1
    
    def flush(self):
        """刷新缓冲区"""
        if self.target:
            records_to_flush = len(self.buffer)
            super().flush()
            self.stats['records_flushed'] += records_to_flush
            self.stats['flush_count'] += 1
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats['buffer_size'] = len(self.buffer)
        stats['buffer_capacity'] = self.capacity
        return stats


# 处理器工厂函数
def create_handler(handler_type: str, **config) -> logging.Handler:
    """创建日志处理器"""
    
    handlers = {
        'console': logging.StreamHandler,
        'file': logging.FileHandler,
        'rotating_file': RotatingFileHandler,
        'async_file': AsyncFileHandler,
        'elasticsearch': ElasticsearchHandler,
        'memory': MemoryHandler
    }
    
    handler_class = handlers.get(handler_type.lower())
    if not handler_class:
        raise ValueError(f"Unknown handler type: {handler_type}")
    
    # 过滤配置参数
    if handler_type == 'console':
        # StreamHandler只接受stream参数
        filtered_config = {}
        if 'stream' in config:
            filtered_config['stream'] = config['stream']
    else:
        filtered_config = config
    
    return handler_class(**filtered_config)