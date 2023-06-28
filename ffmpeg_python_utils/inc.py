import re
from pathlib import Path
import os
from ffmpeg_python_utils.config import *

def print_info(msg: str, color='white', to_print: bool = True):
    if to_print:
        colors = {
            'black': '\033[30m',
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'reset': '\033[0m'
        }

        if color not in colors:
            color = 'white'

        print(f"{colors[color]}{msg}{colors['reset']}")


def make_lists_equal(**kwargs):
    max_len = max([len(kwargs[i]) if kwargs[i] else 0 for i in kwargs])
    for k, v in kwargs.items():
        if v and len(v) < max_len:
            print_info(f'List "{k}" is less than the longest ({max_len}). Appending the last element until it is equal.', 'red', C_TO_PRINT_PACKAGE_INFO)

    for k, v in kwargs.items():
        if v:
            while len(v) < max_len:
                v.append(v[-1])

    return kwargs.values()


def is_hex(s):
    return re.fullmatch(r"^[0-9a-fA-F]$", s or "") is not None

def replace_forbidden_chars(file_path, to_rename: bool):
    # List of forbidden characters in file names
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '%']

    # Get the parent folder and file name
    path_obj = Path(file_path)
    parent_folder = path_obj.parent
    file_name = path_obj.name

    # Replace spaces in the file name with underscores
    new_file_name = file_name.replace(' ', '_')

    # Check if the new file name contains any forbidden characters
    for char in forbidden_chars:
        if char in new_file_name:
            # Replace the forbidden character with an underscore
            new_file_name = new_file_name.replace(char, '_')

    # Check if the new file name starts or ends with a space, period, hyphen, or underscore
    if new_file_name.startswith((' ', '.', '-', '_')):
        new_file_name = new_file_name.lstrip(' .-_')
        new_file_name = '_' + new_file_name

    if new_file_name.endswith((' ', '.', '-', '_')):
        new_file_name = new_file_name.rstrip(' .-_')
        new_file_name = new_file_name + '_'

    # Rename the file if the new file name is different from the original file name
    if new_file_name != file_name:
        new_file_path = os.path.join(parent_folder, new_file_name)
        if to_rename:
            os.rename(file_path, new_file_path)
            print_info(f"{file_path} has been renamed to {new_file_path}", C_TO_PRINT_PACKAGE_INFO)
        else:
            print_info(f"{file_path} has been changed (not renamed) to {new_file_path}", C_TO_PRINT_PACKAGE_INFO)
        return str(new_file_path)
    else:
        print_info(f"{file_path} does not need to be renamed", C_TO_PRINT_PACKAGE_INFO)
        return file_path


def check_relative_position(position):
    if position[1] > 1.0 or position[1] < 0.0:
        raise ValueError(f'position must be between 0 and 1, got {position}')
    elif not isinstance(position[0], str) and (position[0] > 1.0 or position[0] < 0.0):
        raise ValueError(f'position must be between 0 and 1, got {position}')

def save_string_return_output(string, output_path:str):
    with open(output_path, 'w') as file:
        file.write(string)
    return output_path

def get_codec_meeting_constraints(sizes):
    """
    Function checks if current codec meets specific codec sizes constraint (min 145 for width/height for nvidia).
    Checks only if size is integer. It takes in account if size is -1.
    TODO i don't know amd constraints so project needs some update here
    :param sizes: list of pair-sizes or just pair-sizes
    :return: codec to use
    """
    if C_CODEC == 'cpu':
        return C_CODEC
    elif C_CODEC == 'amd':
        return C_CODEC
    elif C_CODEC == 'nvidia':
        use_cpu = False
        if isinstance(sizes[0], list):
            for size_pair in sizes:
                if isinstance(size_pair[0], int) and size_pair[0] != -1:
                    if size_pair[0] < 145:
                        use_cpu = True
                        break
                if isinstance(size_pair[1], int) and size_pair[1] != -1:
                    if size_pair[1] < 145:
                        use_cpu = True
                        break
        else:
            for size in sizes:
                if isinstance(size, int) and size != -1:
                    if size < 145:
                        use_cpu = True
                        break
        if use_cpu:
            print_info(
                f'Width or height is less then 145, which is not compatible with nvidia codec. '
                f'Using libx264 instead.',
                'red', C_TO_PRINT_PACKAGE_INFO)
            return 'cpu'
    return C_CODEC