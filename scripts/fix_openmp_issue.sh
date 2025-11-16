#!/bin/bash
# Script to fix OpenMP conflict on macOS
# This script provides multiple solutions for the OpenMP library conflict

echo "🔧 OpenMP Conflict Fix Script"
echo "=============================="
echo ""

# Solution 1: Set environment variable permanently
echo "Solution 1: Add to shell profile (recommended for development)"
echo "------------------------------------------------"
echo "Run one of these commands based on your shell:"
echo ""
echo "For Zsh (default on macOS):"
echo "  echo 'export KMP_DUPLICATE_LIB_OK=TRUE' >> ~/.zshrc"
echo "  source ~/.zshrc"
echo ""
echo "For Bash:"
echo "  echo 'export KMP_DUPLICATE_LIB_OK=TRUE' >> ~/.bashrc"
echo "  source ~/.bashrc"
echo ""

# Solution 2: Reinstall PyTorch with conda
echo "Solution 2: Use Conda environment (most stable)"
echo "------------------------------------------------"
echo "1. Install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
echo "2. Create new environment:"
echo "   conda create -n rag-env python=3.11"
echo "   conda activate rag-env"
echo "3. Install PyTorch via conda:"
echo "   conda install pytorch torchvision torchaudio -c pytorch"
echo "4. Install other dependencies:"
echo "   pip install -r requirements.txt"
echo ""

# Solution 3: Reinstall with specific torch version
echo "Solution 3: Reinstall PyTorch CPU-only (lighter, more stable)"
echo "------------------------------------------------"
echo "pip uninstall torch"
echo "pip install torch --index-url https://download.pytorch.org/whl/cpu"
echo ""

# Solution 4: Check current OpenMP libraries
echo "Solution 4: Diagnostic - Check OpenMP libraries"
echo "------------------------------------------------"
echo "Find OpenMP libraries in your Python environment:"
echo "  find \$(python -c 'import sys; print(sys.prefix)') -name 'libomp*.dylib'"
echo ""

# Solution 5: Quick fix for current session
echo "Solution 5: Quick fix for current session"
echo "------------------------------------------------"
echo "export KMP_DUPLICATE_LIB_OK=TRUE"
echo ""

echo "=============================="
echo "💡 Recommendation:"
echo "   - For development: Use Solution 1 (add to shell profile)"
echo "   - For production: Use Solution 2 (Conda) or ensure single OpenMP"
echo "   - For quick test: Code already sets this automatically"
echo ""

