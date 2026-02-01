# GDownloader - Detailed Project Documentation

## Project Overview

**GDownloader** (also known as **HianimeDownloader**) is a comprehensive CLI tool designed for downloading content from multiple platforms:

- **hianime.to** - Anime streaming platform
- **Social Media Platforms** - TikTok, YouTube, Instagram (reels/images)

This tool combines web scraping, browser automation, network interception, and video downloading technologies to automate content retrieval.

## Developer Setup

### Prerequisites

Before starting development, ensure you have:

- **Python 3.10+** installed
- **Google Chrome** browser installed (required for Selenium)
- **pip** package manager
- **git** for version control

### Installation Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/gheatherington/HianimeDownloader
   cd HianimeDownloader
   ```

2. **Create Virtual Environment (Recommended):**
   - **Windows:**
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **Linux/macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Optional: Setup Cookies (for Instagram):**
   - Export your browser cookies to `cookies.txt` in Netscape format
   - Place the file in the project root directory
   - This is only required for downloading Instagram posts

### Development Environment

**Linting and Code Quality:**

- The project uses **Ruff** for code formatting and linting
- Configuration: `ruff.toml`
  - Line length: 120 characters
  - Ignores E501 (line too long) warnings
- Run linting: `ruff check .`
- Auto-format code: `ruff format .`

**Git Ignore:**
The `.gitignore` file excludes:

- Virtual environments (`/.venv/`)
- Downloaded content (`/output/`)
- IDE configurations (`.idea`, `/.vscode/`)
- Python cache files (`__pycache__`)
- Environment variables (`.env`)
- Cookie files (`cookies.txt`)
- System files (`.DS_Store`)

### Project Standards

- **Type Hints:** Use Python type hints for all function parameters and returns
- **Dataclasses:** Use dataclasses for structured data (e.g., `Anime` class)
- **Error Handling:** Implement retry mechanisms for network operations
- **Color Output:** Use `colorama` for colored terminal output

## Architecture & Components

### 1. Main Entry Point (`main.py`)

The main entry point handles:

- Command-line argument parsing
- Routing to appropriate extractors based on URL or input type
- Execution time tracking

**Key Command-Line Arguments:**

- `-o` / `--output-dir`: Specify custom output directory
- `-l` / `--link`: Provide direct URL to content
- `-n` / `--filename`: Custom filename or anime name for search
- `--no-subtitles`: Skip downloading subtitle files
- `--server`: Select specific streaming server (for HiAnime)
- `-t` / `--type`: Set download type (sub/dub)
- `--aria`: Use aria2c for faster/multithreaded downloads (recommended)
- `--last`: Repeat the last download session

**Workflow:**

1. Parses arguments
2. Determines extractor type based on URL or input
3. Instantiates appropriate extractor
4. Executes download process

### 2. Extractors

#### A. HianimeExtractor (`extractors/hianime.py`)

The most complex extractor, handling anime downloads from hianime.to.

**How It Works:**

1. **Search & Selection Phase:**
   - User provides anime name or direct link
   - If name provided: searches hianime.to and displays results
   - User selects anime from numbered list
   - Displays available sub/dub episode counts

2. **Configuration Phase:**
   - User selects sub or dub (if both available)
   - User specifies episode range (start and end, inclusive)
   - User enters season number
   - User selects streaming server (HD-1, HD-2, etc.)

3. **Web Scraping Phase:**
   - Uses Selenium with stealth mode to avoid detection
   - Configures Chrome with mobile emulation (iPhone X)
   - Navigates to anime page
   - Clicks selected server button
   - Extracts episode URLs from HTML using BeautifulSoup
   - Parses episode numbers and titles

4. **Media Capture Phase:**
   - Uses Selenium Wire to intercept network requests
   - Navigates to each episode page
   - Monitors network traffic for:
     - `.m3u8` files (HLS video streams) - Relaxed detection (not just "master")
     - `.vtt` files (WebVTT subtitle files)
   - Captures specific HTTP headers for both video and subtitles to avoid 403 Forbidden errors
   - Filters subtitles by language (English by default, supports 30+ languages)
   - Uses language detection to ensure correct subtitle selection
   - Retries up to 45 times with page refreshes at attempts 15 and 30
   - Stores captured URLs with request headers

5. **Download Phase:**
   - Uses `yt-dlp` to download HLS streams
   - Resolves variants or falls back to the original index playlist
   - Downloads video as MP4 format
   - Downloads subtitle files as VTT using the `requests` library (faster and avoids 403 errors)
   - Downloads subtitles _before_ the video to prevent link expiration
   - Handles retries and error recovery
   - Creates organized folder structure

**Key Features:**

- **Anti-Detection:**
  - Mobile emulation (iPhone X)
  - Selenium Stealth integration
  - Popup blocking via JavaScript injection
  - Custom user agents
  - Ad blocking preferences
- **Subtitle Handling:**
  - Language detection using `langdetect`
  - Filters out non-English subtitles (configurable)
  - Handles multiple subtitle files per episode
  - User selection if multiple subtitles found
- **Organization:**
  - Creates folder: `{Anime Name} (Sub/Dub)/`
  - Files named: `{Anime Name} - s{Season:02}e{Episode:02} - {Title}.mp4`
  - Exports JSON metadata file with all episode information
  - Removes invalid filename characters

**Data Structures:**

```python
@dataclass
class Anime:
    name: str
    url: str
    sub_episodes: int
    dub_episodes: int
    download_type: str = ""  # "sub" or "dub"
    season_number: int = -1
```

#### B. InstagramExtractor (`extractors/instagram.py`)

Handles Instagram content downloads.

**How It Works:**

- **For Posts (`/p/`):**
  - Uses `gallery-dl` library
  - Configures gallery-dl with custom settings
  - Downloads images with metadata
  - Requires `cookies.txt` for authentication

- **For Reels (`/reel/`):**
  - Uses `yt-dlp` (inherits from GeneralExtractor)
  - Extracts post title from meta tags
  - Downloads video content

**Features:**

- Extracts post titles from Open Graph meta tags
- Supports custom filenames via `--filename` argument
- Cookie-based authentication support

#### C. GeneralExtractor (`extractors/general.py`)

Fallback extractor for other platforms (TikTok, YouTube, etc.).

**How It Works:**

- Uses `yt-dlp` with optimized settings
- Downloads best quality video + audio
- Merges into MP4 format
- Supports cookies.txt for authentication
- Handles various video formats and qualities

**Configuration:**

- Format selection: `bv*+ba/best` (best video + best audio)
- Fragment retries: 10 attempts
- Socket timeout: 60 seconds
- Sleep interval: 1 second between requests
- Force keyframes at cuts for better editing compatibility

### 3. Utility Tools

#### `tools/config.py`

Handles project-wide configuration:

- Loads defaults from `config.json`
- Supports home directory expansion (`~`) for paths
- Provides default values for CLI arguments

#### `tools/functions.py`

Helper functions for user interaction and file operations:

- **`get_conformation(prompt: str) -> bool`:**
  - Prompts user for yes/no confirmation
  - Validates input (y/yes/true or n/no/false)
  - Recursive validation on invalid input

- **`get_int_in_range(prompt: str, _min: int, _max: int) -> int`:**
  - Prompts for integer input within specified range
  - Validates input type and range
  - Recursive validation on invalid input

- **`safe_remove(file: str, retries: int, delay: int)`:**
  - Safely removes files with retry mechanism
  - Handles PermissionError exceptions
  - Retries up to 5 times with 2-second delays
  - Useful for cleaning up temporary download files

#### `tools/YTDLogger.py`

Custom logger for `yt-dlp` output formatting:

- **`debug(msg: str)`:**
  - Filters and colors download progress messages
  - Shows ETA and completion status
  - Highlights errors in red
  - Formats fragment errors
  - Uses carriage return for progress updates

- **`info(msg)`:**
  - Logs informational messages

- **`warning(msg)`:**
  - Currently passes (no output)

- **`error(msg)`:**
  - Logs error messages

## Complete Workflow Example (HiAnime)

1. **User Command:**

   ```bash
   python main.py -n "Solo Leveling" -o ~/Downloads/Anime/ --server "HD-1"
   ```

2. **Search Phase:**
   - Searches hianime.to for "Solo Leveling"
   - Displays numbered list of results with episode counts

3. **Selection:**
   - User selects anime (e.g., option 1)
   - System displays: name, URL, sub episodes, dub episodes

4. **Configuration:**
   - User selects: Sub
   - User enters: Start episode 1, End episode 12
   - User enters: Season 1
   - Server "HD-1" already specified via argument

5. **Browser Automation:**
   - Selenium opens Chrome in stealth mode
   - Navigates to anime page
   - Clicks HD-1 server button
   - Extracts episode URLs from page source

6. **Network Interception:**
   - For each episode:
     - Navigates to episode page
     - Monitors network requests
     - Captures .m3u8 (video) and .vtt (subtitle) URLs
     - Stores request headers for authentication

7. **Download:**
   - yt-dlp downloads each episode:
     - Resolves master.m3u8 to actual stream URL
     - Downloads HLS stream segments
     - Merges into MP4 file
     - Downloads subtitle file
   - Files saved with proper naming convention

8. **Organization:**
   ```
   ~/Downloads/Anime/
     Solo Leveling (Sub)/
       Solo Leveling (Season 1).json
       Solo Leveling - s01e01 - Episode Title.mp4
       Solo Leveling - s01e01 - Episode Title.vtt
       Solo Leveling - s01e02 - Episode Title.mp4
       Solo Leveling - s01e02 - Episode Title.vtt
       ...
   ```

## Technical Details

### Dependencies

**Core Libraries:**

- `selenium` + `selenium-wire`: Browser automation and network interception
- `selenium-stealth`: Anti-detection measures
- `yt-dlp`: Video downloading and format handling
- `beautifulsoup4`: HTML parsing
- `gallery-dl`: Instagram image downloads
- `colorama`: Colored terminal output
- `langdetect`: Subtitle language detection
- `requests`: HTTP requests

**Key Features:**

- Mobile emulation for browser
- Stealth mode to avoid bot detection
- Network request interception
- HLS stream handling
- Subtitle language detection
- Retry mechanisms for reliability

### Security & Anti-Detection Measures

1. **Mobile Emulation:**
   - Emulates iPhone X device
   - Reduces detection likelihood

2. **Stealth Mode:**
   - Selenium Stealth integration
   - Hides automation indicators
   - Custom WebGL vendor/renderer

3. **Popup Blocking:**
   - JavaScript injection to block alerts/confirms/prompts
   - Blocks window.open() calls
   - Chrome preferences for popup blocking

4. **Custom Headers:**
   - Realistic user agent strings
   - Standard browser headers

### Error Handling

- **Retry Mechanisms:**
  - Up to 45 attempts for media URL capture
  - 10 fragment retries for downloads
  - Page refreshes at specific attempt numbers

- **File Operations:**
  - Safe file deletion with retries
  - Handles PermissionError exceptions

- **User Interruption:**
  - Keyboard interrupt handling
  - Option to download captured URLs before exit
  - Cleanup of temporary files

- **Validation:**
  - Input validation for user prompts
  - Range checking for episode numbers
  - Server selection validation

## Supported Platforms

### Fully Tested:

- **hianime.to** - Anime episodes with subtitles
- **TikTok** - Videos
- **YouTube** - Long-form videos and shorts
- **Instagram** - Reels and images/posts

### Platform-Specific Notes:

**HiAnime:**

- Requires server selection
- Supports both sub and dub
- Episode range selection
- Season organization

**Instagram:**

- Posts require `cookies.txt` for authentication
- Reels use yt-dlp
- Images use gallery-dl

**General (TikTok, YouTube, etc.):**

- Uses yt-dlp with best quality selection
- Automatic format detection
- Cookie support available

## Limitations & Known Issues

1. **Ad Blocking:**
   - Works best with VPN that has ad blocking
   - Chrome session ad blocking is limited
   - Manual intervention may be needed for redirect ads

2. **Manual Intervention:**
   - If redirect ads open second tab, user must:
     - Close the second tab manually
     - Refresh the original site
   - This is a known issue to be patched

3. **Cookies:**
   - Instagram requires `cookies.txt` for some content
   - Cookies must be in Netscape format

4. **Server Selection:**
   - Must choose valid streaming server for HiAnime
   - Server names are case-sensitive

5. **Network Requirements:**
   - Requires stable internet connection
   - HLS streams may have multiple segments
   - Download speed depends on server performance

## File Structure

```
HianimeDownloader/
├── extractors/
│   ├── general.py          # General platform extractor (TikTok, YouTube)
│   ├── hianime.py           # HiAnime-specific extractor
│   └── instagram.py         # Instagram extractor
├── tools/
│   ├── functions.py         # Utility functions
│   └── YTDLogger.py         # Custom yt-dlp logger
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── ruff.toml               # Linter configuration
└── README.md               # Basic usage instructions
```

## Usage Examples

### Basic Usage:

```bash
python main.py
# Interactive mode - prompts for all inputs
```

### With Arguments:

```bash
python main.py -n "Solo Leveling" -o ~/Desktop/ --server "HD-1" --no-subtitles
```

### Direct Link:

```bash
python main.py -l "https://hianime.to/watch/solo-leveling" -o ~/Downloads/
```

### Instagram Reel:

```bash
python main.py -l "https://www.instagram.com/reel/ABC123/" -n "my_reel"
```

### YouTube Video:

```bash
python main.py -l "https://www.youtube.com/watch?v=ABC123" -n "video_title"
```

## Configuration

### Output Directory:

- Default: `output/`
- Customizable via `-o` / `--output-dir`

### Cookies:

- Place `cookies.txt` in project root
- Format: Netscape cookie format
- Used for authenticated downloads

### Linter:

- Uses Ruff for code formatting
- Configuration in `ruff.toml`
- Line length: 120 characters

## Future Improvements

Potential enhancements mentioned in code:

- Better ad blocking integration
- Automatic popup handling
- More platform support
- Improved error messages
- Batch download capabilities

## Conclusion

GDownloader is a sophisticated tool that combines multiple technologies to automate content downloading from various platforms. It handles complex scenarios like HLS stream extraction, subtitle language detection, and anti-detection measures while providing a user-friendly CLI interface.

The modular architecture allows for easy extension to new platforms, and the robust error handling ensures reliable downloads even in challenging network conditions.
