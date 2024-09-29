import os
import requests
import subprocess
import time
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import hashlib
import shutil
import json

def setup_logging(log_level=logging.WARNING):
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_segments(m3u8_filename):
    """
    Extracts segment URLs from an M3U8 file.

    Parameters:
        m3u8_filename (str): The path to the M3U8 file.

    Returns:
        list: A list of segment URLs.
    """
    segments = []
    base_url = os.path.dirname(m3u8_filename)
    with open(m3u8_filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                if not line.startswith('http'):
                    line = os.path.join(base_url, line)
                segments.append(line)
    return segments

def calculate_file_md5(filename):
    """
    Calculates the MD5 hash of a file.

    Parameters:
        filename (str): The path to the file.

    Returns:
        str: The MD5 hash of the file.
    """
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_segment(url, output_filename, segment_index, total_segments):
    """
    Downloads a video segment from a given URL.

    Parameters:
        url (str): The URL of the segment to download.
        output_filename (str): The file path to save the downloaded segment.
        segment_index (int): The index of the segment being downloaded (for progress display).
        total_segments (int): The total number of segments to download.

    Returns:
        str: The MD5 hash of the downloaded segment file if successful, None otherwise.
    """
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        
        mode = 'wb'
        initial_pos = 0
        
        if os.path.exists(output_filename):
            mode = 'ab'
            initial_pos = os.path.getsize(output_filename)
            if initial_pos >= total_size:
                logging.info(f"Segment {segment_index}/{total_segments} already downloaded.")
                return calculate_file_md5(output_filename)
        
        with open(output_filename, mode) as f, tqdm(
            desc=f"Segment {segment_index}/{total_segments}",
            initial=initial_pos,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
            leave=False
        ) as bar:
            start_time = time.time()
            downloaded = initial_pos
            
            for data in response.iter_content(block_size):
                size = f.write(data)
                downloaded += size
                bar.update(size)
                
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    speed = downloaded / elapsed_time / 1024  # KB/s
                    bar.set_postfix(speed=f"{speed:.2f} KB/s", refresh=False)
        
        return calculate_file_md5(output_filename)
    except requests.RequestException as e:
        logging.error(f"Error downloading {url}: {e}")
        if os.path.exists(output_filename):
            os.remove(output_filename)
        return None

def download_segments_in_parallel(segments, output_dir, num_threads=8):
    """
    Downloads video segments in parallel.

    Parameters:
        segments (list): A list of segment URLs to download.
        output_dir (str): The directory to save the downloaded segments.
        num_threads (int): The number of threads to use for downloading.

    Returns:
        list: A sorted list of tuples containing the segment index and filename of downloaded segments.
    """
    os.makedirs(output_dir, exist_ok=True)

    total_segments = len(segments)
    downloaded_segments = []
    skipped_counter = 0

    segment_info_file = os.path.join(output_dir, 'segment_info.json')
    if os.path.exists(segment_info_file):
        with open(segment_info_file, 'r') as f:
            segment_info = json.load(f)
    else:
        segment_info = {}

    logging.info(f"Starting download of {total_segments} segments.")

    with tqdm(total=total_segments, desc="Overall Progress", unit='segment') as progress_bar:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_index = {}
            for i, seg in enumerate(segments):
                segment_filename = os.path.join(output_dir, f"segment_{i:05d}.ts")
                if str(i) in segment_info and os.path.exists(segment_filename):
                    if segment_info[str(i)]['md5'] == calculate_file_md5(segment_filename):
                        downloaded_segments.append((i, segment_filename))
                        skipped_counter += 1
                        progress_bar.update(1)
                        continue
                future_to_index[executor.submit(download_segment, seg, segment_filename, i + 1, total_segments)] = i
            
            for future in as_completed(future_to_index):
                segment_index = future_to_index[future]
                try:
                    md5 = future.result()
                    if md5:
                        segment_filename = os.path.join(output_dir, f"segment_{segment_index:05d}.ts")
                        downloaded_segments.append((segment_index, segment_filename))
                        segment_info[str(segment_index)] = {'url': segments[segment_index], 'md5': md5}
                    else:
                        logging.error(f"Failed to download segment {segment_index + 1}")
                except Exception as e:
                    logging.error(f"Error processing segment {segment_index + 1}: {e}")
                finally:
                    progress_bar.update(1)

    with open(segment_info_file, 'w') as f:
        json.dump(segment_info, f)

    logging.info(f"Download completed: {len(downloaded_segments)} segments downloaded, {skipped_counter} segments skipped.")
    return sorted(downloaded_segments, key=lambda x: x[0])

def merge_segments_to_mp4(segments, output_file, ffmpeg_options=None):
    """
    Merges video segments into a single MP4 file using FFmpeg.

    Parameters:
        segments (list): A list of downloaded segments.
        output_file (str): The filename for the merged output MP4 file.
        ffmpeg_options (list): Additional options for the FFmpeg command.
    """
    concat_filename = "concat_list.txt"
    with open(concat_filename, 'w') as concat_file:
        for _, seg in segments:
            concat_file.write(f"file '{seg}'\n")

    ffmpeg_command = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_filename,
        "-c", "copy", "-movflags", "+faststart", output_file
    ]
    
    if ffmpeg_options:
        ffmpeg_command.extend(ffmpeg_options)

    try:
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        logging.info(f"Output saved to: {output_file}")
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg error: {e.stderr}")
    finally:
        os.remove(concat_filename)

def extract_id_from_m3u8(m3u8_filename):
    """
    Extracts a unique identifier from an M3U8 file.

    Parameters:
        m3u8_filename (str): The path to the M3U8 file.

    Returns:
        str: The extracted ID or None if not found.
    """
    
    try:
        with open(m3u8_filename, 'r') as file:
            for line in file:
                if line.strip() and not line.startswith('#'):
                    print(f"Processing line: {line.strip()}")
                    match = re.search(r'_([^_]+_[0-9]+_[0-9]+)/', line)
                    if match:
                        full_match = match.group(1)
                        print(f"Match found: {full_match}")
                        
                        id_part = full_match.split('_', 2)[:2]
                        result = '_'.join(id_part)
                        
                        return result
            print("WARNING - No valid lines found for ID extraction.")
    except FileNotFoundError:
        print(f"Error: The file '{m3u8_filename}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    print("WARNING - Could not extract ID from M3U8 file. Using default naming.")
    return None

def m3u8_to_mp4(m3u8_filename, output_mp4=None, num_threads=8, log_level=logging.WARNING, keep_segments=True, ffmpeg_options=None):
    """
    Converts an M3U8 file to an MP4 file by downloading segments and merging them.
    """
    setup_logging(log_level)
    
    video_id = extract_id_from_m3u8(m3u8_filename)
    if not video_id:
        logging.warning("Could not extract ID from M3U8 file. Using default naming.")
        video_id = "default"

    if output_mp4 is None:
        output_mp4 = f"{video_id}.mp4"

    segments = extract_segments(m3u8_filename)
    logging.info(f"Found {len(segments)} segments to download.")

    output_dir = os.path.join(os.getcwd(), "tmp", f"m3u8_segments_{video_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        downloaded_segments = download_segments_in_parallel(segments, output_dir, num_threads)
        merge_segments_to_mp4(downloaded_segments, output_mp4, ffmpeg_options)
    finally:
        if not keep_segments:
            shutil.rmtree(output_dir, ignore_errors=True)
        else:
            logging.info(f"Segments kept in: {output_dir}")

    logging.info("All tasks completed!")
