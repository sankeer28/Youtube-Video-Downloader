import streamlit as st
import yt_dlp
import os
from pathlib import Path
import re
from datetime import timedelta
from moviepy.editor import VideoFileClip, AudioFileClip
import tempfile

st.set_page_config(
    page_title="YouTube Video Downloader",
    page_icon="🎥",
    layout="centered"
)

st.markdown("""
    <style>

        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        .title-container h1 {
            font-size: 3rem;  /* Adjust font size as needed */
            font-weight: bold;
            text-align: center;
            margin-bottom: 1rem;
            background: linear-gradient(45deg, #FF7E5F, #FEB47B, #6A5ACD, #00CED1, #FF6347);
            background-size: 400% 400%; /* Makes the gradient bigger for animation */
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: gradient-animation 5s ease infinite; /* Looping animation */
        }

        @keyframes gradient-animation {
            0% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
            100% {
                background-position: 0% 50%;
            }
        }
        
        .video-info {
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        .footer {
            text-align: center;
            padding: 1rem;
            margin-top: 2rem;
            border-top: 1px solid #ddd;
        }
    </style>
""", unsafe_allow_html=True)

def create_download_directory():
    download_dir = Path("temp_downloads")
    download_dir.mkdir(exist_ok=True)
    return download_dir

def strip_ansi_codes(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def format_duration(seconds):
    return str(timedelta(seconds=seconds))

def get_video_info(url):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail'),
                'duration': format_duration(info.get('duration', 0)),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'channel': info.get('channel', 'Unknown Channel'),
                'upload_date': info.get('upload_date', 'Unknown Date'),
                'description': info.get('description', 'No description available'),
                'formats': info.get('formats', [])
            }
    except Exception as e:
        st.error(f"Error fetching video information: {str(e)}")
        return None

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            if '_percent_str' in d:
                percent_str = strip_ansi_codes(d['_percent_str']).strip()
                progress = float(percent_str.replace('%', ''))
            elif 'percentage' in d:
                progress = float(d['percentage'])
            else:
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                progress = (downloaded / total * 100) if total else 0
                
            st.session_state.progress_bar.progress(progress / 100)
            st.session_state.status_text.text(f"Downloading: {progress:.1f}%")
        except Exception as e:
            st.warning(f"Progress update error: {e}")
            
    elif d['status'] == 'finished':
        st.session_state.status_text.text("Download completed! Processing video...")

def get_available_formats(formats):
    quality_formats = {}  
    best_audio = None

    for f in formats:
        if (f.get('acodec') != 'none' and not f.get('vcodec')) or f['vcodec'] == 'none':
            if not best_audio or f.get('filesize', 0) > best_audio.get('filesize', 0):
                best_audio = f

    for f in formats:
        if not f.get('height') or not f.get('vcodec') or f['vcodec'] == 'none':
            continue
            
        height = f.get('height', 0) 
        filesize = f.get('filesize', 0) 
        ext = f.get('ext', 'mp4')  
        
        if height > 0:
            quality_string = f"{height}p ({ext})"
            if quality_string not in quality_formats or filesize > quality_formats[quality_string]['filesize']:
                quality_formats[quality_string] = {
                    'height': height,
                    'format_id': f['format_id'],
                    'quality': quality_string,
                    'video_ext': ext,
                    'filesize': filesize,
                    'audio_format_id': best_audio['format_id'] if best_audio else None
                }
    unique_formats = list(quality_formats.values())
    return sorted(unique_formats, key=lambda x: x['height'], reverse=True)

def merge_video_audio(video_path, audio_path, output_path):
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        final_video = video.set_audio(audio)
        final_video.write_videofile(output_path, codec='libx264')
        video.close()
        audio.close()
        return True
    except Exception as e:
        st.error(f"Error merging video and audio: {str(e)}")
        return False

def download_video(url, format_data):
    download_dir = create_download_directory()
    temp_dir = tempfile.mkdtemp()
    
    video_opts = {
        'format': format_data['format_id'],
        'outtmpl': os.path.join(temp_dir, 'video.%(ext)s'),
        'progress_hooks': [progress_hook],
    }
    
    audio_opts = {
        'format': format_data['audio_format_id'],
        'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
        'progress_hooks': [progress_hook],
    }
    
    try:
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            video_info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(video_info)

        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            audio_info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(audio_info)
        
        output_filename = f"{video_info['title']}.mp4"
        output_path = os.path.join(download_dir, output_filename)
        st.text("Merging video and audio... Please Wait")
        if merge_video_audio(video_path, audio_path, output_path):
            try:
                os.remove(video_path)
                os.remove(audio_path)
                os.rmdir(temp_dir)
            except Exception as e:
                st.warning(f"Error cleaning up temporary files: {str(e)}")
            
            return output_path
        else:
            st.error("Failed to merge video and audio.")
            return None
            
    except Exception as e:
        st.error(f"Error downloading video: {str(e)}")
        return None

def main():
    st.markdown("""
        <div class="title-container">
            <h1>🎥 YouTube Video Downloader</h1>
        </div>
    """, unsafe_allow_html=True)
    
    
    url = st.text_input("Enter YouTube URL:")
    
    if url:
        video_info = get_video_info(url)
        if video_info:
            st.markdown('<div class="video-info">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(video_info['thumbnail'], use_container_width=True)
            
            with col2:
                st.markdown(f"### {video_info['title']}")
                st.markdown(f"**Channel:** {video_info['channel']}   &nbsp;&nbsp;&nbsp; **Duration:** {video_info['duration']}   &nbsp;&nbsp;&nbsp; **Views:** {video_info['view_count']:,}")
                if video_info['like_count']:
                    st.markdown(f"**Likes:** {video_info['like_count']:,}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            formats = get_available_formats(video_info['formats'])
            if formats:
                format_display = [f"{f['quality']}" for f in formats]
                
                selected_format = st.selectbox(
                    "Select video quality and format:",
                    options=range(len(format_display)),
                    format_func=lambda x: format_display[x],
                    index=0
                )
                
                if st.button("Start Download", type="primary"):
                    st.session_state.progress_bar = st.progress(0)
                    st.session_state.status_text = st.empty()
                    
                    selected_format_data = formats[selected_format]
                    filename = download_video(url, selected_format_data)
                    
                    if filename and os.path.exists(filename):
                        with open(filename, 'rb') as file:
                            video_data = file.read()
                            st.download_button(
                                label="Download Video",
                                data=video_data,
                                file_name=os.path.basename(filename),
                                mime="video/mp4"
                            )
                        try:
                            os.remove(filename)
                        except Exception as e:
                            st.error(f"Error cleaning up file: {e}")
                    else:
                        st.error("Download failed. Please try again.")
            else:
                st.warning("No compatible formats found. Please try another video.")
        else:
            st.warning("Could not fetch video information. Please check the URL and try again.")
    else:
        st.info("Please enter a YouTube URL to see video information and download options.")
    
    st.markdown("""
        <div class="footer">
            <p><a href="https://github.com/sankeer28/Youtube-Video-Downloader" target="_blank">GitHub</a></p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
