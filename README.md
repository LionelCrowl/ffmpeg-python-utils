# Notes
This library provides functions that create and execute ffmpeg commands using subprocess in Python.

There are good libraries for video editing, such as Moviepy. However, I encountered multiple errors that I could not overcome. 

This library is straightforward but it works. During some activities, I ended up with a bunch of functions that create and start pure ffmpeg scripts with subprocess. So, I decided to publish it here. 

There may be some ```issues```. I'm still a novice with ffmpeg and would appreciate some feedback. The project has GPU acceleration set up for Nvidia and AMD, but I don't have an AMD card, so the project needs feedback here. Also, I don't have experience with Linux, so there may be some problems with paths. The project needs feedback here as well.

## Setting up
1) First, you need to install it:

   ```
   pip install ffmpeg-python-utils
   ```

2) Next, you need to extract the ffmpeg binary folder to the root project directory.

3) Check the settings in [config.py](https://lionelcrowl.github.io/ffmpeg-python-utils/configuration/).

4) Enjoy!

## Usage
Basic usage is similar to:
```
import ffmpeg_python_utils
output_path = ffmpeg_python_utils.function(input_path, output_path, **kwargs)
```

* Each function name starts with 'add' or 'get', so you can start typing this in your IDE to conveniently get hints.
* Functions do not drop audio stream.
* Functions receive arguments in the form of lists so that all changes to the video can be rendered at once.

## Documentation

You can find it [here](https://lionelcrowl.github.io/ffmpeg-python-utils/)