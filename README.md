# m3u8-downloader

## Overview
**m3u8-downloader** is a command-line tool designed to download and merge video segments from M3U8 streaming URLs into a single MP4 file. It utilizes the `requests` library for downloading segments and `FFmpeg` for merging them.

## Features
- Download video segments from M3U8 playlists.
- Supports multi-threaded downloads for faster retrieval.
- Automatically merges downloaded segments into a single MP4 file.
- Logging capabilities to track progress and errors.
- Option to keep downloaded segments after merging.

## Installation

### Prerequisites
- Python 3.6 or higher
- FFmpeg (make sure it is installed and added to your system's PATH)

### Clone the Repository
```bash
git clone https://github.com/fllppi/m3u8-downloader.git
cd m3u8-downloader
```

### Install Dependencies
If you prefer to install dependencies separately, create a virtual environment and run:
```bash
pip install -r requirements.txt
```

### Install the Package
You can install the package using pip:
```bash
pip install .
```

## Usage

### Basic Command
To use the tool, run the following command in your terminal:
```bash
m3u8-downloader path/to/your/file.m3u8 --output desired_output.mp4
```

### Command-Line Options
- `m3u8_filename`: The path to the M3U8 file (required).
- `--output`: Specify the output MP4 filename. If not provided, the extracted ID from the M3U8 will be used.
- `--threads`: Specify the number of threads for downloading segments (default is 8).
- `--log_level`: Set the logging level (default is WARNING). Options: DEBUG, INFO, WARNING, ERROR.
- `--keep_segments`: Keep downloaded segments after merging (optional).
- `--ffmpeg_options`: Additional options for the FFmpeg command (space-separated).

### Example
```bash
m3u8-downloader my_video.m3u8 --output my_video.mp4 --threads 4 --keep_segments
```

## License
This project is licensed under the AGPL-3.0 License. See the [LICENSE](LICENSE) file for more details.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for suggestions or bugs.

## Acknowledgments
- [requests](https://docs.python-requests.org/en/latest/) - For handling HTTP requests.
- [tqdm](https://tqdm.github.io/) - For displaying download progress.
- [FFmpeg](https://ffmpeg.org/) - For merging video segments.
