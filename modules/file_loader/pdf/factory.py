"""
PDF strategy factory for managing PDF loading strategies.

This module provides a factory pattern implementation for registering,
managing, and selecting PDF processing strategies based on availability,
priority, and configuration preferences.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Union, Any

from config.file_loader_config import PDFLoaderConfig
from modules.file_loader.pdf.base import IPDFLoadStrategy, PDFStrategyError

logger = logging.getLogger(__name__)


class PDFStrategyFactory:
    """
    Factory class for managing PDF loading strategies.
    
    This factory manages registration, retrieval, and selection of PDF
    processing strategies. It supports automatic strategy selection based
    on availability, priority, and configuration preferences.
    """
    
    def __init__(self, config: Optional[PDFLoaderConfig] = None):
        """
        Initialize PDF strategy factory.
        
        Args:
            config: PDF loader configuration. If None, uses default config.
        """
        self.config = config or PDFLoaderConfig()
        self._strategies: Dict[str, Union[IPDFLoadStrategy, Type[IPDFLoadStrategy]]] = {}
        self._strategy_instances: Dict[str, IPDFLoadStrategy] = {}
        
        logger.debug(f"PDFStrategyFactory initialized with {len(self._strategies)} strategies")
    
    def register_strategy(
        self, 
        name: str, 
        strategy: Union[IPDFLoadStrategy, Type[IPDFLoadStrategy]]
    ) -> None:
        """
        Register a PDF loading strategy.
        
        Args:
            name: Unique name for the strategy
            strategy: Strategy instance or class
        """
        if name in self._strategies:
            logger.warning(f"Strategy '{name}' already registered, overriding")
        
        self._strategies[name] = strategy
        
        # Clear cached instance if exists
        if name in self._strategy_instances:
            del self._strategy_instances[name]
            
        logger.info(f"Registered PDF strategy: {name}")
    
    def unregister_strategy(self, name: str) -> bool:
        """
        Unregister a PDF loading strategy.
        
        Args:
            name: Name of strategy to remove
            
        Returns:
            bool: True if strategy was removed, False if not found
        """
        if name not in self._strategies:
            return False
            
        del self._strategies[name]
        
        if name in self._strategy_instances:
            del self._strategy_instances[name]
            
        logger.info(f"Unregistered PDF strategy: {name}")
        return True
    
    def is_registered(self, name: str) -> bool:
        """
        Check if a strategy is registered.
        
        Args:
            name: Strategy name to check
            
        Returns:
            bool: True if strategy is registered
        """
        return name in self._strategies
    
    def get_registered_strategies(self) -> List[str]:
        """
        Get list of all registered strategy names.
        
        Returns:
            List[str]: List of registered strategy names
        """
        return list(self._strategies.keys())
    
    def get_strategy(self, name: str) -> IPDFLoadStrategy:
        """
        Get a strategy instance by name.
        
        Args:
            name: Name of the strategy
            
        Returns:
            IPDFLoadStrategy: Strategy instance
            
        Raises:
            PDFStrategyError: If strategy is not found or cannot be instantiated
        """
        if name not in self._strategies:
            raise PDFStrategyError(f"Strategy '{name}' is not registered")
        
        # Return cached instance if available
        if name in self._strategy_instances:
            return self._strategy_instances[name]
        
        try:
            strategy_def = self._strategies[name]
            
            # If it's a class, instantiate it
            if isinstance(strategy_def, type):
                strategy_config = self.config.get_strategy_config(name)
                instance = strategy_def(config=strategy_config)
            else:
                # It's already an instance
                instance = strategy_def
            
            # Cache the instance
            self._strategy_instances[name] = instance
            
            return instance
            
        except Exception as e:
            raise PDFStrategyError(
                f"Failed to instantiate strategy '{name}': {str(e)}",
                strategy_name=name,
                original_error=e
            )
    
    def get_strategies_by_priority(self) -> List[IPDFLoadStrategy]:
        """
        Get all registered strategies ordered by priority.
        
        Returns:
            List[IPDFLoadStrategy]: Strategies ordered by priority (highest first)
        """
        strategy_priorities = []
        
        for name in self._strategies.keys():
            try:
                instance = self.get_strategy(name)
                strategy_priorities.append((instance, instance.priority))
            except Exception as e:
                logger.warning(f"Failed to get strategy '{name}' for priority ordering: {e}")
                continue
        
        # Sort by priority (lower number = higher priority)
        strategy_priorities.sort(key=lambda x: x[1])
        
        return [strategy for strategy, _ in strategy_priorities]
    
    async def select_best_strategy(
        self, 
        file_path: Path, 
        config: Optional[PDFLoaderConfig] = None
    ) -> IPDFLoadStrategy:
        """
        Select the best available strategy for a given PDF file.
        
        Args:
            file_path: Path to the PDF file
            config: Optional configuration override
            
        Returns:
            IPDFLoadStrategy: Best available strategy
            
        Raises:
            PDFStrategyError: If no suitable strategy is available
        """
        effective_config = config or self.config
        
        # If a specific strategy is requested and not "auto"
        if effective_config.default_strategy != "auto":
            if self.is_registered(effective_config.default_strategy):
                try:
                    strategy = self.get_strategy(effective_config.default_strategy)
                    if await strategy.can_handle(file_path):
                        logger.info(f"Using configured strategy: {effective_config.default_strategy}")
                        return strategy
                    else:
                        logger.warning(
                            f"Configured strategy '{effective_config.default_strategy}' "
                            f"cannot handle file: {file_path}"
                        )
                except Exception as e:
                    logger.warning(
                        f"Configured strategy '{effective_config.default_strategy}' failed: {e}"
                    )
            else:
                logger.warning(f"Configured strategy '{effective_config.default_strategy}' not registered")
        
        # Try strategies by priority
        strategies = self.get_strategies_by_priority()
        
        if not strategies:
            raise PDFStrategyError(
                "No PDF strategies are registered",
                file_path=str(file_path)
            )
        
        for strategy in strategies:
            try:
                if await strategy.can_handle(file_path):
                    logger.info(f"Selected strategy by priority: {strategy.strategy_name}")
                    return strategy
            except Exception as e:
                logger.warning(
                    f"Strategy '{strategy.strategy_name}' failed availability check: {e}"
                )
                continue
        
        # No suitable strategy found
        available_strategies = [s.strategy_name for s in strategies]
        raise PDFStrategyError(
            f"No suitable strategy found for file: {file_path}. "
            f"Available strategies: {available_strategies}",
            file_path=str(file_path)
        )
    
    async def select_strategy_with_fallback(
        self, 
        file_path: Path,
        preferred_strategy: Optional[str] = None,
        config: Optional[PDFLoaderConfig] = None
    ) -> List[IPDFLoadStrategy]:
        """
        Select strategy with fallback options.
        
        Args:
            file_path: Path to the PDF file
            preferred_strategy: Preferred strategy name
            config: Optional configuration override
            
        Returns:
            List[IPDFLoadStrategy]: Primary strategy and fallback options
        """
        effective_config = config or self.config
        fallback_strategies = []
        
        # Try preferred strategy first
        if preferred_strategy and self.is_registered(preferred_strategy):
            try:
                strategy = self.get_strategy(preferred_strategy)
                if await strategy.can_handle(file_path):
                    fallback_strategies.append(strategy)
            except Exception as e:
                logger.warning(f"Preferred strategy '{preferred_strategy}' failed: {e}")
        
        # Add other strategies by priority
        for strategy in self.get_strategies_by_priority():
            if strategy.strategy_name == preferred_strategy:
                continue  # Already added or failed
                
            try:
                if await strategy.can_handle(file_path):
                    fallback_strategies.append(strategy)
            except Exception as e:
                logger.warning(
                    f"Strategy '{strategy.strategy_name}' failed availability check: {e}"
                )
                continue
        
        if not fallback_strategies:
            raise PDFStrategyError(
                f"No suitable strategies found for file: {file_path}",
                file_path=str(file_path)
            )
        
        return fallback_strategies
    
    def clear_strategies(self) -> None:
        """
        Clear all registered strategies.
        
        This is primarily useful for testing.
        """
        self._strategies.clear()
        self._strategy_instances.clear()
        logger.debug("Cleared all PDF strategies")
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """
        Get factory statistics and information.
        
        Returns:
            Dict[str, Any]: Factory statistics
        """
        return {
            "total_strategies": len(self._strategies),
            "cached_instances": len(self._strategy_instances),
            "registered_strategies": list(self._strategies.keys()),
            "default_strategy": self.config.default_strategy,
            "fallback_enabled": self.config.enable_fallback
        }


# Global factory instance (singleton pattern)
_global_factory: Optional[PDFStrategyFactory] = None


def get_pdf_strategy_factory() -> PDFStrategyFactory:
    """
    Get the global PDF strategy factory instance.
    
    Returns:
        PDFStrategyFactory: Global factory instance
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = PDFStrategyFactory()
    return _global_factory


def register_pdf_strategy(name: str):
    """
    Decorator for registering PDF strategies.
    
    Args:
        name: Unique name for the strategy
        
    Returns:
        Decorator function
    """
    def decorator(strategy_class: Type[IPDFLoadStrategy]):
        """Register the strategy class."""
        factory = get_pdf_strategy_factory()
        factory.register_strategy(name, strategy_class)
        
        logger.info(f"Auto-registered PDF strategy '{name}' via decorator")
        
        return strategy_class
    
    return decorator


# Convenience functions
async def get_best_pdf_strategy(
    file_path: Union[str, Path],
    config: Optional[PDFLoaderConfig] = None
) -> IPDFLoadStrategy:
    """
    Convenience function to get the best PDF strategy for a file.
    
    Args:
        file_path: Path to the PDF file
        config: Optional configuration
        
    Returns:
        IPDFLoadStrategy: Best available strategy
    """
    factory = get_pdf_strategy_factory()
    return await factory.select_best_strategy(Path(file_path), config)


def list_available_strategies() -> List[str]:
    """
    Convenience function to list all available PDF strategies.
    
    Returns:
        List[str]: List of available strategy names
    """
    factory = get_pdf_strategy_factory()
    return factory.get_registered_strategies()