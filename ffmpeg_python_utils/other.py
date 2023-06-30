import os
import matplotlib.pyplot as plt
from pydub.silence import split_on_silence
import librosa
from scipy import signal
import numpy as np
import pickle
from pydub import AudioSegment
import hashlib
from functools import wraps
import inspect
from .inc import print_info
from .config import C_TO_PRINT_PACKAGE_INFO, C_TIME_AMONG_NEIGHBOUR_PEAKS


def cache_results(function_to_modify):
    # Caches results from find_offsets just in case. Takes in account hash + kwargs.
    # Saves cache to "cached_offset_searches.pickle" file.

    @wraps(function_to_modify)
    def wrapper(*args, **kwargs):

        # Get the names of the arguments in the decorated function
        arg_names = inspect.getfullargspec(function_to_modify).args
        # Create a dictionary of keyword arguments based on the positional arguments
        kwargs.update(dict(zip(arg_names, args)))

        within_file = kwargs['within_file']
        find_file = kwargs['find_file']

        # load cached searches if we have them
        cached_searches = None
        if os.access('cached_offset_searches.pickle', os.R_OK):
            with open('cached_offset_searches.pickle', 'rb') as file:
                cached_searches = pickle.load(file)

        current_info = kwargs
        current_info['hash_within'] = get_hash_for_audio(within_file)
        current_info['hash_find'] = get_hash_for_audio(find_file)

        if cached_searches:
            # Search for the current call dict in the cached ones
            time_codes = [i for i in cached_searches if
                          all(k in i and v == i[k] for k, v in kwargs.items())]
            if time_codes:
                current_info.update({"time_codes": time_codes[0]["time_codes"]})
                print(f'Found that this audio was already searched for offsets with the same parameters: '
                      f'{current_info}')
                return time_codes[0]['time_codes']

        hash_within = kwargs.pop('hash_within')
        hash_find = kwargs.pop('hash_find')
        # function itself
        res = function_to_modify(**kwargs)

        # cache the result
        cached_search = {'hash_within': hash_within, **kwargs, 'time_codes': res, 'hash_find': hash_find}
        if cached_searches:
            cached_searches.append(cached_search)
        else:
            cached_searches = [cached_search]

        with open('cached_offset_searches.pickle', 'wb') as file:
            pickle.dump(cached_searches, file)

        return res

    return wrapper


def get_hash_for_audio(input_path):
    from ffmpeg_python_utils import get_audio_from_video
    # Extract the video file
    audio_name = get_audio_from_video(input_path, 'tmp_hash_audio.wav')
    # Read the audio file as binary data
    with open(audio_name, "rb") as f:
        audio_data = f.read()
    # Generate the hash value for the audio
    hash_object = hashlib.sha256(audio_data)
    # Get hash of the current audio
    os.remove('tmp_hash_audio.wav')
    return hash_object.hexdigest()


def remove_silence_from_audio_file(input_path: str, output_path: str, audio_format: str = 'wav',
                                   min_silence_len: int = 100, silence_thresh: int = -45,
                                   keep_silence: int = 50) -> str:
    """
    Removes silence from audio file. Results are cached taking in account hash of the input files and kwargs passed.

    Args:
        input_path (str): The path to the audio file.
        output_path (str): The path to the directory where the edited audio files will be saved.
        audio_format (str, optional): The format of the audio output.
        min_silence_len (int, optional): The minimum length of silence to be removed, in milliseconds.
        silence_thresh (int, optional): The threshold for silence, in decibels.
        keep_silence (int, optional): The length of silence to keep at the beginning and end of the audio file, in milliseconds.

    Returns:
        str: output_path
    """
    sound = AudioSegment.from_file(input_path, format=audio_format)
    audio_chunks = split_on_silence(sound, min_silence_len=min_silence_len, silence_thresh=silence_thresh,
                                    keep_silence=keep_silence)
    combined = AudioSegment.empty()
    for chunk in audio_chunks:
        combined += chunk
    combined.export(output_path, format=audio_format)
    return output_path


def delete_neighbors(input_list):
    if not input_list:
        return input_list
    input_list.sort()
    output_list = [input_list[0]]
    for i in range(1, len(input_list)):
        if input_list[i] - output_list[-1] >= C_TIME_AMONG_NEIGHBOUR_PEAKS:
            output_list.append(input_list[i])
    return output_list


@cache_results
def find_offsets(within_file: str, find_file: str, multiplier: float, window: int = 2, number: int = None,
                 max_tries_number: int = 80, to_print_plots=False) -> list:
    """
    Finds time codes of appearance audio of find_file in within_file using scipy.

    Args:
        within_file (str): path to the audio file to search within
        find_file (str): path to the audio file to search for
        multiplier (float): a multiplier used to calculate the prominence of peaks in the correlation signal. The bigger you set it, the less time codes function returns.
        window (int): the length of find_file audio to use for the correlation (in seconds)
        number (int): the goal number of offsets to return
        max_tries_number (int): maximum number of tries to find the number
        to_print_plots (bool): whether to print plot before proceeding

    Returns:
        list: list of time codes
    """

    y_within, sr_within = librosa.load(within_file, sr=None)
    y_find, _ = librosa.load(find_file, sr=sr_within)
    c = signal.correlate(y_within, y_find[:sr_within * window], mode='valid', method='fft')
    if number is not None and number < 1:
        print_info(f'Number of peaks you are looking for is {number}. Returning empty list.', 'red',
                   C_TO_PRINT_PACKAGE_INFO)
        return []

    elif number == 1:
        c = np.argmax(c)
        if to_print_plots:
            plot_offsets(c, find_file)
        peak = round(c / sr_within, 2)
        return [peak]
    else:
        prominence = int(c[np.argmax(c)] * multiplier)
        counter = 0
        while True:
            try:
                peaks, _ = signal.find_peaks(c, prominence=prominence)
                points_of_time = [round(peak / sr_within, 2) for peak in peaks]
                points_of_time = delete_neighbors(points_of_time)
                if to_print_plots:
                    plot_offsets(c, find_file)
                if counter > max_tries_number:
                    if C_TO_PRINT_PACKAGE_INFO: print(
                        f'Max try number reached. Returning the last time codes. {points_of_time}')
                    return points_of_time
                if number and number != len(points_of_time):
                    print_info(
                        f'Try number № {counter}. Looking for peaks. The goal number is {number}, the number we got is {len(points_of_time)}. Prominence: {prominence}',
                        'white', C_TO_PRINT_PACKAGE_INFO)
                    if C_TO_PRINT_PACKAGE_INFO: print_info(f'Time codes we got: {points_of_time}', 'white')
                    if number > len(points_of_time):
                        diff = number - len(points_of_time)
                        prominence *= 0.80 if diff > 5 else 0.95
                    else:
                        prominence *= 1.01
                    counter += 1
                    continue
                print_info(f'Found specified number={number}. Offsets: {points_of_time}', 'white',
                           C_TO_PRINT_PACKAGE_INFO)
                return points_of_time
            except IndexError:
                prominence *= 0.8
                counter += 1


def plot_offsets(c, find_file):
    fig, ax = plt.subplots()
    ax.set_title(f"Offsets of {find_file}")
    ax.plot(c)
    plt.show()
    plt.close()
