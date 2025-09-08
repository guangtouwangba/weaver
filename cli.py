#!/usr/bin/env python3
"""
RAG CLI Client - RAG知识管理系统客户端

基于NotebookLM概念的智能知识管理系统，提供完整的RAG功能支持。
支持主题管理、文件处理、智能聊天和系统监控等核心功能。

主要功能:
    - 主题管理: 创建、删除、查看和切换知识主题
    - 文件处理: 批量上传、处理、嵌入和索引文档
    - 智能聊天: 基于检索增强的对话交互
    - 系统监控: 服务状态、性能指标和健康检查
    - 数据管理: 清理、备份和恢复功能

使用方法:
    python cli.py init                     # 初始化系统
    python cli.py topics create "研究项目"  # 创建主题
    python cli.py files upload ./docs     # 上传文件
    python cli.py chat                     # 开始对话
    python cli.py system status           # 查看状态
"""

import asyncio
import atexit
import json
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Prompt, Confirm
from rich.status import Status
from tqdm import tqdm

# 添加项目根目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent))

# 导入现有服务
from config.settings import get_config
from modules.database import get_db_session
from modules.services.rag_integrated_chat_service import RAGIntegratedChatService, create_rag_integrated_chat_service
from modules.services.file_service import FileService
from modules.services.topic_service import TopicService
from modules.repository.file_repository import FileRepository
from modules.vector_store.weaviate_service import WeaviateVectorStore
from modules.storage import LocalStorage
from modules.schemas.chat import ChatRequest
from modules.schemas.topic import TopicCreate
from modules.schemas.enums import FileStatus

# 全局变量存储服务实例
console = Console()
services = {}

# CLI状态文件路径
CLI_STATE_FILE = Path.home() / ".rag_cli_state.json"

# 默认配置
cli_config = {
    'current_topic_id': None,
    'current_topic_name': 'default',
    'services_initialized': False,  # 标记服务是否已初始化
}


def load_cli_state():
    """加载CLI状态"""
    try:
        if CLI_STATE_FILE.exists():
            with open(CLI_STATE_FILE, 'r') as f:
                state = json.load(f)
                cli_config.update(state)
    except Exception:
        pass  # 忽略加载错误，使用默认状态


def save_cli_state():
    """保存CLI状态"""
    try:
        with open(CLI_STATE_FILE, 'w') as f:
            json.dump(cli_config, f)
    except Exception:
        pass  # 忽略保存错误


# 启动时加载状态
load_cli_state()


class CLIError(Exception):
    """CLI错误基类"""
    pass


async def cleanup_services():
    """清理所有服务资源"""
    try:
        # 清理向量存储
        if 'vector_store' in services:
            await services['vector_store'].cleanup()
            
        # 清理聊天服务
        if 'chat_service' in services:
            await services['chat_service'].close()
            
    except Exception as e:
        # 忽略清理过程中的错误，避免影响程序退出
        pass


def cleanup_handler():
    """同步清理处理器，用于atexit"""
    try:
        # 安全的事件循环检查和清理
        try:
            loop = asyncio.get_running_loop()
            if loop and not loop.is_closed():
                # 如果有运行中的循环，创建任务
                asyncio.create_task(cleanup_services())
        except RuntimeError:
            # 没有运行中的事件循环，创建新的
            try:
                asyncio.run(cleanup_services())
            except Exception:
                pass  # 忽略清理过程中的错误
    except Exception:
        # 忽略所有清理错误
        pass


def signal_handler(signum, frame):
    """信号处理器"""
    cleanup_handler()
    sys.exit(0)


# 注册清理处理器
atexit.register(cleanup_handler)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def _show_welcome_message():
    """显示欢迎信息和帮助"""
    console.print(Panel.fit(
        "[bold cyan]RAG CLI Client[/bold cyan]\n\n"
        "智能知识管理系统客户端\n"
        "基于NotebookLM概念，提供完整的RAG功能支持",
        title="🎯 欢迎使用",
        border_style="cyan"
    ))
    
    console.print("\n[bold green]主要功能模块:[/bold green]")
    console.print("  [cyan]python cli.py init[/cyan]           - 系统初始化")
    console.print("  [cyan]python cli.py topics --help[/cyan]  - 主题管理")
    console.print("  [cyan]python cli.py files --help[/cyan]   - 文件处理")
    console.print("  [cyan]python cli.py chat[/cyan]           - 智能对话")
    console.print("  [cyan]python cli.py system --help[/cyan]  - 系统管理")
    console.print("\n使用 [cyan]--help[/cyan] 查看详细命令帮助")
    

def _format_timestamp(timestamp: Optional[datetime]) -> str:
    """格式化时间戳"""
    if not timestamp:
        return "N/A"
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    

def _format_file_size(size: int) -> str:
    """格式化文件大小"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


def error_handler(func):
    """错误处理装饰器"""
    import functools
    
    @functools.wraps(func)  # 保持原函数的元数据
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return asyncio.run(result)
            return result
        except CLIError as e:
            console.print(f"[red]错误: {e}[/red]")
            sys.exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]用户取消操作[/yellow]")
            sys.exit(0)
        except Exception as e:
            console.print(f"[red]未知错误: {e}[/red]")
            try:
                ctx = click.get_current_context()
                if ctx.obj and ctx.obj.get('debug', False):
                    import traceback
                    console.print(traceback.format_exc())
            except:
                pass  # 忽略获取上下文失败的情况
            sys.exit(1)
    return wrapper


@click.group()
@click.option('--debug', is_flag=True, help='启用调试模式')
@click.option('--config', type=click.Path(exists=True), help='指定配置文件路径')
@click.option('--profile', default='default', help='指定配置文件')
@click.pass_context
def cli(ctx, debug, config, profile):
    """RAG CLI Client - RAG知识管理系统客户端
    
    基于NotebookLM概念的智能知识管理系统，提供完整的主题管理、文件处理、
    智能对话和系统监控功能。支持多租户、异步处理和分布式部署。
    """
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['config'] = config
    ctx.obj['profile'] = profile
    
    # 显示欢迎信息（仅在主命令时）
    if ctx.invoked_subcommand is None:
        _show_welcome_message()
        
        # 提示用户新命令
        console.print("\n[yellow]ℹ️  旧命令更新提示:[/yellow]")
        console.print("  [dim]`python cli.py start` → `python cli.py init`[/dim]")
        console.print("  [dim]`python cli.py load` → `python cli.py files upload`[/dim]")
        console.print("  [dim]`python cli.py status` → `python cli.py system status`[/dim]")


# ==================== 系统初始化命令 ====================

@cli.command(name='init')
@error_handler
async def init_system():
    """初始化RAG服务和连接"""
    console.print("[bold green]🚀 启动RAG服务...[/bold green]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        
        # 1. 加载配置
        task = progress.add_task("加载配置...", total=None)
        try:
            config = get_config()
            progress.update(task, description="✅ 配置加载完成")
            await asyncio.sleep(0.1)  # 让用户看到进度
        except Exception as e:
            raise CLIError(f"配置加载失败: {e}")
        
        # 2. 初始化数据库
        progress.update(task, description="初始化数据库连接...")
        try:
            from modules.database import DatabaseConnection
            db = DatabaseConnection()
            await db.initialize()
            progress.update(task, description="✅ 数据库连接成功")
            await asyncio.sleep(0.1)
        except Exception as e:
            console.print(f"[yellow]警告: 数据库连接失败: {e}[/yellow]")
            progress.update(task, description="⚠️ 数据库连接失败")
        
        # 3. 初始化向量存储
        progress.update(task, description="初始化向量存储...")
        try:
            weaviate_url = getattr(config, 'weaviate_url', 'http://localhost:8080')
            vector_store = WeaviateVectorStore(url=weaviate_url)
            await vector_store.initialize()
            services['vector_store'] = vector_store
            progress.update(task, description="✅ 向量存储连接成功")
            await asyncio.sleep(0.1)
        except Exception as e:
            console.print(f"[yellow]警告: 向量存储连接失败: {e}[/yellow]")
            console.print("[yellow]某些功能可能不可用[/yellow]")
        
        # 4. 初始化RAG集成聊天服务
        progress.update(task, description="初始化增强AI服务...")
        try:
            chat_service = await create_rag_integrated_chat_service(
                pipeline_type="adaptive",
                enable_routing=True
            )
            services['chat_service'] = chat_service
            progress.update(task, description="✅ 增强AI服务初始化成功")
            await asyncio.sleep(0.1)
        except Exception as e:
            console.print(f"[yellow]警告: 增强AI服务初始化失败: {e}[/yellow]")
            console.print("[yellow]聊天功能可能不可用[/yellow]")
        
        # 5. 初始化默认主题
        progress.update(task, description="设置默认主题...")
        try:
            # 创建默认主题（如果不存在）
            from modules.database import get_db_session
            from modules.services.topic_service import TopicService
            
            session_gen = get_db_session()
            session = await session_gen.__anext__()
            
            try:
                topic_service = TopicService(session)
                # 尝试创建默认主题
                topic_data = TopicCreate(
                    name="CLI开发测试",
                    description="CLI工具的默认开发主题"
                )
                topic = await topic_service.create_topic(topic_data)
                cli_config['current_topic_id'] = topic.id
                cli_config['current_topic_name'] = topic.name
                cli_config['services_initialized'] = True
                save_cli_state()
                progress.update(task, description="✅ 默认主题创建完成")
            except Exception as e:
                # 如果创建失败（可能已存在），使用null topic_id
                cli_config['current_topic_id'] = None
                cli_config['current_topic_name'] = "CLI开发测试"
                cli_config['services_initialized'] = True
                save_cli_state()
                progress.update(task, description="✅ 默认主题设置完成")
            finally:
                if session:
                    await session.close()
                    
        except Exception as e:
            # 完全回退方案
            cli_config['current_topic_id'] = None
            cli_config['current_topic_name'] = "CLI开发测试"
            cli_config['services_initialized'] = True
            save_cli_state()
            console.print(f"[yellow]警告: 主题设置失败，使用默认配置: {e}[/yellow]")
    
    console.print("\n[bold green]🎉 RAG系统初始化完成![/bold green]")
    console.print(f"当前主题: [cyan]{cli_config['current_topic_name']}[/cyan]")
    console.print("\n下一步操作:")
    console.print("  [cyan]python cli.py files upload ./docs[/cyan]     - 上传文件")
    console.print("  [cyan]python cli.py system status[/cyan]           - 查看状态")
    console.print("  [cyan]python cli.py chat[/cyan]                    - 开始对话")
    console.print("  [cyan]python cli.py topics --help[/cyan]           - 主题管理")
    
    # 在init命令结束前进行清理，避免资源泄漏
    await cleanup_services()


# ==================== 主题管理命令组 ====================

@cli.group()
def topics():
    """主题管理 - 创建、删除、查看和切换知识主题"""
    pass


@topics.command(name='create')
@click.argument('name')
@click.option('--description', '-d', help='主题描述')
@click.option('--set-active', is_flag=True, help='创建后立即设为当前主题')
@error_handler
async def create_topic(name, description, set_active):
    """创建新主题"""
    console.print(f"[bold blue]🎨 创建主题: {name}[/bold blue]")
    
    session_gen = get_db_session()
    session = await session_gen.__anext__()
    
    try:
        topic_service = TopicService(session)
        
        # 创建主题
        topic_data = TopicCreate(
            name=name,
            description=description or f"主题: {name}"
        )
        topic = await topic_service.create_topic(topic_data)
        
        console.print(f"[green]✅ 主题创建成功![/green]")
        console.print(f"ID: {topic.id}")
        console.print(f"名称: {topic.name}")
        console.print(f"描述: {topic.description}")
        
        # 设为当前主题
        if set_active:
            cli_config['current_topic_id'] = topic.id
            cli_config['current_topic_name'] = topic.name
            save_cli_state()
            console.print(f"[cyan]🎯 已设为当前主题[/cyan]")
            
    except Exception as e:
        raise CLIError(f"创建主题失败: {e}")
    finally:
        if session:
            await session.close()


@topics.command(name='list')
@click.option('--limit', '-l', default=20, help='显示数量限制')
@error_handler
async def list_topics(limit):
    """列出所有主题"""
    console.print("[bold blue]📚 主题列表[/bold blue]")
    
    session_gen = get_db_session()
    session = await session_gen.__anext__()
    
    try:
        topic_service = TopicService(session)
        topic_list = await topic_service.list_topics(page_size=limit)
        topics = topic_list.topics
        
        if not topics:
            console.print("[yellow]暂无主题，使用 'topics create' 创建新主题[/yellow]")
            return
            
        # 创建表格
        table = Table(title=f"主题列表 (显示 {len(topics)}/{limit})")
        table.add_column("ID", style="dim")
        table.add_column("名称", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("描述", style="white")
        table.add_column("创建时间", style="dim")
        table.add_column("文件数", style="magenta")
        
        current_topic_id = cli_config.get('current_topic_id')
        
        for topic in topics:
            # 标记当前主题
            name_display = topic.name
            if topic.id == current_topic_id:
                name_display = f"{topic.name} 🎯"
                
            table.add_row(
                str(topic.id)[:8] + "...",
                name_display,
                topic.status.value if hasattr(topic.status, 'value') else str(topic.status),
                topic.description or "N/A",
                _format_timestamp(topic.created_at),
                str(getattr(topic, 'file_count', 0))
            )
        
        console.print(table)
        console.print(f"\n[cyan]当前主题: {cli_config.get('current_topic_name', 'N/A')}[/cyan]")
        
    except Exception as e:
        raise CLIError(f"获取主题列表失败: {e}")
    finally:
        if session:
            await session.close()


@topics.command(name='switch')
@click.argument('topic_id')
@error_handler
async def switch_topic(topic_id):
    """切换当前主题"""
    console.print(f"[bold blue]🔄 切换主题: {topic_id}[/bold blue]")
    
    session_gen = get_db_session()
    session = await session_gen.__anext__()
    
    try:
        topic_service = TopicService(session)
        topic = await topic_service.get_topic(int(topic_id))
        
        if not topic:
            raise CLIError(f"主题不存在: {topic_id}")
        
        cli_config['current_topic_id'] = topic.id
        cli_config['current_topic_name'] = topic.name
        save_cli_state()
        
        console.print(f"[green]✅ 已切换到主题: {topic.name}[/green]")
        console.print(f"ID: {topic.id}")
        console.print(f"描述: {topic.description}")
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise CLIError(f"主题不存在: {topic_id}")
        raise CLIError(f"切换主题失败: {e}")
    finally:
        if session:
            await session.close()


@topics.command(name='show')
@click.argument('topic_id', required=False)
@error_handler
async def show_topic(topic_id):
    """查看主题详情（默认显示当前主题）"""
    if not topic_id:
        topic_id = cli_config.get('current_topic_id')
        if not topic_id:
            raise CLIError("未指定主题ID且没有当前主题")
    
    console.print(f"[bold blue]🔍 主题详情: {topic_id}[/bold blue]")
    
    session_gen = get_db_session()
    session = await session_gen.__anext__()
    
    try:
        topic_service = TopicService(session)
        topic = await topic_service.get_topic(int(topic_id) if isinstance(topic_id, str) else topic_id)
        
        if not topic:
            raise CLIError(f"主题不存在: {topic_id}")
        
        # 创建主题信息面板
        info = (
            f"[bold]主题名称:[/bold] {topic.name}\n"
            f"[bold]ID:[/bold] {topic.id}\n"
            f"[bold]状态:[/bold] {getattr(topic.status, 'value', str(topic.status))}\n"
            f"[bold]描述:[/bold] {topic.description or 'N/A'}\n"
            f"[bold]创建时间:[/bold] {_format_timestamp(topic.created_at)}\n"
            f"[bold]更新时间:[/bold] {_format_timestamp(topic.updated_at)}"
        )
        
        console.print(Panel(info, title="主题信息", border_style="cyan"))
        
        # TODO: 显示关联文件统计信息
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise CLIError(f"主题不存在: {topic_id}")
        raise CLIError(f"查看主题失败: {e}")
    finally:
        if session:
            await session.close()


@topics.command(name='delete')
@click.argument('topic_id')
@click.option('--force', is_flag=True, help='强制删除，不提示确认')
@error_handler
async def delete_topic(topic_id, force):
    """删除主题"""
    console.print(f"[bold red]⚠️ 删除主题: {topic_id}[/bold red]")
    
    # 确认删除
    if not force:
        if not Confirm.ask(f"确定要删除主题 {topic_id} 吗？这将一同删除所有关联数据"):
            console.print("[yellow]操作已取消[/yellow]")
            return
    
    session_gen = get_db_session()
    session = await session_gen.__anext__()
    
    try:
        topic_service = TopicService(session)
        
        # 检查主题是否存在
        topic = await topic_service.get_topic(int(topic_id))
        if not topic:
            raise CLIError(f"主题不存在: {topic_id}")
        
        # 执行删除
        await topic_service.delete_topic(topic_id)
        
        console.print(f"[green]✅ 主题已删除: {topic.name}[/green]")
        
        # 如果删除的是当前主题，清除状态
        if topic_id == cli_config.get('current_topic_id'):
            cli_config['current_topic_id'] = None
            cli_config['current_topic_name'] = None
            save_cli_state()
            console.print("[yellow]已清除当前主题状态[/yellow]")
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise CLIError(f"主题不存在: {topic_id}")
        raise CLIError(f"删除主题失败: {e}")
    finally:
        if session:
            await session.close()


# ==================== 文件管理命令组 ====================

@cli.group()
def files():
    """文件管理 - 上传、处理、索引和管理文档"""
    pass


@files.command(name='upload')
@click.argument('path', type=click.Path(exists=True))
@click.option('--topic-id', help='指定主题ID（默认使用当前主题）')
@click.option('--recursive/--no-recursive', default=True, help='是否递归处理子目录')
@click.option('--confirm/--no-confirm', default=True, help='是否显示确认提示')
@click.option('--process/--no-process', default=True, help='是否立即开始处理')
@error_handler
async def upload_files(path, topic_id, recursive, confirm, process):
    """上传文件或目录到RAG系统"""
    path = Path(path).resolve()
    
    # 获取目标主题
    target_topic_id = topic_id or cli_config.get('current_topic_id')
    if not target_topic_id:
        raise CLIError("未指定主题ID且没有当前主题，请先创建或切换主题")
    
    console.print(f"[bold blue]📤 上传文件: {path}[/bold blue]")
    console.print(f"目标主题: {cli_config.get('current_topic_name', target_topic_id)}")
    
    # 支持的文件类型
    supported_extensions = {'.pdf', '.txt', '.md', '.docx'}
    
    # 扫描文件
    files_to_process = []
    
    if path.is_file():
        # 单个文件
        if path.suffix.lower() in supported_extensions:
            files_to_process.append(path)
        else:
            raise CLIError(f"不支持的文件类型: {path.suffix}")
    else:
        # 目录
        pattern = "**/*" if recursive else "*"
        for ext in supported_extensions:
            files_to_process.extend(path.glob(f"{pattern}{ext}"))
    
    if not files_to_process:
        console.print(f"[yellow]在 {path} 中未找到支持的文件类型[/yellow]")
        console.print(f"支持的类型: {', '.join(supported_extensions)}")
        return
    
    console.print(f"[green]找到 {len(files_to_process)} 个文件待处理[/green]")
    
    # 显示文件列表
    table = Table(title="待处理文件")
    table.add_column("文件名", style="cyan")
    table.add_column("大小", style="magenta") 
    table.add_column("类型", style="green")
    
    for file_path in files_to_process[:10]:  # 最多显示10个文件
        file_size = file_path.stat().st_size
        size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
        table.add_row(file_path.name, size_str, file_path.suffix)
    
    if len(files_to_process) > 10:
        table.add_row("...", "...", "...")
    
    console.print(table)
    
    # 确认处理
    if confirm:
        try:
            if not Confirm.ask(f"是否开始上传这 {len(files_to_process)} 个文件?"):
                console.print("[yellow]操作已取消[/yellow]")
                return
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]操作已取消[/yellow]")
            return
    
    # 处理文件
    processed_count = 0
    error_count = 0
    failed_files = []
    uploaded_files = []  # 收集成功上传的文件信息
    
    # 处理文件，使用正确的服务层方法
    with tqdm(total=len(files_to_process), desc="上传文件", unit="个") as pbar:
        for file_path in files_to_process:
            pbar.set_description(f"上传: {file_path.name}")
            
            try:
                # 为每个文件创建新的数据库会话
                session_gen = get_db_session()
                session = await session_gen.__anext__()
                try:
                    file_info = await _process_single_file(
                        file_path, session, target_topic_id
                    )
                    uploaded_files.append(file_info)
                    processed_count += 1
                finally:
                    await session.close()
                    
            except Exception as e:
                error_count += 1
                error_msg = f"上传失败 {file_path.name}: {str(e)}"
                failed_files.append((file_path.name, str(e)))
                pbar.write(error_msg)
                console.print(f"[red]{error_msg}[/red]")
            
            pbar.update(1)
    
    # 显示详细错误信息
    if failed_files:
        console.print("\n[red]失败文件详情:[/red]")
        error_table = Table(title="处理失败的文件")
        error_table.add_column("文件名", style="yellow")
        error_table.add_column("错误信息", style="red")
        
        for filename, error in failed_files:
            error_table.add_row(filename, error)
        
        console.print(error_table)
    
    console.print(f"\n[bold green]✅ 文件上传完成![/bold green]")
    console.print(f"成功: {processed_count} 个")
    if error_count > 0:
        console.print(f"失败: {error_count} 个")
    
    # 是否开始处理
    if process and processed_count > 0:
        console.print("\n[cyan]🔄 开始异步处理文件...[/cyan]")
        await _submit_file_processing_tasks(uploaded_files)
        console.print("[green]✅ 异步处理任务已提交![/green]")
        console.print("[dim]提示: 使用 'rag system status' 查看任务状态[/dim]")


async def _process_single_file(file_path: Path, session, topic_id: Optional[str]) -> dict:
    """处理单个文件上传并返回文件信息"""
    import uuid
    
    # 生成文件ID
    file_id = str(uuid.uuid4())
    
    # 上传文件到存储服务
    from modules.storage.base import create_storage_service
    storage = create_storage_service()
    
    # 生成存储键（使用文件ID和原始文件名）
    storage_key = f"cli-uploads/{file_id}/{file_path.name}"
    
    # 读取文件内容并上传到存储服务
    content_type = _get_content_type(file_path.suffix)
    with open(file_path, 'rb') as f:
        file_content = f.read()
        await storage.upload_file(storage_key, file_content, content_type)
    
    console.print(f"[green]✓[/green] 已上传文件到存储服务: {file_path.name}")
    
    # 创建文件记录
    file_repo = FileRepository(session)
    
    # 准备文件数据
    file_data = {
        "file_id": file_id,
        "original_name": file_path.name,
        "content_type": _get_content_type(file_path.suffix),
        "file_size": file_path.stat().st_size,
        "status": FileStatus.AVAILABLE,
        "topic_id": topic_id,
        "storage_key": storage_key,  # 使用存储服务中的路径
        "storage_bucket": "cli-uploads",  # CLI专用存储桶
        "upload_path": str(file_path.absolute()),  # 本地文件路径（供参考）
    }
    
    # 创建文件记录
    file_record = await file_repo.create_file(**file_data)
    
    # 提交事务
    await session.commit()
    
    console.print(f"[green]✓[/green] 已创建文件记录: {file_path.name} (ID: {file_id[:8]}...)")
    
    # 返回文件信息供后续任务处理使用
    return {
        "file_id": file_id,
        "file_path": str(file_path),
        "file_name": file_path.name,
        "storage_key": storage_key,  # 使用存储服务中的路径
        "topic_id": topic_id
    }


def _get_content_type(extension: str) -> str:
    """根据文件扩展名获取内容类型"""
    content_types = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    return content_types.get(extension.lower(), 'application/octet-stream')


async def _submit_file_processing_tasks(uploaded_files: list) -> None:
    """提交文件处理异步任务"""
    try:
        # 导入任务服务
        from modules.services.task_service import CeleryTaskService
        from modules.schemas.enums import TaskName
        from config.settings import get_config
        
        config = get_config()
        
        # 初始化任务服务
        task_service = CeleryTaskService(
            broker_url=config.redis.url,
            result_backend=config.redis.url,
            app_name="rag_cli_tasks"
        )
        
        # 初始化任务服务
        await task_service.initialize()
        
        # 为每个文件提交处理任务
        task_ids = []
        for file_info in uploaded_files:
            try:
                # 提交文件上传确认任务，这会触发后续的RAG处理管道
                task_id = await task_service.submit_task(
                    TaskName.FILE_UPLOAD_CONFIRM.value,
                    file_info["file_id"],
                    file_info["storage_key"],
                    filename=file_info["file_name"],
                    topic_id=file_info["topic_id"]
                )
                task_ids.append(task_id)
                console.print(f"[green]✓[/green] 已提交任务: {file_info['file_name']} (Task ID: {task_id[:8]}...)")
                
            except Exception as e:
                console.print(f"[red]✗[/red] 任务提交失败: {file_info['file_name']}, {str(e)}")
        
        # 显示任务ID汇总
        if task_ids:
            console.print(f"\n[bold green]共提交 {len(task_ids)} 个处理任务[/bold green]")
            console.print("[dim]任务ID列表:[/dim]")
            for i, task_id in enumerate(task_ids, 1):
                console.print(f"  {i}. {task_id}")
        
        # 清理任务服务
        await task_service.cleanup()
        
    except Exception as e:
        console.print(f"[red]错误: 任务提交失败: {str(e)}[/red]")
        # 不抛出异常，让文件上传结果仍然显示


@files.command(name='list')
@click.option('--topic-id', help='指定主题ID（默认使用当前主题）')
@click.option('--limit', '-l', default=20, help='显示数量限制')
@click.option('--status', type=click.Choice(['pending', 'processing', 'available', 'failed', 'deleted']), help='按状态过滤')
@error_handler
async def list_files(topic_id, limit, status):
    """列出文件"""
    target_topic_id = topic_id or cli_config.get('current_topic_id')
    if not target_topic_id:
        raise CLIError("未指定主题ID且没有当前主题")
    
    console.print(f"[bold blue]📄 文件列表[/bold blue]")
    
    session_gen = get_db_session()
    session = await session_gen.__anext__()
    
    try:
        file_service = FileService(session, LocalStorage())
        
        # TODO: 实现按主题和状态查询文件
        console.print("[yellow]文件列表功能正在完善中...[/yellow]")
        
    except Exception as e:
        raise CLIError(f"获取文件列表失败: {e}")
    finally:
        if session:
            await session.close()


@files.command(name='status')
@click.argument('file_id')
@error_handler
async def file_status(file_id):
    """查看文件状态"""
    console.print(f"[bold blue]🔍 文件状态: {file_id}[/bold blue]")
    
    # TODO: 实现文件状态查询
    console.print("[yellow]文件状态查询功能正在完善中...[/yellow]")


@files.command(name='delete')
@click.argument('file_id')
@click.option('--force', is_flag=True, help='强制删除，不提示确认')
@error_handler
async def delete_file(file_id, force):
    """删除文件"""
    console.print(f"[bold red]⚠️ 删除文件: {file_id}[/bold red]")
    
    if not force:
        if not Confirm.ask(f"确定要删除文件 {file_id} 吗?"):
            console.print("[yellow]操作已取消[/yellow]")
            return
    
    # TODO: 实现文件删除
    console.print("[yellow]文件删除功能正在完善中...[/yellow]")


# ==================== 系统管理命令组 ====================

@cli.group()
def system():
    """系统管理 - 状态监控、性能指标和维护操作"""
    pass


@system.command(name='status')
@error_handler  
async def system_status():
    """显示系统状态和统计信息"""
    console.print("[bold blue]📊 系统状态[/bold blue]")
    
    # 创建状态表格
    table = Table(title="RAG系统状态")
    table.add_column("组件", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("详情", style="dim")
    
    # 检查数据库
    db = None
    try:
        from modules.database import DatabaseConnection
        db = DatabaseConnection()
        await db.initialize()
        is_healthy = await db.health_check()
        
        if is_healthy:
            table.add_row("数据库", "✅ 连接正常", "PostgreSQL")
        else:
            table.add_row("数据库", "⚠️ 连接异常", "健康检查失败")
    except Exception as e:
        table.add_row("数据库", "❌ 连接失败", str(e))
    finally:
        # 确保清理数据库连接
        if db and hasattr(db, 'pool') and db.pool:
            try:
                await db.pool.close()
            except:
                pass
    
    # 检查向量存储
    if cli_config.get('services_initialized', False):
        # 尝试连接向量存储进行健康检查
        try:
            from modules.vector_store.weaviate_service import WeaviateVectorStore
            from config.settings import get_config
            
            config = get_config()
            weaviate_url = getattr(config, 'weaviate_url', 'http://localhost:8080')
            vector_store = WeaviateVectorStore(url=weaviate_url)
            await vector_store.initialize()
            table.add_row("向量存储", "✅ 连接正常", "Weaviate")
            await vector_store.cleanup()  # 立即清理
        except Exception as e:
            table.add_row("向量存储", "❌ 连接失败", str(e))
    else:
        table.add_row("向量存储", "❌ 未初始化", "请先执行 start 命令")
    
    # 检查AI服务
    if cli_config.get('services_initialized', False):
        # 简单检查配置是否可用
        try:
            from config.settings import get_config
            config = get_config()
            if hasattr(config, 'ai') and hasattr(config.ai.chat.openai, 'api_key'):
                table.add_row("AI服务", "✅ 配置可用", "OpenAI")
            else:
                table.add_row("AI服务", "⚠️ 配置缺失", "需要API密钥")
        except Exception as e:
            table.add_row("AI服务", "❌ 配置错误", str(e))
    else:
        table.add_row("AI服务", "❌ 未初始化", "请先执行 start 命令")
    
    console.print(table)
    
    # 显示当前配置
    console.print(f"\n[bold cyan]当前主题:[/bold cyan] {cli_config['current_topic_name']}")
    console.print(f"[bold cyan]主题ID:[/bold cyan] {cli_config['current_topic_id']}")
    
    # TODO: 显示系统统计信息
    console.print("\n[dim]系统统计信息正在完善中...[/dim]")


@system.command(name='health')
@error_handler
async def health_check():
    """执行系统健康检查"""
    console.print("[bold blue]🩺 系统健康检查[/bold blue]")
    
    with Status("正在执行健康检查...", console=console) as status:
        health_results = {
            '数据库': False,
            '向量存储': False,
            'AI服务': False,
            '缓存服务': False
        }
        
        # 检查数据库
        status.update("检查数据库连接...")
        try:
            from modules.database import DatabaseConnection
            db = DatabaseConnection()
            await db.initialize()
            health_results['数据库'] = await db.health_check()
            if db and hasattr(db, 'pool') and db.pool:
                await db.pool.close()
        except Exception:
            pass
        
        # 检查向量存储
        status.update("检查向量存储...")
        try:
            from modules.vector_store.weaviate_service import WeaviateVectorStore
            from config.settings import get_config
            config = get_config()
            weaviate_url = getattr(config, 'weaviate_url', 'http://localhost:8080')
            vector_store = WeaviateVectorStore(url=weaviate_url)
            await vector_store.initialize()
            health_results['向量存储'] = True
            await vector_store.cleanup()
        except Exception:
            pass
        
        # 检查AI服务
        status.update("检查AI服务...")
        try:
            from config.settings import get_config
            config = get_config()
            if hasattr(config, 'ai') and hasattr(config.ai.chat.openai, 'api_key'):
                health_results['AI服务'] = True
        except Exception:
            pass
    
    # 显示结果
    console.print("\n[bold green]📊 健康检查结果:[/bold green]")
    
    for service, is_healthy in health_results.items():
        status_icon = "✅" if is_healthy else "❌"
        status_color = "green" if is_healthy else "red"
        console.print(f"  {status_icon} {service}: [{status_color}]{'PASS' if is_healthy else 'FAIL'}[/{status_color}]")
    
    overall_health = all(health_results.values())
    health_emoji = "🚀" if overall_health else "⚠️"
    health_status = "健康" if overall_health else "异常"
    health_color = "green" if overall_health else "red"
    
    console.print(f"\n{health_emoji} [bold {health_color}]系统整体状态: {health_status}[/bold {health_color}]")


@system.command(name='cleanup')
@click.option('--confirm/--no-confirm', default=True, help='是否显示确认提示')
@error_handler
async def cleanup_system(confirm):
    """清理系统临时数据和缓存"""
    console.print("[bold yellow]🧽 系统清理[/bold yellow]")
    
    if confirm:
        if not Confirm.ask("确定要清理系统临时数据吗?"):
            console.print("[yellow]操作已取消[/yellow]")
            return
    
    # TODO: 实现系统清理功能
    console.print("[yellow]系统清理功能正在完善中...[/yellow]")


@system.command(name='backup')
@click.option('--output', '-o', help='备份文件输出路径')
@error_handler
async def backup_system(output):
    """创建系统数据备份"""
    console.print("[bold blue]💾 系统备份[/bold blue]")
    
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"rag_backup_{timestamp}.sql"
    
    # TODO: 实现数据库备份功能
    console.print(f"[yellow]备份功能正在完善中...目标文件: {output}[/yellow]")


# ==================== 智能对话命令 ====================

@cli.command()
@click.option('--topic-id', help='指定主题ID（默认使用当前主题）')
@click.option('--model', default='gpt-4', help='指定使用的AI模型')
@click.option('--context-limit', default=5, help='最大检索上下文数量')
@click.option('--no-context', is_flag=True, help='禁用上下文检索')
@error_handler
async def chat(topic_id, model, context_limit, no_context):
    """开始智能对话"""
    # 获取目标主题
    target_topic_id = topic_id or cli_config.get('current_topic_id')
    if not target_topic_id:
        raise CLIError("未指定主题ID且没有当前主题，请先创建或切换主题")
    
    # 初始化RAG集成聊天服务
    try:
        chat_service = await create_rag_integrated_chat_service(
            pipeline_type="adaptive",
            enable_routing=True
        )
    except Exception as e:
        raise CLIError(f"增强聊天服务初始化失败: {e}")
    
    topic_name = cli_config.get('current_topic_name', target_topic_id)
    
    # 显示聊天信息
    chat_panel = Panel.fit(
        f"[bold cyan]智能对话模式[/bold cyan]\n\n"
        f"当前主题: {topic_name}\n"
        f"AI模型: {model}\n"
        f"上下文检索: {'OFF' if no_context else f'ON (max {context_limit})'}\n\n"
        f"[dim]输入 '/help' 查看命令帮助\n"
        f"输入 '/exit' 或 '/quit' 退出聊天[/dim]",
        title="💬 聊天界面",
        border_style="green"
    )
    console.print(chat_panel)
    
    conversation_id = None
    
    while True:
        try:
            # 获取用户输入
            user_input = Prompt.ask("\n[cyan]您[/cyan]").strip()
            
            if not user_input:
                continue
            
            # 处理命令
            if user_input.startswith('/'):
                if user_input.lower() in ['/exit', '/quit']:
                    console.print("[yellow]退出聊天模式[/yellow]")
                    break
                elif user_input.lower() in ['/clear', '/清除']:
                    conversation_id = None
                    console.print("[yellow]对话历史已清除[/yellow]")
                    continue
                elif user_input.lower() == '/help':
                    _show_chat_help()
                    continue
                elif user_input.lower() == '/history':
                    console.print("[yellow]对话历史功能正在完善中...[/yellow]")
                    continue
                else:
                    console.print(f"[red]未知命令: {user_input}[/red]")
                    continue
            
            # 退出命令（兼容老版本）
            if user_input.lower() in ['exit', 'quit', '退出']:
                console.print("[yellow]退出聊天模式[/yellow]")
                break
            
            # 显示思考状态
            with console.status("[bold green]AI思考中...[/bold green]"):
                # 构建聊天请求
                chat_request = ChatRequest(
                    message=user_input,
                    topic_id=target_topic_id,
                    conversation_id=conversation_id,
                    include_context=not no_context,
                    max_results=context_limit,
                )
                
                # 调用聊天服务
                response = await chat_service.chat(chat_request)
                conversation_id = response.conversation_id
            
            # 显示AI回复
            console.print(f"\n[bold blue]AI:[/bold blue] {response.content}")
            
            # 显示检索上下文（可选）
            if response.retrieved_contexts and not no_context:
                console.print(f"\n[dim]🔍 检索到 {len(response.retrieved_contexts)} 个相关上下文[/dim]")
                # TODO: 显示详细的上下文信息
                
        except KeyboardInterrupt:
            console.print("\n[yellow]退出聊天模式[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]聊天错误: {e}[/red]")
    
    # 聊天结束时清理资源
    try:
        await chat_service.close()
    except Exception:
        pass


def _show_chat_help():
    """显示聊天帮助信息"""
    help_panel = Panel.fit(
        "[bold cyan]聊天命令帮助[/bold cyan]\n\n"
        "[green]/help[/green]     - 显示此帮助信息\n"
        "[green]/clear[/green]    - 清除对话历史\n"
        "[green]/history[/green]  - 查看对话历史\n"
        "[green]/exit[/green]     - 退出聊天模式\n"
        "[green]/quit[/green]     - 退出聊天模式\n\n"
        "[dim]直接输入消息开始对话[/dim]",
        title="❓ 帮助",
        border_style="blue"
    )
    console.print(help_panel)


# ==================== 数据管理命令 ====================

@cli.command(name='clear')
@click.option('--confirm/--no-confirm', default=True, help='是否显示确认提示')
@error_handler
async def clear_data(confirm):
    """清理CLI创建的测试数据"""
    console.print("[bold yellow]⚠️  清理数据[/bold yellow]")
    
    if confirm:
        if not Confirm.ask("这将删除所有CLI创建的测试数据，是否继续?"):
            console.print("[yellow]操作已取消[/yellow]")
            return
    
    deleted_files = 0
    
    try:
        # 简化清理逻辑，暂时只显示提示信息
        console.print("[yellow]⏳ 清理功能正在完善中...[/yellow]")
        console.print(f"[green]✅ 已清理 {deleted_files} 个文件记录[/green]")
        
    except Exception as e:
        raise CLIError(f"清理失败: {e}")


# ==================== 兼容性命令 ====================

@cli.command(name='start', hidden=True)
@error_handler
async def start_compat():
    """兼容性命令，重定向到 init"""
    console.print("[yellow]⚠️  `start` 命令已弃用，请使用 `init` 命令[/yellow]")
    console.print("[cyan]正在自动调用 `init` 命令...[/cyan]\n")
    await init_system()


@cli.command(name='load', hidden=True)
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@error_handler
async def load_compat(directory):
    """兼容性命令，重定向到 files upload"""
    console.print("[yellow]⚠️  `load` 命令已弃用，请使用 `files upload` 命令[/yellow]")
    console.print("[cyan]正在自动调用 `files upload` 命令...[/cyan]\n")
    # 调用新的upload命令
    await upload_files(directory, None, True, True, True)


@cli.command(name='status', hidden=True)
@error_handler
async def status_compat():
    """兼容性命令，重定向到 system status"""
    console.print("[yellow]⚠️  `status` 命令已弃用，请使用 `system status` 命令[/yellow]")
    console.print("[cyan]正在自动调用 `system status` 命令...[/cyan]\n")
    await system_status()


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    cli()