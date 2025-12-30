#!/usr/bin/env python3
"""Deployment script for Modal OCR service.

This script provides commands for deploying and managing the Modal OCR service.

Usage:
    # Deploy to Modal (production)
    python app/backend/modal_ocr/deploy.py deploy

    # Run locally for testing
    python app/backend/modal_ocr/deploy.py test

    # Check deployment status
    python app/backend/modal_ocr/deploy.py status
"""

import subprocess
import sys
from pathlib import Path


def get_modal_app_path() -> Path:
    """Get the path to the Modal app file."""
    return Path(__file__).parent / "app.py"


def deploy():
    """Deploy the Modal OCR service to Modal cloud."""
    app_path = get_modal_app_path()

    print("=" * 60)
    print("Deploying Modal OCR Service")
    print("=" * 60)
    print(f"App file: {app_path}")
    print()

    # Run modal deploy
    result = subprocess.run(
        ["modal", "deploy", str(app_path)],
        capture_output=False,
    )

    if result.returncode == 0:
        print()
        print("=" * 60)
        print("Deployment successful!")
        print("=" * 60)
        print()
        print("The service is now available at:")
        print("  App name: research-agent-ocr")
        print()
        print("You can call it from your backend using:")
        print('  fn = modal.Function.from_name("research-agent-ocr", "parse_document")')
        print("  result = fn.remote(document_bytes)")
    else:
        print()
        print("=" * 60)
        print("Deployment failed!")
        print("=" * 60)
        sys.exit(1)


def test(document_path: str = None):
    """Run the Modal app locally for testing."""
    app_path = get_modal_app_path()

    print("=" * 60)
    print("Running Modal OCR Service locally")
    print("=" * 60)

    cmd = ["modal", "run", str(app_path)]
    if document_path:
        cmd.extend(["--document-filename", document_path])

    subprocess.run(cmd)


def status():
    """Check the deployment status of the Modal app."""
    print("=" * 60)
    print("Modal OCR Service Status")
    print("=" * 60)

    # List Modal apps
    result = subprocess.run(
        ["modal", "app", "list"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        if "research-agent-ocr" in result.stdout:
            print("Status: DEPLOYED")
            print()
            print("App details:")
            # Get app details
            subprocess.run(
                ["modal", "app", "list", "--json"],
                capture_output=False,
            )
        else:
            print("Status: NOT DEPLOYED")
            print()
            print("Run 'python deploy.py deploy' to deploy the service.")
    else:
        print("Error checking status:")
        print(result.stderr)


def main():
    """Main entry point for the deployment script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Deploy and manage the Modal OCR service",
    )
    parser.add_argument(
        "command",
        choices=["deploy", "test", "status"],
        help="Command to run",
    )
    parser.add_argument(
        "--document",
        "-d",
        help="Path to document for testing",
        default=None,
    )

    args = parser.parse_args()

    if args.command == "deploy":
        deploy()
    elif args.command == "test":
        test(args.document)
    elif args.command == "status":
        status()


if __name__ == "__main__":
    main()














