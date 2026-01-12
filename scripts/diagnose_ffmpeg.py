#!/usr/bin/env python3
"""Diagnose ffmpeg availability for yt-dlp."""

import shutil
import subprocess
import sys
from pathlib import Path


def check_command(cmd: str) -> tuple[bool, str]:
    """Check if a command is available."""
    path = shutil.which(cmd)
    if path:
        try:
            result = subprocess.run(
                [cmd, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version = result.stdout.split("\n")[0] if result.stdout else "unknown"
            return True, f"Found at {path}: {version}"
        except Exception as e:
            return True, f"Found at {path} but error getting version: {e}"
    return False, "Not found in PATH"


def check_ytdlp():
    """Check if yt-dlp can find ffmpeg."""
    try:
        import yt_dlp

        # Test with different ffmpeg_location values
        locations = [None, "/usr/bin", "/usr/local/bin", ""]

        for location in locations:
            try:
                ydl_opts = {"quiet": True, "no_warnings": True}
                if location is not None:
                    ydl_opts["ffmpeg_location"] = location

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Try to access FFmpeg postprocessor
                    pp_key = "FFmpegExtractAudio"
                    # This will raise an error if ffmpeg is not found
                    ydl.add_post_processor(
                        ydl.get_postprocessor(pp_key)() if ydl.get_postprocessor(pp_key) else None
                    )

                    location_str = f"'{location}'" if location else "default"
                    return True, f"yt-dlp can find ffmpeg with ffmpeg_location={location_str}"

            except Exception as e:
                continue

        return False, "yt-dlp cannot find ffmpeg with any location setting"

    except ImportError:
        return False, "yt-dlp not installed"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    print("=" * 60)
    print("FFmpeg Availability Diagnostic")
    print("=" * 60)
    print()

    # Check ffmpeg
    print("1. Checking ffmpeg:")
    found, msg = check_command("ffmpeg")
    print(f"   {'✓' if found else '✗'} {msg}")
    print()

    # Check ffprobe
    print("2. Checking ffprobe:")
    found, msg = check_command("ffprobe")
    print(f"   {'✓' if found else '✗'} {msg}")
    print()

    # Check common paths
    print("3. Checking common installation paths:")
    common_paths = [
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
    ]
    for path in common_paths:
        exists = Path(path).exists()
        print(f"   {'✓' if exists else '✗'} {path}")
    print()

    # Check yt-dlp
    print("4. Checking yt-dlp integration:")
    found, msg = check_ytdlp()
    print(f"   {'✓' if found else '✗'} {msg}")
    print()

    # Check PATH
    print("5. Current PATH:")
    path_env = subprocess.run(
        ["printenv", "PATH"], capture_output=True, text=True
    ).stdout.strip()
    for p in path_env.split(":"):
        print(f"   - {p}")
    print()

    print("=" * 60)
    print("Diagnostic complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
