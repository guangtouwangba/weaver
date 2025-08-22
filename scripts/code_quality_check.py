#!/usr/bin/env python3
"""
Code Quality Check Script

Comprehensive code quality analysis and automated fixes for the RAG system.
This script provides:
- Linting analysis with detailed reporting
- Automated fixes for common issues  
- Progress tracking and reporting
- Best practice recommendations
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def run_command(command: str, capture_output: bool = True) -> Tuple[int, str, str]:
    """
    Execute a shell command and return the result.
    
    Args:
        command: Shell command to execute
        capture_output: Whether to capture stdout/stderr
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command.split(),
            capture_output=capture_output,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_linting() -> Dict[str, int]:
    """
    Run flake8 linting and return categorized issue counts.
    
    Returns:
        Dictionary with issue categories and counts
    """
    print("🔍 Running flake8 linting analysis...")
    
    # Run flake8 with detailed output
    cmd = "python -m flake8 modules/ --count --statistics --max-line-length=100"
    return_code, stdout, stderr = run_command(cmd)
    
    if return_code != 0:
        print(f"⚠️ Linting found issues:\n{stdout}")
    else:
        print("✅ No linting issues found!")
    
    # Parse results
    issues = {}
    if stdout:
        for line in stdout.split('\n'):
            if line.strip() and not line.startswith('modules/'):
                parts = line.strip().split()
                if len(parts) >= 2:
                    count, code = parts[0], parts[1]
                    try:
                        issues[code] = int(count)
                    except ValueError:
                        pass
    
    return issues


def apply_automatic_fixes() -> bool:
    """
    Apply automatic formatting and fixes.
    
    Returns:
        True if successful, False otherwise
    """
    print("🛠️ Applying automatic fixes...")
    
    # Apply Black formatting
    print("  📐 Running Black formatter...")
    ret_code, _, _ = run_command("python -m black modules/ --line-length=100")
    if ret_code == 0:
        print("    ✅ Black formatting complete")
    else:
        print("    ❌ Black formatting failed")
        return False
    
    # Apply isort import sorting
    print("  📋 Running isort for imports...")
    ret_code, _, _ = run_command("python -m isort modules/ --profile black --line-length=100")
    if ret_code == 0:
        print("    ✅ Import sorting complete")
    else:
        print("    ❌ Import sorting failed")
        return False
    
    return True


def generate_report(before_issues: Dict[str, int], after_issues: Dict[str, int]) -> None:
    """
    Generate a detailed improvement report.
    
    Args:
        before_issues: Issue counts before fixes
        after_issues: Issue counts after fixes
    """
    print("\n" + "="*60)
    print("📊 CODE QUALITY IMPROVEMENT REPORT")
    print("="*60)
    
    # Calculate totals
    total_before = sum(before_issues.values())
    total_after = sum(after_issues.values())
    improvement = total_before - total_after
    improvement_pct = (improvement / total_before * 100) if total_before > 0 else 0
    
    print(f"🎯 OVERALL RESULTS:")
    print(f"   Before: {total_before:,} issues")
    print(f"   After:  {total_after:,} issues")
    print(f"   Fixed:  {improvement:,} issues ({improvement_pct:.1f}% improvement)")
    print()
    
    # Detailed breakdown
    if before_issues or after_issues:
        print("📋 DETAILED BREAKDOWN:")
        all_codes = set(before_issues.keys()) | set(after_issues.keys())
        
        for code in sorted(all_codes):
            before = before_issues.get(code, 0)
            after = after_issues.get(code, 0)
            if before > 0 or after > 0:
                fixed = before - after
                status = "✅" if fixed > 0 else "⚠️" if after > 0 else "✨"
                print(f"   {status} {code}: {before} → {after} (fixed {fixed})")
    
    print()
    print("🚀 NEXT STEPS:")
    if total_after == 0:
        print("   🎉 Perfect! No remaining issues.")
    elif total_after < 50:
        print("   ✨ Excellent progress! Focus on remaining critical issues.")
    elif total_after < 200:
        print("   👍 Good progress! Continue with systematic fixes.")
    else:
        print("   📈 Initial cleanup done. Plan next iteration.")


def main():
    """Main execution function."""
    print("🔧 RAG System Code Quality Checker")
    print("="*50)
    
    # Check initial state
    print("\n📸 Taking before snapshot...")
    before_issues = check_linting()
    
    # Apply fixes
    print("\n🛠️ Applying improvements...")
    if not apply_automatic_fixes():
        print("❌ Automatic fixes failed")
        sys.exit(1)
    
    # Check final state
    print("\n📸 Taking after snapshot...")
    after_issues = check_linting()
    
    # Generate report
    generate_report(before_issues, after_issues)
    
    print("\n✨ Code quality check complete!")


if __name__ == "__main__":
    main()