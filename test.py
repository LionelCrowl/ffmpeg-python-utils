import ffmpeg_python_utils
from ffmpeg_python_utils import add_text_to_video, get_subclips_with_sound, add_image_to_video, add_audio_to_video, \
    add_video_to_video, get_resized_video, get_video_info, get_audio_info, \
    add_blurred_space_around_video, \
    get_cropped_video, add_colored_space_around_video, get_concantenated_videos, get_image_info, \
    get_audio_from_video, get_frame, get_mirrored_video, get_rotated_video, get_video_from_picture, \
    add_rectangle_to_video, get_resized_image

if __name__ == '__main__':
    input_path = './test/test _uc_berkeley_salto.mp4'
    output_path = './test/'
    picture = './test/data-analysis-system.jpg'
    audio = './test/dj akeeni - snowfall comes again.mp3'

    # Getting subclips
    input_path = get_subclips_with_sound(input_video_path=input_path, output_path=output_path + 'test subclip .mp4',
                                         subclip_times=[[7, 12]])

    # Adding text
    add_text_to_video(input_path, output_path=output_path + 'with_text.mp4', texts=['hello', 'world'],
                      fonts_paths=['C\:\\\\Windows\\\\Fonts\\\\Arial.ttf'], font_sizes=[300, 200],
                      font_colors=['red', 'blue'], start_times=[0, 2], durations=[3, 4],
                      x_y_coordinates=[[0, 30], [60, 100]], fade_duration=4, border_color='black', border_width=3)

    # Adding picture
    add_image_to_video(input_video_path=input_path, input_image_paths=[picture, picture],
                       output_path=output_path + 'with pictures.mp4', x_y_coordinates=[[45, 100], [89, 200]],
                       start_times=[0, 3], durations=[2], img_goal_sizes=[[100, -1], [400, -1]], opacities=None,
                       fade_duration=0)

    # Adding audio
    add_audio_to_video(input_video_path=input_path, input_audio_paths=[audio],
                       output_path=output_path + 'with sound.mp4',
                       sound_volumes=[1.0], start_times=[2])
    add_audio_to_video(input_video_path=input_path, input_audio_paths=[audio],
                       output_path=output_path + 'with sound trim.mp4',
                       sound_volumes=[1.0], start_times=[0, 2], durations=[5, 3])

    # Adding colored space to video
    add_colored_space_around_video(input_video_path=input_path, output_path=output_path + 'padded video resized.mp4',
                                   goal_size=[1920, 1080], color='FFFFFF', to_resize_video=True)
    add_colored_space_around_video(input_video_path=input_path, output_path=output_path + 'padded video orig.mp4',
                                   goal_size=[1920, 1080], color='458b74', to_resize_video=False)
    add_colored_space_around_video(input_video_path=input_path,
                                   output_path=output_path + 'padded video 1280 resized.mp4',
                                   goal_size=[1280, 720 * 2], color='black', x_y_coordinate=[0, 720],
                                   to_resize_video=True)
    add_colored_space_around_video(input_video_path=input_path, output_path=output_path + 'padded video 1280 orig.mp4',
                                   goal_size=[1280, 720 * 2], color='black', x_y_coordinate=[0, 720],
                                   to_resize_video=False)

    # Adding blurred space to video
    add_blurred_space_around_video(input_video_path=input_path,
                                   output_path=output_path + 'with blurred space resized.mp4',
                                   goal_size=[1920, 1080], sigma=40, to_resize_video=True)
    add_blurred_space_around_video(input_video_path=input_path, output_path=output_path + 'with blurred space orig.mp4',
                                   goal_size=[1920, 1080], sigma=40, to_resize_video=False)

    # Adding video to video
    add_video_to_video(input_video_path=input_path,
                       video_to_overlay_paths=[output_path + 'with blurred space orig.mp4',
                                               output_path + 'padded video 1280 orig.mp4'],
                       goal_sizes=[[1280, -1], [400, -1]], x_y_coordinates=[[0, -720], [300, 400]], start_times=[1.5],
                       durations=[2], output_path=output_path + 'with overlayed video.mp4', fade_duration=1,
                       opacities=[0.5, 1])

    # Getting concantenated videos
    get_concantenated_videos([input_path, input_path, input_path], output_path + 'concantenated_with_transitions.mp4',
                             effects=['wiperight'], transition_durations=[1, 2])
    get_concantenated_videos([input_path, input_path, input_path],
                             output_path + 'concantenated_without_transitions.mp4')

    # Adding rectangle to video
    add_rectangle_to_video(input_path=input_path, output_path=output_path + 'with rectangle.mp4', start_times=[1, 0],
                           durations=[2, 5],
                           x_y_coordinates=[[700, 400], [0, 0]], sizes=[[200, 300], [400, 500]], rect_colors=['red'],
                           opacities=[0.4, 0.05])

    # Getting image info
    print(get_image_info(picture))

    # Getting audio info
    print(get_audio_info(audio))

    # Getting video info
    print(get_video_info(input_path))

    # Getting cropped video
    get_cropped_video(input_path, output_path + 'cropped video.mp4', size=[300, 400], x_y_coordinate=[300, 0])

    # Getting resized video
    get_resized_video(input_path, output_path + 'resized video .mp4', size=[1920, -1])

    # Getting resized picture
    get_resized_image(picture, output_path + '_resized picture.png', [100, -1])

    # Getting frames of the video
    get_frame(input_path, './test/frame_0.png', 2)

    # Getting audio from the video
    get_audio_from_video(input_path, output_path=output_path + 'audio test.wav')

    # Getting mirrorred video
    get_mirrored_video(input_path, output_path=output_path + 'mirrored.mp4')

    # Get rotated video
    get_rotated_video(input_path, output_path=output_path + 'rotated 15.mp4', degree=15)

    # Get video from picture
    get_video_from_picture(picture, output_path=output_path + 'video_from_picture.mp4', duration=8)
