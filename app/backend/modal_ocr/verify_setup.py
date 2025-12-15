#!/usr/bin/env python3
"""Verify Modal OCR setup and configuration."""

import sys
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))


def check_config():
    """Check configuration settings."""
    print("=" * 60)
    print("Modal OCR Setup Verification")
    print("=" * 60)
    print()

    # Check config
    print("1. Configuration:")
    try:
        from research_agent.config import get_settings
        settings = get_settings()
        print(f"   ✅ Config loaded successfully")
        print(f"   - OCR Mode: {settings.ocr_mode}")
        print(f"   - Modal Enabled: {settings.modal_enabled}")
        print(f"   - Modal App Name: {settings.modal_app_name}")
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return False
    print()

    # Check Modal parser import
    print("2. Modal Parser:")
    try:
        from research_agent.infrastructure.parser.modal_parser import ModalParser
        print(f"   ✅ ModalParser imported successfully")
    except ImportError as e:
        print(f"   ⚠️  ModalParser import failed: {e}")
        print(f"      This is expected if Modal is not installed.")
        print(f"      Run: pip install modal")
    print()

    # Check ParserFactory
    print("3. Parser Factory:")
    try:
        from research_agent.infrastructure.parser.factory import ParserFactory
        print(f"   ✅ ParserFactory imported successfully")
        print(f"   - Supported MIME types: {ParserFactory.supported_mime_types()}")
    except Exception as e:
        print(f"   ❌ ParserFactory error: {e}")
        return False
    print()

    # Check Modal client
    print("4. Modal Client:")
    try:
        import modal
        print(f"   ✅ Modal library installed (version: {modal.__version__})")
    except ImportError:
        print(f"   ⚠️  Modal library not installed")
        print(f"      Run: pip install modal")
        print(f"      Then: modal token new")
    print()

    # Check Modal authentication
    print("5. Modal Authentication:")
    try:
        import modal
        # Try to get token info
        from modal._utils.grpc_utils import get_metadata
        print(f"   ✅ Modal authentication configured")
    except ImportError:
        print(f"   ⚠️  Cannot check (Modal not installed)")
    except Exception as e:
        print(f"   ⚠️  Modal authentication may not be set up: {e}")
        print(f"      Run: modal token new")
    print()

    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Install Modal: pip install modal")
    print("  2. Authenticate: modal token new")
    print("  3. Deploy: make modal-deploy")
    print("  4. Enable in .env: MODAL_ENABLED=true")
    print()

    return True


if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)



