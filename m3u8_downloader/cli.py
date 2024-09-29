# m3u8_downloader/cli.py

import argparse
import logging
from .main import m3u8_to_mp4

def main():
    parser = argparse.ArgumentParser(description="Download and merge M3U8 video segments into MP4.")
    parser.add_argument("m3u8_filename", help="Path to the M3U8 file.")
    parser.add_argument("--output", help="Output MP4 filename. If not provided, will use the extracted ID.")
    parser.add_argument("--threads", type=int, default=8, help="Number of threads for downloading.")
    parser.add_argument("--log_level", type=str, default="WARNING", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Set the logging level.")
    parser.add_argument("--keep_segments", action="store_true", help="Keep downloaded segments after merging.")
    parser.add_argument("--ffmpeg_options", nargs='*', help="Additional FFmpeg options (space-separated).")
    
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), logging.WARNING)
    m3u8_to_mp4(args.m3u8_filename, args.output, args.threads, log_level, args.keep_segments, args.ffmpeg_options)

if __name__ == "__main__":
    main()
