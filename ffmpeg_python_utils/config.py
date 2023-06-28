C_TO_RENAME_FILES = False
C_TO_PRINT_PLOTS = False
C_TO_PRINT_FFMPEG_DEBUG = False
C_TO_PRINT_PACKAGE_INFO = True
C_TO_PRINT_EXECUTION_TIME = True
C_TO_SAVE_LOGS = False
C_CODEC = 'nvidia'  # nvidia, amd

# TODO find the right settings for amd
"""
nvidia as described here "https://video.stackexchange.com/questions/29659/is-there-a-way-to-improve-h264-nvenc-output-quality"
"""
C_CODEC_SETTINGS = {
    'nvidia': '-c:v h264_nvenc -profile:v high -tune hq -rc-lookahead 8 -bf 2 -rc vbr -cq 26 -b:v 0 -maxrate 120M -bufsize 240M',
    'amd': '-c:v h264_amf',
    'cpu': '-c:v libx264',
}
