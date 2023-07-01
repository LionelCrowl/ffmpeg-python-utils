"""
:authors: LionelCrowl
:license: MIT License, see LICENSE file

:copyright: (c) 2023 LionelCrowl
"""

from .main import *
from .other import remove_silence_from_audio_file, find_offsets

__all__ = ['add_audio_to_video',
           'add_blurred_space_around_video',
           'add_colored_space_around_video',
           'add_image_to_video',
           'add_rectangle_to_video',
           'add_text_to_video',
           'add_video_to_video',
           'get_audio_from_video',
           'get_audio_info',
           'get_concantenated_videos',
           'get_cropped_video',
           'get_frame',
           'get_image_info',
           'get_mirrored_video',
           'get_resized_video',
           'get_rotated_video',
           'get_subclips_with_sound',
           'get_video_from_picture',
           'get_video_info',
           'remove_silence_from_audio_file',
           'find_offsets',
           ]
