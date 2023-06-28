C_CODEC = 'nvidia'  # nvidia, amd, cpu
"""
The codec we will use during the project.
"""
# TODO: Find the right settings for AMD.
C_CODEC_SETTINGS = {
    'nvidia': '-c:v h264_nvenc -profile:v high -tune hq -rc-lookahead 8 -bf 2 -rc vbr -cq 26 -b:v 0 -maxrate 120M -bufsize 240M',
    'amd': '-c:v h264_amf',
    'cpu': '-c:v libx264',
}
"""
Specific settings for the codec. Nvidia is described here: 
"https://video.stackexchange.com/questions/29659/is-there-a-way-to-improve-h264-nvenc-output-quality"
"""

C_TO_PRINT_PACKAGE_INFO = True
"""Whether to show package info."""
C_TO_PRINT_EXECUTION_TIME = False
"""Whether to show each function's execution time."""

C_TO_PRINT_ONLY_FFMPEG_ERRORS = False
"""Whether to print only ffmpeg errors. C_TO_PRINT_ONLY_FFMPEG_ERRORS > C_TO_PRINT_FFMPEG_DEBUG. The code first 
checks if to print only errors."""
C_TO_PRINT_FFMPEG_DEBUG = False
"""Whether to show detailed information from ffmpeg."""
C_TO_SAVE_LOGS = False
"""Whether to save ffmpeg logs."""

C_TO_RENAME_FILES = False
"""Whether to rename files. It should work with False."""
C_TO_PRINT_PLOTS = False
"""Whether to show plots during finding offsets before proceeding."""
