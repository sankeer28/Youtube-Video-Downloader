# YouTube Video Downloader 🎥

A simple and intuitive YouTube video downloader built with **Streamlit** and **yt-dlp** (a powerful fork of youtube-dl). This app allows you to download YouTube videos in various formats and qualities with an easy-to-use interface.

## Features

- **Download YouTube videos**: Input the YouTube URL and download videos in different qualities.
- **Video Info**: Displays video details such as title, channel, duration, view count, and more.
- **Format Selection**: Choose from available video formats, including audio and video quality options.
- **Progress Tracker**: View download progress in real time.
- **Clean and Simple UI**: Built using **Streamlit** with modern styling and responsive layout.
  
## Installation

### Prerequisites

Make sure you have **Python 3.7** or later installed on your machine.

1. Clone the repository:

   ```bash
   git clone https://github.com/sankeer28/Youtube-Video-Downloader.git
   cd Youtube-Video-Downloader
   ```

2. Install the required dependencies using pip:

   ```bash
   pip install -r requirements.txt
   ```

   The dependencies include:
   - `streamlit` for the user interface
   - `yt-dlp` for downloading YouTube videos
   - `pathlib` and `os` for handling file paths

## Usage

1. Run the Streamlit app:

   ```bash
   streamlit run app.py
   ```

