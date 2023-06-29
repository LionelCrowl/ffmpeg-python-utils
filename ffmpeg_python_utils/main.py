import datetime
import inspect
import json
import subprocess
import os
from functools import wraps
from .config import C_TO_RENAME_FILES, C_TO_PRINT_PACKAGE_INFO, C_TO_SAVE_LOGS, C_TO_PRINT_FFMPEG_DEBUG, \
    C_TO_PRINT_EXECUTION_TIME, C_CODEC, C_CODEC_SETTINGS, C_TO_PRINT_ONLY_FFMPEG_ERRORS
from .inc import replace_forbidden_chars, print_info, make_lists_equal, \
    get_codec_meeting_constraints, save_string_return_output


def process(function_to_modify):
    # Renames input_path if input_path == output_path, then deletes it.
    # If needed renames input file if space in its name to avoid problems.
    # Catches and prints errors from console during .run() ffmpeg-python command.

    @wraps(function_to_modify)
    def wrapper(input_path=None, *args, **kwargs):
        # Get the names of the arguments in the decorated function
        arg_names = inspect.getfullargspec(function_to_modify).args
        if input_path:
            arg_dict = {arg_names[0]: input_path}
            if args:
                arg_dict.update(dict(zip(arg_names[1:], args)))
            kwargs.update(arg_dict)
        else:
            input_path = kwargs[arg_names[0]]

        # Checking if readable
        # Renaming file if needed
        # Rewriting input_path with output_path
        iterable_input_path = input_path if not isinstance(input_path, str) else [input_path]
        files_to_delete_after_renaming = []
        for i, input_path in enumerate(iterable_input_path):
            # Checking if list was initially passed, and there are duplicates in iterable_input_path,
            # and we rewrite file (at some point there will be file with "_tmp" at the end, and it will try to read it without "_tmp")
            if len(iterable_input_path) > 1 and input_path in iterable_input_path[i:] and 'output_path' in kwargs and \
                    kwargs['output_path'] in iterable_input_path:
                raise IOError(
                    f"If you want to rewrite file, then please exclude duplicates from input_paths. Consider not rewriting input_path with output_path ({kwargs['output_path']})")

            # Check if there is a readable file at path
            if not os.access(input_path, os.R_OK):
                raise IOError(
                    f"Path {input_path} is not readable.")

            # Rename input file if special symbols in name
            if C_TO_RENAME_FILES:
                input_path = replace_forbidden_chars(input_path, True)
                if 'output_path' in kwargs:
                    kwargs['output_path'] = replace_forbidden_chars(kwargs['output_path'], True)

            # Dealing with input file rewriting ffmpeg feature
            # If there is 'output_path' in kwargs then check if it is equal to path
            if 'output_path' in kwargs:
                # If it equals, then we rename input_path due to the limitation of ffmpeg - it can't rewrite the input file
                if kwargs['output_path'] == input_path:
                    files_to_delete_after_renaming.append(input_path + '_tmp')
                    try:
                        os.rename(input_path, input_path + '_tmp')
                        iterable_input_path[i] = input_path + '_tmp'
                        print_info(f'Renamed {input_path} to {input_path + "_tmp"}', to_print=C_TO_PRINT_PACKAGE_INFO)
                    except FileExistsError:
                        # if we already have the input_path+'_tmp', we delete it, bc it is probably due to error
                        os.remove(input_path + '_tmp')
                        os.rename(input_path, input_path + '_tmp')
                        iterable_input_path[i] = input_path + '_tmp'
                        print_info(
                            f'Found already created {input_path + "_tmp"} in the {input_path}! Deleted the old one and '
                            f'renamed {input_path} to {input_path + "_tmp"}.', to_print=C_TO_PRINT_PACKAGE_INFO)

        # Dealing with iterable_input_path
        if len(iterable_input_path) == 1:
            arg_dict = {arg_names[0]: iterable_input_path[0]}
            kwargs.update(arg_dict)

        # Running function
        print_info(f'Running {function_to_modify} in ffmpeg_python_utils package with kwargs: \n{kwargs}',
                   to_print=C_TO_PRINT_PACKAGE_INFO)
        res = function_to_modify(**kwargs)

        # If we rewrite the input_path, we have {input_path + "_tmp"} there. Deleting it.
        if files_to_delete_after_renaming:
            for file in files_to_delete_after_renaming:
                os.remove(file)
        return res

    return wrapper


def run_command(cmd, filter_str=None):
    # Get the current time
    start_time = datetime.datetime.now()
    # Check program
    is_ffprobe = cmd.startswith('ffprobe')
    # Construct cmd line
    cmd += ' -report' if C_TO_SAVE_LOGS else ''
    if C_TO_PRINT_ONLY_FFMPEG_ERRORS:
        cmd += ' -loglevel fatal'
    elif C_TO_PRINT_FFMPEG_DEBUG:
        cmd += ' -loglevel debug'
    else:
        cmd += ' -loglevel warning'
    cmd += ' -stats' if not is_ffprobe and not C_TO_PRINT_ONLY_FFMPEG_ERRORS else ''
    command_file = ''
    if len(cmd) > 8000:
        command_file = save_string_return_output(filter_str, 'cmd_tmp.txt')
        cmd = cmd.replace(f' -filter_complex "{filter_str}"', ' -filter_complex_script "cmd_tmp.txt"')
    # Print final command
    if not is_ffprobe: print_info(cmd, 'green', C_TO_PRINT_PACKAGE_INFO)
    # Run
    res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE).stdout
    # Clear tmp file
    if command_file:
        os.remove(command_file)
    # Calculate the time it took. Since ffprobe is lightning fast we do not use it there
    if not is_ffprobe:
        time_diff = datetime.datetime.now() - start_time
        time_diff_seconds = time_diff.total_seconds()
        print_info(f"Time it took (seconds): {time_diff_seconds:.2f}.", 'green', C_TO_PRINT_EXECUTION_TIME)
    return res


@process
def add_rectangle_to_video(input_path: str, output_path: str, start_times: list[float], durations: list[float],
                           x_y_coordinates: list[list], sizes: list[list], rect_colors: list[str],
                           opacities: list[float]) -> str:
    """
    Adds a rectangle to a video using ffmpeg.

    Args:
        input_path (str): The path to the input video file.
        output_path (str): The path to the output video file.
        start_times (list[float]): A list of start times in seconds for each rectangle.
        durations (list[float]): A list of durations for each rectangle.
        x_y_coordinates (list[list]): A list of [x,y] coordinates for each rectangle. Can be passed as built-in ffmpeg thing like 'iw/2'
        sizes (list[list]): A list of sizes [w,h] for each rectangle. Can be passed as built-in ffmpeg thing like ['iw/2', -1]  or as [int, int]
        rect_colors (list[str]): A list of colors for each rectangle. Can be passed as built-in ffmpeg color name (black, red etc.) or as hex string like 'FFFFFF'.
        opacities (list[float]): A list of opacities for each rectangle.

    Returns:
        str: The path to the output video file.
    """
    # Make lists equal
    start_times, durations, x_y_coordinates, sizes, rect_colors, opacities = make_lists_equal(
        start_times=start_times, durations=durations, x_y_coordinates=x_y_coordinates, sizes=sizes, colors=rect_colors,
        opacities=opacities)

    # Constructing filter str
    filter_str = ''
    for i in range(len(start_times)):
        filter_str += '' if i == 0 else f'[box{i}]'
        filter_str += f'drawbox=enable=\'between(t,{start_times[i]},{start_times[i] + durations[i]})\':x={x_y_coordinates[i][0]}' \
                      f':y={x_y_coordinates[i][1]}:w={sizes[i][0]}:h={sizes[i][1]}:color={rect_colors[i]}@{opacities[i]}:t=fill,' \
                      f'format=yuva420p[box{i + 1}];'
    # Run
    cmd = f'ffmpeg -y -i "{input_path}" -movflags +faststart ' \
          f'-filter_complex "{filter_str}" -map [box{len(start_times)}] ' \
          f'{C_CODEC_SETTINGS[C_CODEC]} ' \
          f'-c:a copy "{output_path}"'
    run_command(cmd, filter_str)
    return output_path


@process
def add_text_to_video(input_video_path: str, output_path: str, texts: list[str], fonts_paths: list[str],
                      font_sizes: list[int], font_colors: list[str], start_times: list[float], durations: list[float],
                      x_y_coordinates: list[list], fade_duration: float = 0, border_color='black',
                      border_width: int = 5):
    """
    Adds text to a video and saves it.

    Args:
        input_video_path (str): Path to the video to add texts to.
        output_path (str): Path to the new video.
        texts (list[str]): List of texts to add.
        fonts_paths (list[str]): List of paths to fonts. At windows should be like "C\:\\\\Windows\\\\Fonts\\\\Arial.ttf"
        font_sizes (list[int]): List of font sizes.
        font_colors (list): List of font colors. Can be passed as built-in ffmpeg color name (black, red etc.) or as hex string like 'FFFFFF'.
        start_times (list[float]): List of start times in seconds.
        durations (list[float]): List of durations in seconds.
        x_y_coordinates (list[list]): List of [x, y] coordinates. Can be passed as built-in ffmpeg thing like '(w-text_w)/2'
        fade_duration (float, optional): Duration of the fade effect.
        border_color (str, optional): Color of the border. Can be passed as built-in ffmpeg color name (black, red etc.) or as hex string like 'FFFFFF'.
        border_width (int, optional): Width of the border.

    Returns:
        str: Path to the new video (output_path).
    """
    # Making dict lists equal
    texts, fonts_paths, font_sizes, font_colors, x_y_coordinates, durations, start_times = \
        make_lists_equal(texts=texts, fonts=fonts_paths, font_sizes=font_sizes,
                         font_colors=font_colors, x_y_coordinates=x_y_coordinates,
                         durations=durations, start_times=start_times)
    # Setting files and filter strings
    filter_str = ''
    for i in range(len(texts)):
        fade_str = ''
        if fade_duration:
            fade_duration_to_use = min(fade_duration, durations[i] / 2)
            fade_str = f":alpha='if(lt(t,{start_times[i]}),0,if(lt(t,{start_times[i] + fade_duration_to_use}),(t-{start_times[i]})/{fade_duration_to_use},if(lt(t,{start_times[i] + fade_duration_to_use}),1,if(lt(t,{start_times[i] + durations[i]}),({fade_duration_to_use}-(t-{start_times[i] - fade_duration_to_use + durations[i]}))/{fade_duration_to_use},0))))'"
        border_str = ''
        if border_color:
            border_str += f':bordercolor={border_color}'
        if border_width:
            border_str += f':borderw={border_width}'
        filter_str += f'[0:v]' if i == 0 else f'[v{i}]'
        filter_str += f"drawtext=fontfile='{fonts_paths[i]}':text='{texts[i]}':fontsize={font_sizes[i]}:" \
                      f"fontcolor={font_colors[i]}{fade_str}:x={x_y_coordinates[i][0]}:y={x_y_coordinates[i][1]}{border_str}"
        if start_times is not None and durations is not None:
            filter_str += f":enable='between(t,{start_times[i]},{start_times[i] + durations[i]})'"
        filter_str += f'[v{i + 1}]'
        filter_str += ';'
    # Run
    cmd = f'ffmpeg -y -i "{input_video_path}" -movflags +faststart ' \
          f'-filter_complex "{filter_str}" -map [v{len(texts)}] -map 0:a {C_CODEC_SETTINGS[C_CODEC]} {output_path}'
    run_command(cmd, filter_str)

    return output_path


@process
def add_image_to_video(input_video_path: str, output_path: str, input_image_paths: list[str],
                       x_y_coordinates: list[list], start_times: list[float], durations: list[float],
                       img_goal_sizes: list, opacities: list = None, fade_duration: float = 0) -> str:
    """
    Adds images to a video at specified times and positions.

    Args:
        input_video_path (str): Path to the input video file.
        output_path (str): Path to the output video file.
        input_image_paths (list[str]): List of paths to the input image files.
        x_y_coordinates (list[list]): List of tuples specifying the x and y coordinates of each image.
        start_times (list[float]): List of start times for each image in seconds.
        durations (list[float]): List of durations for each image in seconds.
        img_goal_sizes (list): List of [w, h] specifying the width and height of each image after resizing. Can be passed as built-in ffmpeg thing like ['iw/2', -1]
        opacities (list, optional): List of opacities for each image.
        fade_duration (float, optional): Duration of fade in and fade out for each image in seconds.

    Returns:
        str: Path to the output video file.
    """
    # Make lists equal
    input_image_paths, x_y_coordinates, start_times, durations, img_goal_sizes, opacities = \
        make_lists_equal(input_image_paths=input_image_paths, x_y_coordinates=x_y_coordinates,
                         start_times=start_times, durations=durations,
                         img_goal_sizes=img_goal_sizes, opacities=opacities)

    # Constructing input str and complex filter
    files_str = f'-i "{input_video_path}"'
    filter_str_0 = ''
    filter_str_1 = ''
    for i in range(len(input_image_paths)):
        # Resizing img
        input_image_paths[i] = get_resized_image(input_image_paths[i], f'temp_image__{i}.png',
                                                 [img_goal_sizes[i][0], img_goal_sizes[i][1]])
        files_str += f' -loop 1 -i "{input_image_paths[i]}"'
        if_img_str = ''
        if fade_duration or (opacities and opacities[i] and opacities[i] != 1):
            filter_str_0 += f'[{i + 1}]'
            if_img_str = 'img'
        if fade_duration:
            fade_duration = min(fade_duration, durations[i] / 2)
            filter_str_0 += f'fade=t=in:st={start_times[i]}:d={fade_duration}:alpha=1,' \
                            f'fade=t=out:st={start_times[i] + durations[i] - fade_duration}:d={fade_duration}:alpha=1'
            filter_str_0 += ',' if opacities else ''
        if opacities and opacities[i] and opacities[i] != 1:
            filter_str_0 += f'format=pix_fmts=rgba,colorchannelmixer=aa={opacities[i]}'
        if fade_duration or (opacities and opacities[i] and opacities[i] != 1):
            filter_str_0 += f'[img{i + 1}];'

        filter_str_1 += f"[0]" if i == 0 else f"[bg{i - 1}]"
        filter_str_1 += f"[{if_img_str}{i + 1}]overlay=x={x_y_coordinates[i][0]}:y={x_y_coordinates[i][1]}:" \
                        f"enable='between(t,{start_times[i]},{start_times[i] + durations[i]})':shortest=1[bg{i}];"

    # Run command
    cmd = (f'ffmpeg -y {files_str} '
           f'-filter_complex "{filter_str_0 + filter_str_1}" '
           f'-map [bg{len(input_image_paths) - 1}]  -map 0 -map 0:a  -c:a copy {C_CODEC_SETTINGS[C_CODEC]} '
           f'-movflags +faststart "{output_path}" ')
    run_command(cmd, filter_str_0 + filter_str_1)

    # Remove temporary image file
    [os.remove(i) for i in os.listdir() if i.startswith('temp_image') and i.endswith('.png')]

    return output_path


@process
def add_audio_to_video(input_video_path: str, output_path: str, input_audio_paths: list[str],
                       sound_volumes: list[float], start_times: list[float], durations: list[float] = None) -> str:
    """
    Adds audio tracks to a video using ffmpeg.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to the output video file.
        input_audio_paths (list[str]): A list of paths to the input audio files.
        sound_volumes (list[float]): A list of sound volumes for each audio track.
        start_times (list[float]): A list of start times for each audio track in seconds.
        durations (list[float], optional): A list of durations for each audio track.

    Returns:
        str: The path to the output video file.
    """
    # Make lists equal
    input_audio_paths, sound_volumes, start_times, durations = make_lists_equal(
        input_audio_paths=input_audio_paths, sound_volumes=sound_volumes, start_times=start_times, durations=durations)

    # Setting files and filter strings
    filter_str_0 = ''
    filter_str_1 = ''
    files_str = f'-i "{input_video_path}"'
    for i in range(len(input_audio_paths)):
        files_str += f' -i "{input_audio_paths[i]}"'
        filter_str_0 += f'[{i + 1}:a]volume={sound_volumes[i]},adelay={start_times[i] * 1000}|{start_times[i] * 1000}'
        filter_str_0 += f', atrim=start=0:duration={durations[i]}' if durations and durations[i] else ''
        filter_str_0 += f'[a{i + 1}];'
        filter_str_1 += f'[a{i + 1}]'
    filter_str_1 += f'[0:a]amix=inputs={len(input_audio_paths) + 1}:duration=longest[audio_out]'

    # Run command
    cmd = f'ffmpeg {files_str} -movflags +faststart -filter_complex "{filter_str_0 + filter_str_1}" ' \
          f'-map 0:v -map "[audio_out]" -c:v copy -y "{output_path}"'
    run_command(cmd, filter_str_0 + filter_str_1)

    return output_path


@process
def add_colored_space_around_video(input_video_path: str, output_path: str, goal_size: list,
                                   to_resize_video: bool = True, color: str = 'black',
                                   x_y_coordinate: list = ('(ow-iw)/2', '(oh-ih)/2')) -> str:
    """
    Adds colored space around a video using ffmpeg.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to the output video file.
        goal_size (list): The desired size [w,h] of the output video. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]
        to_resize_video (bool, optional): Whether or not to resize the input video to fit the output size.
        color (str, optional): The color of the space around the video. Can be passed as built-in ffmpeg color name (black, red etc.) or as hex string like 'FFFFFF'.
        x_y_coordinate (list, optional): The x and y coordinates of the video within the output space. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]

    Returns:
        str: The path to the output video file.
    """
    codec_to_use = get_codec_meeting_constraints(goal_size)
    scale_w = (goal_size[0] if goal_size[0] < goal_size[1] else -1)
    scale_h = (goal_size[1] if goal_size[1] < goal_size[0] else -1)
    resize_str = f'scale={scale_w}:{scale_h},' if to_resize_video else ''
    filter_str = f'[0:v]{resize_str}pad=width={goal_size[0]}:height={goal_size[1]}:x={x_y_coordinate[0]}:y={x_y_coordinate[1]}:color={color}[v]'
    cmd = f'ffmpeg -y -i  "{input_video_path}" -movflags +faststart ' \
          f'-filter_complex "{filter_str}" -map "[v]" -map 0:a {C_CODEC_SETTINGS[codec_to_use]} "{output_path}"'

    run_command(cmd, filter_str)
    return output_path


@process
def add_blurred_space_around_video(input_video_path: str, output_path: str, goal_size: list,
                                   to_resize_video: bool = True, sigma: int = 20) -> str:
    """
    Adds blurred space around a video using ffmpeg.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to the output video file.
        goal_size (list): The desired size of the output video. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]
        to_resize_video (bool, optional): Whether or not to resize the input video to fit the output size.
        sigma (int, optional): The amount of blur to apply to the space around the video.

    Returns:
        str: The path to the output video file.
    """
    codec_to_use = get_codec_meeting_constraints(goal_size)
    scale_w = (goal_size[0] if goal_size[0] < goal_size[1] else -1)
    scale_h = (goal_size[1] if goal_size[1] < goal_size[0] else -1)
    scale_copy_w = (goal_size[0] if goal_size[0] > goal_size[1] else -1)
    scale_copy_h = (goal_size[1] if goal_size[1] > goal_size[0] else -1)

    resize_str = f'[original]scale={scale_w}:{scale_h}[original];' if to_resize_video else ''
    filter_str = f'[0:v]split[original][copy];{resize_str}' \
                 f'[copy]scale={scale_copy_w}:{scale_copy_h},crop={goal_size[0]}:{goal_size[1]},gblur=sigma={sigma}[blurred];' \
                 f'[blurred][original]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2'
    command = f'ffmpeg -y -i "{input_video_path}" -movflags +faststart -filter_complex "{filter_str}" {C_CODEC_SETTINGS[codec_to_use]} "{output_path}"'
    run_command(command, filter_str)
    return output_path


@process
def add_video_to_video(input_video_path: str, output_path: str, video_to_overlay_paths: list[str],
                       goal_sizes: list[list], x_y_coordinates: list[list],
                       start_times: list[float], durations: list[float],
                       opacities: list[float] = None, fade_duration: float = 0) -> str:
    """
    Adds a video overlay to a video using ffmpeg.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to the output video file.
        video_to_overlay_paths (list[str]): A list of paths to the video files to overlay.
        goal_sizes (list[list]): A list of sizes [w,h] for each overlay video. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]
        x_y_coordinates (list[list]): A list of [x,y] coordinates for each overlay video. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]
        start_times (list[float]): A list of start times for each overlay video in seconds.
        durations (list[float]): A list of durations for each overlay video.
        opacities (list[float], optional): A list of opacities for each overlay video.
        fade_duration (float, optional): The duration of the fade in/out effect for each overlay video.

    Returns:
        str: The path to the output video file.
    """
    # Make lists equal
    video_to_overlay_paths, goal_sizes, x_y_coordinates, start_times, durations, opacities = make_lists_equal(
        video_to_overlay_paths=video_to_overlay_paths, goal_sizes=goal_sizes, x_y_coordinates=x_y_coordinates,
        start_times=start_times, durations=durations, opacities=opacities)

    # Get codec to use according to constraints
    codec_to_use = get_codec_meeting_constraints(goal_sizes)

    # Construct input and filter strings
    filter_str_0 = '[0]format=pix_fmts=rgba[orig];'
    filter_str_1 = ''
    input_str = ''
    for i in range(len(video_to_overlay_paths)):
        input_str += f'-i "{video_to_overlay_paths[i]}" '

        filter_str_0 += f'[{i + 1}]'
        if fade_duration:
            fade_duration = min(fade_duration, durations[i] / 2)
            filter_str_0 += f'fade=t=in:st={start_times[i]}:d={fade_duration}:alpha=1,fade=t=out:st={start_times[i] + durations[i] - fade_duration}:d={fade_duration}:alpha=1,'
        if fade_duration or (opacities and opacities[i] and opacities[i] != 1):
            filter_str_0 += f'format=pix_fmts=rgba,colorchannelmixer=aa={opacities[i]},'
        filter_str_0 += f'scale={goal_sizes[i][0]}:{goal_sizes[i][1]}[v{i + 1}];'

        filter_str_1 += f'[orig]' if i == 0 else f'[fin{i}]'
        filter_str_1 += f'[v{i + 1}]overlay={x_y_coordinates[i][0]}:{x_y_coordinates[i][1]}[fin{i + 1}];'

    # Run command
    cmd = f'ffmpeg -y -i "{input_video_path}" {input_str} -movflags +faststart -filter_complex ' \
          f'"{filter_str_0 + filter_str_1}"' \
          f' -map [fin{len(video_to_overlay_paths)}] -map 0:a ' \
          f'{C_CODEC_SETTINGS[codec_to_use]}' \
          f' -c:a copy "{output_path}"'
    run_command(cmd, filter_str_0 + filter_str_1)

    return output_path


@process
def get_concantenated_videos(input_video_paths: list[str], output_path: str, effects: list[str] = None,
                             transition_durations: list[float] = None) -> str:
    """
    Concatenates multiple videos together using ffmpeg.
    If effects is False-like, then no transition_duration implemented.

    Args:
        input_video_paths (list[str]): A list of paths to the input video files.
        output_path (str): The path to the output video file.
        effects (list[str]): A list of transition effects to use between each video. See https://trac.ffmpeg.org/wiki/Xfade for options.
        transition_durations (list[float]): A list of durations for each transition.

    Returns:
        str: The path to the output video file.
    """
    # Make lists equal
    input_video_paths, effects, transition_durations = make_lists_equal(
        input_video_paths=input_video_paths, effects=effects, transition_durations=transition_durations)

    # Get input video durations
    video_durations = []
    sizes = []
    for input_video_path in input_video_paths:
        video_info = get_video_info(input_video_path)
        video_durations.append(video_info['duration'])
        sizes.append([video_info['width'], video_info['height']])
    # Checking codec
    codec_to_use = get_codec_meeting_constraints(sizes)


    # We need this only if effects present
    # Calculate offset time
    offsets = []
    if effects:
        for i in range(len(video_durations)):
            offset = video_durations[i] - transition_durations[i]
            offset += offsets[i - 1] if i > 0 else 0
            offsets.append(offset)

    # Construct input and filter str
    input_str = ''
    filter_vid_str = ''
    filter_aud_str = ''
    for i in range(len(input_video_paths)):
        input_str += f'-i "{input_video_paths[i]}" '
        if not effects:
            filter_vid_str += f'[{i}:v][{i}:a]'
    if effects:
        for i in range(len(input_video_paths) - 1):
            filter_vid_str += f'[0]' if i == 0 else f'[vv{i}]'
            filter_aud_str += f'[0:a]' if i == 0 else f'[afade{i}]'
            filter_vid_str += f'[{i + 1}:v]xfade=transition={effects[i]}:duration=1:offset={offsets[i]},format=yuv420p[vv{i + 1}];'
            filter_aud_str += f'[{i + 1}:a]acrossfade=d={transition_durations[i]}[afade{i + 1}];'

    filter_vid_str += f'concat=n={len(input_video_paths)}:v=1:a=1[outv]' if not effects else ''
    map_str = f'-map "[afade{len(input_video_paths) - 1}]" -map "[vv{len(input_video_paths) - 1}]"' if effects else '-map [outv]'

    # Run command
    cmd = f'ffmpeg -y {input_str}-movflags +faststart ' \
          f'-filter_complex "{filter_vid_str + filter_aud_str}" ' \
          f'{map_str} {C_CODEC_SETTINGS[codec_to_use]} ' \
          f'-fps_mode vfr "{output_path}"'
    run_command(cmd, filter_vid_str + filter_aud_str)
    return output_path


@process
def get_image_info(input_image_path: str) -> dict:
    """
    Get the width and height of a video file using ffprobe.

    Args:
        input_image_path (str): The path to the input video file.

    Returns:
        dict: A dictionary containing the width and height of the video.
    """
    cmd = f'ffprobe -v error -print_format json -show_format -show_streams {input_image_path}'
    ffprobe_output = run_command(cmd)
    ffprobe_data = json.loads(ffprobe_output)
    video_info = next((stream for stream in ffprobe_data['streams'] if stream['codec_type'] == 'video'), None)
    if video_info is None:
        raise Exception(f'No video stream found in {input_image_path}')
    width = int(video_info['width'])
    height = int(video_info['height'])
    return {'width': width, 'height': height}


@process
def get_audio_info(input_audio_file: str) -> dict:
    """
    Get the duration, bitrate, and sample rate of an audio file using ffprobe.

    Args:
        input_audio_file (str): The path to the input audio file.

    Returns:
        dict: A dictionary containing the duration, bitrate, and sample rate of the audio.
    """
    # Run ffprobe command to get information about the input audio file
    cmd = f'ffprobe -v error -print_format json -show_format -show_streams "{input_audio_file}"'
    ffprobe_output = run_command(cmd)
    # Parse the ffprobe output as JSON
    ffprobe_data = json.loads(ffprobe_output)
    # Get the audio stream information
    audio_stream = next((stream for stream in ffprobe_data['streams'] if stream['codec_type'] == 'audio'), None)
    # Get the audio duration in seconds
    duration = float(audio_stream['duration'])
    # Get the audio bitrate in kbps
    bitrate = int(audio_stream['bit_rate']) // 1000
    # Get the audio sample rate in Hz
    sample_rate = int(audio_stream['sample_rate'])
    return {'duration': duration, 'bitrate': bitrate, 'sample_rate': sample_rate}


@process
def get_video_info(input_video_path: str) -> dict:
    """
    Get the duration, width, height, and FPS of a video file using ffprobe.

    Args:
        input_video_path (str): The path to the input video file.

    Returns:
        dict: A dictionary containing the duration, width, height, and FPS of the video.
    """
    # Get the metadata of the video
    cmd = f'ffprobe -v error -print_format json -show_format -show_streams "{input_video_path}"'
    result = run_command(cmd)
    metadata = json.loads(result)
    # Get the duration of the video
    duration = float(metadata['format']['duration'])
    # Get the size and FPS of the video
    width, height, fps = None, None, None
    for stream in metadata['streams']:
        if stream['codec_type'] == 'video':
            width = stream['width']
            height = stream['height']
            fps = eval(stream['r_frame_rate'])
    return {'duration': duration, 'width': width, 'height': height, 'fps': fps}


@process
def get_cropped_video(input_video_path: str, output_path: str, size: list, x_y_coordinate: list) -> str:
    """
    Crop a video file to a specified size and position.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to save the cropped video file.
        size (list): A tuple containing the width and height of the cropped video. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]
        x_y_coordinate (list): A tuple containing the x and y coordinates of the top-left corner of the cropped video. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]

    Returns:
        str: The path to the cropped video file.
    """
    codec_to_use = get_codec_meeting_constraints(size)
    filter_str = f"crop={size[0]}:{size[1]}:{x_y_coordinate[0]}:{x_y_coordinate[1]}"
    # Crop the video
    cmd = f'ffmpeg -y -i "{input_video_path}" -movflags use_metadata_tags -movflags +faststart -filter_complex "{filter_str}" ' \
          f' -preset slow {C_CODEC_SETTINGS[codec_to_use]} -c:a copy "{output_path}" '
    run_command(cmd, filter_str)
    return output_path


@process
def get_resized_video(input_video_path: str, output_path: str, size: list) -> str:
    """
    Resize a video file to a specified size.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to save the resized video file.
        size (list): A tuple containing the width and height of the resized video. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]

    Returns:
        str: The path to the resized video file.
    """
    codec_to_use = get_codec_meeting_constraints(size)
    filter_str = f"[0:v]scale={size[0]}:{size[1]}[fin]"
    # Run command
    cmd = f'ffmpeg -y -i "{input_video_path}"  -movflags +faststart ' \
          f'-filter_complex "{filter_str}" -map [fin] -map 0:a -c:a copy {C_CODEC_SETTINGS[codec_to_use]} "{output_path}"'
    run_command(cmd, filter_str)
    return output_path


@process
def get_resized_image(input_image_path: str, output_path: str, size: list) -> str:
    """
    Resize an image file to a specified size.

    Args:
        input_image_path (str): The path to the input image file.
        output_path (str): The path to save the resized image file.
        size (list): A tuple containing the width and height of the resized image. Can be passed as built-in ffmpeg thing like ['iw/2', -1] or as [int, int]

    Returns:
        str: The path to the resized image file.
    """
    filter_str = f'scale={size[0]}:{size[1]}'
    # Run command
    cmd = f'ffmpeg -y -i "{input_image_path}"  -filter_complex "{filter_str}" -frames:v 1 -update 1 "{output_path}"'
    run_command(cmd, filter_str)
    return output_path


@process
def get_frame(input_video_path: str, output_path: str, time: float) -> str:
    """
    Extract a single frame from a video file at a specified time.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to save the extracted frame.
        time (float): The time at which to extract the frame in seconds.

    Returns:
        str: The path to the extracted frame.
    """
    cmd = f'ffmpeg -y -i "{input_video_path}" -ss {time} -frames:v 1  -update 1 "{output_path}"'
    run_command(cmd)
    return output_path


@process
def get_subclips_with_sound(input_video_path: str, output_path: str, subclip_times: list[list[float]]) -> str:
    """
    Extract subclips from a video file and concatenate them into a single video file with sound.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to save the concatenated video file.
        subclip_times (list[list[float]]): A list of lists containing the start and end times in seconds of each subclip in the format [[start1, end1], [start2, end2], ...].

    Returns:
        str: The path to the concatenated video file.
    """
    # Construct filter and input str
    input_str = ''
    filter_str = ''
    for i, (start, end) in enumerate(subclip_times):
        input_str += f'-ss {start} -to {end} -i "{input_video_path}" '
        filter_str += f'[{i}:v][{i}:a]'
    filter_str += f'concat=a=1:n={len(subclip_times)}:v=1[s0]'
    # Run command
    cmd = f'ffmpeg -y {input_str} -movflags +faststart ' \
          f'-filter_complex "{filter_str}" -map [s0] {C_CODEC_SETTINGS[C_CODEC]} "{output_path}"'
    run_command(cmd, filter_str)
    return output_path


@process
def get_audio_from_video(input_video_path: str, output_path: str = 'audio.wav') -> str:
    """
    Extracts the audio from a video file using ffmpeg and saves it to a WAV file.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to save the output audio file.

    Returns:
        str: The path to the output audio file.
    """
    cmd = f'ffmpeg -y -i "{input_video_path}" -vn -acodec pcm_s16le -ar 44100 -ac 2 "{output_path}"'
    run_command(cmd)
    return output_path


@process
def get_mirrored_video(input_video_path: str, output_path: str) -> str:
    """
    Creates a horizontally mirrored version of a video file using ffmpeg and saves it to a new file.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to save the output mirrored video file.

    Returns:
        str: The path to the output mirrored video file.
    """
    filter_str = "hflip"
    cmd = f'ffmpeg -y -i "{input_video_path}" -movflags +faststart ' \
          f'-vf "{filter_str}" {C_CODEC_SETTINGS[C_CODEC]} -c:a copy "{output_path}"'
    run_command(cmd)
    return output_path


@process
def get_rotated_video(input_video_path: str, output_path: str, degree: float) -> str:
    """
    Rotates a video file clockwise by a specified degree using ffmpeg and saves it to a new file.

    Args:
        input_video_path (str): The path to the input video file.
        output_path (str): The path to save the output rotated video file.
        degree (float): The degree to rotate the video clockwise.

    Returns:
        str: The path to the output rotated video file.
    """
    cmd = f'ffmpeg -y -i "{input_video_path}" -movflags +faststart ' \
          f'-vf "rotate={degree}*(PI/180)" {C_CODEC_SETTINGS[C_CODEC]} "{output_path}"'
    run_command(cmd)
    return output_path


@process
def get_video_from_picture(input_path: str, output_path: str, duration: float) -> str:
    """
    Creates a video file from a single image file using ffmpeg and saves it to a new file.

    Args:
        input_path (str): The path to the input image file.
        output_path (str): The path to save the output video file.
        duration (float): The duration of the output video file in seconds.

    Returns:
        str: The path to the output video file.
    """
    cmd = f'ffmpeg -y -loop 1 -i {input_path} {C_CODEC_SETTINGS[C_CODEC]} -t {duration} ' \
          f'-movflags +faststart -pix_fmt yuv420p {output_path}'
    run_command(cmd)
    return output_path
