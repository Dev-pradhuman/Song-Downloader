# Song Downloader

A clean, modern, portable desktop application for downloading Spotify songs, albums, and playlists with local dependency isolation.

![Song Downloader](assets/preview.png)

---

## Why Choose Song Downloader?

Most command-line and third-party media downloaders create headaches for everyday users:
* ❌ They demand manual installation of FFmpeg, Deno, and package managers into your machine's global environment.
* ❌ They pollute global folders (`%APPDATA%`, `~/.cache`, `~/.deno`) and system PATHs with gigabytes of untracked files.
* ❌ They force you to download entire 50-track albums or playlists just to get the 2 or 3 songs you actually like.
* ❌ Uninstalling them leaves abandoned dependencies scattered all over your hard drive.

### Here is Why Song Downloader is Better:

* **🛡️ 100% Isolated & Truly Portable**: All runtimes (FFmpeg, Deno), caches, and temp files live exclusively inside the application directory. No global system pollution, no registry tampering, no PATH modifications. To uninstall, simply delete the folder.
* **🎯 True Selective Downloading**: Paste an album or playlist link, and Song Downloader previews the full tracklist and durations first without downloading media. You pick exactly which songs you want via checkboxes. Unselected tracks are never downloaded.
* **⚡ One-Click Automated Setup**: No need to open PowerShell, install winget/chocolatey, or configure command-line tools. Click **Install Dependencies** on first launch, and the app sets up its own isolated environment automatically.
* **🏷️ Studio-Grade Metadata & Artwork**: Every track is automatically converted and tagged with official high-resolution album artwork, artist credentials, album names, year, and track numbers.
* **🚀 Multi-Threaded Performance**: Downloads multiple audio streams concurrently with optimized audio conversion and modern YouTube stream signature deciphering.
* **📂 User-First File Control**: Your downloaded songs go wherever you want (defaults to your standard OS `Downloads` folder), keeping your personal music library neatly separated from application files.

---

## Features

* **Single Song Downloading**: Paste any Spotify song URL to fetch rich metadata (cover, title, artist, album, duration) and download it cleanly tagged.
* **Album & Playlist Track Detection**: Retrieves track listings without downloading unwanted media.
* **Selective Multi-Track Download**: Choose exactly which songs to download using checkboxes, or use **Select All** / **Deselect All**. Only selected tracks are fetched.
* **Configurable Download Destination**: Defaults to your operating system's `Downloads` folder (`%USERPROFILE%\Downloads`), with full browse control to save anywhere.
* **100% Local Dependency Management**: FFmpeg, Deno, caches, and temporary files live strictly inside the application folder. No global system pollution.
* **Truly Portable**: To uninstall, simply delete the `Song Downloader` folder. Your system remains completely untouched.
* **First-Run Verification & Repair**: Checks and installs all required components on first run with real progress indicators, and includes a one-click repair tool.

---

## Quick Start

1. **Download or Clone** this repository:
   ```bash
   git clone https://github.com/your-username/Song-Downloader.git
   cd "Song Downloader"
   ```
2. **Launch the application**:
   - Double-click **`Song Downloader.exe`** (or run **`run.bat`** on Windows / **`./run.sh`** on Linux).
3. **Install Dependencies**:
   - On first launch, click **Install Dependencies**. The application will automatically download and verify the local FFmpeg binary and Deno runtime.
4. **Download Music**:
   - Paste any Spotify track, album, or playlist URL into the input field and click **Continue**.
   - For albums/playlists: select the tracks you want.
   - Choose your destination folder.
   - Click **Download**!

---

## Application Architecture

Song Downloader enforces strict local dependency containment:

```text
Song Downloader/
│
├── Song Downloader.exe        # Standalone Windows executable
├── run.bat                    # Fallback Windows launcher
├── run.sh                     # Fallback Linux/macOS launcher
├── README.md                  # Documentation
├── LICENSE                    # MIT License
├── .gitignore                 # Strict hygiene
├── requirements.txt           # Python library requirements
│
├── src/
│   ├── main.py                # Application entry point & router
│   ├── core/                  # Core modules (paths, environment, downloader, metadata)
│   └── ui/                    # CustomTkinter modern UI views
│
├── config/
│   ├── dependencies.json      # Dependency manifest (versions, URLs, paths)
│   └── settings.default.json  # Default user preferences
│
├── tools/                     # Application-managed local binaries
│   └── ffmpeg/                # Local FFmpeg executable (isolated from system PATH)
│
├── runtime/                   # Local runtimes
│   └── deno/                  # Local Deno runtime (for streaming deciphering)
│
├── cache/                     # Isolated cache (SPOTDL_CACHE_DIR, DENO_DIR)
├── logs/                      # Application & download logs
└── temp/                      # Isolated temporary download & extraction scratch space
```

### Dependency Isolation

All external tools required for downloading and audio processing are scoped locally:
* **FFmpeg**: Located in `tools/ffmpeg/`. It is never added to the global system PATH.
* **Deno**: Located in `runtime/deno/`. Used by the media extraction engine for JavaScript signature resolution.
* **Caches & Temp**: `DENO_DIR`, `SPOTDL_CACHE_DIR`, and `TEMP` are redirected to `cache/` and `temp/` inside the application directory.

---

## Uninstallation

Because Song Downloader is built to be strictly self-contained:

> **To uninstall, simply delete the `Song Downloader` folder.**

Deleting the folder immediately removes the application, its settings, its caches, and every dependency it downloaded (FFmpeg, Deno, etc.).

> **Note**: Songs you downloaded and saved to your `Downloads` folder (or other custom directories) are your personal files and will **not** be deleted.

---

## Development & Building

### Running from Source

Requirements: Python 3.9+

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Launch the application:
   ```bash
   python src/main.py
   ```
   Or use the fallback launcher:
   ```cmd
   run.bat
   ```

### Building `Song Downloader.exe`

A build script is included that cleans old build artifacts, compiles the standalone executable using PyInstaller, and deploys it to the application root:

* On Windows:
  ```cmd
  scripts\build.bat
  ```
* On Linux/macOS:
  ```bash
  chmod +x scripts/build.sh
  ./scripts/build.sh
  ```

The build script generates a single-file, windowed executable named `Song Downloader.exe` directly in the project root.

---

## License

This project is licensed under the [MIT License](LICENSE).
