#!/usr/bin/env python3
"""
Terminal UI for RAG Question Answering
Provides interactive command-line interface for RAG functionality
"""

import logging
import sys
from typing import List, Dict, Any, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from ..engine.rag_engine import RAGEngine

logger = logging.getLogger(__name__)

class TerminalUI:
    """Interactive terminal UI for RAG question answering"""
    
    def __init__(self, config_path: str = "config.yaml"):
        if not RICH_AVAILABLE:
            raise ImportError("rich library is required for terminal UI. Install with: pip install rich")
        
        self.console = Console()
        self.rag_engine = None
        self.config_path = config_path
        self.selected_keywords = []
        self.index_built = False
        
        # Initialize RAG engine
        self._init_rag_engine()
    
    def _init_rag_engine(self):
        """Initialize RAG engine with progress display"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Initializing RAG engine...", total=None)
            
            try:
                self.rag_engine = RAGEngine(self.config_path)
                progress.update(task, description="✅ RAG engine ready!")
                
            except Exception as e:
                progress.update(task, description=f"❌ Failed to initialize: {e}")
                self.console.print(f"[red]Error initializing RAG engine: {e}[/red]")
                sys.exit(1)
    
    def run(self):
        """Main UI loop"""
        self._show_welcome()
        
        while True:
            try:
                self._show_main_menu()
                choice = self._get_menu_choice()
                
                if choice == "1":
                    self._keyword_selection_flow()
                elif choice == "2":
                    self._question_answering_flow()
                elif choice == "3":
                    self._search_papers_flow()
                elif choice == "4":
                    self._show_system_status()
                elif choice == "5":
                    self._show_settings()
                elif choice == "q":
                    self._quit()
                    break
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
                    
            except KeyboardInterrupt:
                self.console.print("\\n[yellow]Interrupted by user[/yellow]")
                if Confirm.ask("Do you want to quit?"):
                    break
            except Exception as e:
                self.console.print(f"[red]An error occurred: {e}[/red]")
                logger.error(f"UI error: {e}")
    
    def _show_welcome(self):
        """Show welcome screen"""
        welcome_text = """
# 🤖 ArXiv RAG Question Answering System

Welcome to the intelligent question-answering system for ArXiv papers!

## Features:
- 🔍 **Smart Keyword Selection**: Choose from your collected papers
- 🧠 **AI-Powered Answers**: Get detailed answers with source citations  
- 📚 **Paper Search**: Find relevant papers by content similarity
- ⚡ **Fast Retrieval**: Vector-based semantic search
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="RAG Q&A System",
            border_style="blue"
        ))
    
    def _show_main_menu(self):
        """Show main menu options"""
        self.console.print("\\n" + "="*60)
        
        # Show current status
        status_text = ""
        if self.selected_keywords:
            status_text += f"📋 Keywords: {', '.join(self.selected_keywords[:3])}{'...' if len(self.selected_keywords) > 3 else ''}\\n"
        if self.index_built:
            status_text += "✅ Index built and ready for questions\\n"
        else:
            status_text += "⚠️  Index not built - select keywords first\\n"
        
        if status_text:
            self.console.print(Panel(status_text.strip(), title="Current Status", border_style="cyan"))
        
        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_column(style="cyan", width=3)
        menu_table.add_column(style="white")
        
        menu_table.add_row("1.", "🔍 Select Keywords & Build Index")
        menu_table.add_row("2.", "💬 Ask Questions" + (" [dim](requires index)[/dim]" if not self.index_built else ""))
        menu_table.add_row("3.", "📚 Search Papers")
        menu_table.add_row("4.", "📊 System Status")
        menu_table.add_row("5.", "⚙️  Settings")
        menu_table.add_row("q.", "🚪 Quit")
        
        self.console.print(Panel(menu_table, title="Main Menu", border_style="blue"))
    
    def _get_menu_choice(self) -> str:
        """Get user menu choice"""
        return Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "q"], default="1")
    
    def _keyword_selection_flow(self):
        """Handle keyword selection and index building"""
        self.console.print("\\n[bold blue]📋 Keyword Selection & Index Building[/bold blue]")
        
        # Get available keywords
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Loading keywords from database...", total=None)
            keywords = self.rag_engine.get_available_keywords()
        
        if not keywords:
            self.console.print("[red]No keywords found in database. Please collect some papers first.[/red]")
            return
        
        # Display keywords in a nice table
        self._display_keywords(keywords)
        
        # Get user selection
        selected = self._select_keywords(keywords)
        
        if not selected:
            self.console.print("[yellow]No keywords selected.[/yellow]")
            return
        
        self.selected_keywords = selected
        
        # Build index
        self._build_index()
    
    def _display_keywords(self, keywords: List[Dict[str, Any]]):
        """Display available keywords in a table"""
        table = Table(title="Available Keywords", show_lines=True)
        table.add_column("Keyword", style="cyan", no_wrap=True)
        table.add_column("Papers", justify="right", style="magenta")
        table.add_column("Example Papers", style="dim")
        
        # Limit display to reasonable number
        display_keywords = keywords[:20]  # Show top 20 keywords
        
        for kw_info in display_keywords:
            keyword = kw_info['keyword']
            count = kw_info['count']
            
            # Get example titles
            examples = kw_info.get('examples', [])
            example_text = ""
            if examples:
                example_titles = [ex['title'][:40] + "..." if len(ex['title']) > 40 else ex['title'] 
                                for ex in examples[:2]]
                example_text = "\\n".join(example_titles)
            
            table.add_row(keyword, str(count), example_text)
        
        if len(keywords) > 20:
            table.caption = f"Showing top 20 of {len(keywords)} keywords"
        
        self.console.print(table)
    
    def _select_keywords(self, keywords: List[Dict[str, Any]]) -> List[str]:
        """Interactive keyword selection"""
        self.console.print("\\n[bold]Select keywords for question answering:[/bold]")
        self.console.print("[dim]You can enter multiple keywords separated by commas, or keyword numbers.[/dim]")
        
        # Create lookup maps
        keyword_map = {str(i+1): kw['keyword'] for i, kw in enumerate(keywords[:20])}
        name_map = {kw['keyword']: kw['keyword'] for kw in keywords}
        
        while True:
            user_input = Prompt.ask(
                "Enter keywords or numbers",
                default="",
                show_default=False
            )
            
            if not user_input.strip():
                return []
            
            selected = []
            parts = [part.strip() for part in user_input.split(',')]
            
            for part in parts:
                if part.isdigit() and part in keyword_map:
                    # User entered a number
                    selected.append(keyword_map[part])
                elif part in name_map:
                    # User entered keyword name
                    selected.append(part)
                else:
                    # Try partial matching
                    matches = [kw['keyword'] for kw in keywords 
                             if part.lower() in kw['keyword'].lower()]
                    if matches:
                        selected.extend(matches[:1])  # Add first match
                    else:
                        self.console.print(f"[yellow]Unknown keyword: {part}[/yellow]")
            
            if selected:
                # Remove duplicates and confirm
                selected = list(set(selected))
                self.console.print(f"\\n[green]Selected keywords:[/green] {', '.join(selected)}")
                
                if Confirm.ask("Proceed with these keywords?"):
                    return selected
            else:
                self.console.print("[red]No valid keywords selected.[/red]")
            
            if not Confirm.ask("Try again?"):
                return []
    
    def _build_index(self):
        """Build vector index for selected keywords"""
        self.console.print(f"\\n[bold blue]🏗️  Building index for: {', '.join(self.selected_keywords)}[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Building vector index...", total=None)
            
            results = self.rag_engine.build_index_for_keywords(
                self.selected_keywords,
                force_reindex=False
            )
        
        if results['success']:
            self.index_built = True
            self.console.print("\\n[green]✅ Index built successfully![/green]")
            
            # Show indexing statistics
            stats_table = Table(title="Indexing Results", show_header=False)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="white")
            
            stats_table.add_row("Papers Found", str(results.get('papers_found', 0)))
            stats_table.add_row("Papers Processed", str(results.get('processed_papers', 0)))
            stats_table.add_row("Total Chunks", str(results.get('total_chunks', 0)))
            stats_table.add_row("Skipped Papers", str(results.get('skipped_papers', 0)))
            
            self.console.print(stats_table)
            
        else:
            self.console.print(f"[red]❌ Failed to build index: {results.get('error', 'Unknown error')}[/red]")
    
    def _question_answering_flow(self):
        """Handle question answering interaction"""
        if not self.index_built:
            self.console.print("[red]Please build an index first by selecting keywords.[/red]")
            return
        
        self.console.print("\\n[bold blue]💬 Question Answering[/bold blue]")
        self.console.print(f"[dim]Index contains papers for: {', '.join(self.selected_keywords)}[/dim]")
        self.console.print("[dim]Type 'quit' to return to main menu[/dim]\\n")
        
        while True:
            question = Prompt.ask("❓ Your question").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            # Process question
            self._process_question(question)
            
            self.console.print("\\n" + "-"*60 + "\\n")
    
    def _process_question(self, question: str):
        """Process a single question and display results"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Searching for relevant information...", total=None)
            
            results = self.rag_engine.ask_question(question)
            
            progress.update(task, description="✅ Answer generated!")
        
        if results['success']:
            self._display_answer(results)
        else:
            self.console.print(f"[red]❌ {results.get('answer', 'Failed to generate answer')}[/red]")
    
    def _display_answer(self, results: Dict[str, Any]):
        """Display question answering results"""
        # Main answer
        answer_panel = Panel(
            Markdown(results['answer']),
            title=f"🤖 Answer",
            border_style="green"
        )
        self.console.print(answer_panel)
        
        # Sources
        sources = results.get('sources', [])
        if sources:
            self.console.print("\\n[bold blue]📚 Sources:[/bold blue]")
            
            sources_table = Table(show_header=True, header_style="bold cyan")
            sources_table.add_column("ArXiv ID", style="cyan")
            sources_table.add_column("Title", style="white")
            sources_table.add_column("Similarity", justify="right", style="magenta")
            
            for source in sources:
                similarity = f"{source.get('similarity', 0):.2%}"
                title = source.get('title', 'Unknown Title')
                if len(title) > 50:
                    title = title[:47] + "..."
                
                sources_table.add_row(
                    source.get('arxiv_id', 'Unknown'),
                    title,
                    similarity
                )
            
            self.console.print(sources_table)
        
        # Retrieval statistics
        retrieval_info = results.get('retrieval_info', {})
        if retrieval_info:
            stats_text = (
                f"📊 Retrieved {retrieval_info.get('chunks_used', 0)} chunks "
                f"(avg similarity: {retrieval_info.get('avg_similarity', 0):.1%})"
            )
            self.console.print(f"[dim]{stats_text}[/dim]")
    
    def _search_papers_flow(self):
        """Handle paper search functionality"""
        self.console.print("\\n[bold blue]📚 Paper Search[/bold blue]")
        self.console.print("[dim]Search for papers by content similarity[/dim]")
        self.console.print("[dim]Type 'quit' to return to main menu[/dim]\\n")
        
        while True:
            query = Prompt.ask("🔍 Search query").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # Search papers
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Searching papers...", total=None)
                results = self.rag_engine.search_papers(query, top_k=10)
            
            if results:
                self._display_search_results(results)
            else:
                self.console.print("[yellow]No results found.[/yellow]")
            
            self.console.print("\\n" + "-"*60 + "\\n")
    
    def _display_search_results(self, results: List[Dict[str, Any]]):
        """Display paper search results"""
        self.console.print(f"\\n[green]Found {len(results)} results:[/green]\\n")
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            
            title = metadata.get('title', 'Unknown Title')
            arxiv_id = metadata.get('source_doc', 'Unknown ID')
            similarity = result.get('similarity', 0)
            content = result.get('document', '')[:200] + "..."
            
            result_panel = Panel(
                f"[bold]{title}[/bold]\\n"
                f"[cyan]ArXiv ID:[/cyan] {arxiv_id}\\n"
                f"[magenta]Similarity:[/magenta] {similarity:.1%}\\n\\n"
                f"[dim]{content}[/dim]",
                title=f"Result {i}",
                border_style="blue"
            )
            self.console.print(result_panel)
    
    def _show_system_status(self):
        """Display system status information"""
        self.console.print("\\n[bold blue]📊 System Status[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Checking system status...", total=None)
            status = self.rag_engine.get_system_status()
        
        # Create status table
        status_table = Table(title="Component Status", show_header=True)
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="white")
        status_table.add_column("Details", style="dim")
        
        for component, info in status.items():
            component_status = info.get('status', 'unknown')
            
            # Status indicator
            if component_status == 'active':
                status_indicator = "[green]✅ Active[/green]"
            elif component_status == 'error':
                status_indicator = "[red]❌ Error[/red]"
            else:
                status_indicator = "[yellow]⚠️ Unknown[/yellow]"
            
            # Details
            details = []
            for key, value in info.items():
                if key != 'status':
                    details.append(f"{key}: {value}")
            
            details_text = "\\n".join(details[:3])  # Show first 3 details
            
            status_table.add_row(component.replace('_', ' ').title(), status_indicator, details_text)
        
        self.console.print(status_table)
    
    def _show_settings(self):
        """Display current settings"""
        self.console.print("\\n[bold blue]⚙️ Current Settings[/bold blue]")
        
        config = self.rag_engine.rag_config
        
        # Create settings table
        settings_table = Table(title="RAG Configuration", show_lines=True)
        settings_table.add_column("Setting", style="cyan")
        settings_table.add_column("Value", style="white")
        
        # Embedding settings
        embedding_config = config.get('embeddings', {})
        settings_table.add_row("Embedding Model", embedding_config.get('model', 'Unknown'))
        settings_table.add_row("Device", embedding_config.get('device', 'Unknown'))
        
        # LLM settings
        llm_config = config.get('llm', {})
        settings_table.add_row("LLM Provider", llm_config.get('provider', 'Unknown'))
        settings_table.add_row("LLM Model", llm_config.get('model', 'Unknown'))
        
        # Retrieval settings
        retrieval_config = config.get('retrieval', {})
        settings_table.add_row("Top K Results", str(retrieval_config.get('top_k', 'Unknown')))
        settings_table.add_row("Similarity Threshold", str(retrieval_config.get('similarity_threshold', 'Unknown')))
        
        # Vector DB settings
        vector_config = config.get('vector_db', {})
        settings_table.add_row("Vector DB Type", vector_config.get('type', 'Unknown'))
        settings_table.add_row("Collection Name", vector_config.get('collection_name', 'Unknown'))
        
        self.console.print(settings_table)
    
    def _quit(self):
        """Handle quit operation"""
        self.console.print("\\n[cyan]Thank you for using the RAG Q&A system! 👋[/cyan]")