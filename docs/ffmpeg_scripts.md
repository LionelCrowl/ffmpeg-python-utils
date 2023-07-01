# FFmpeg scripts

### Process

Each function is first processed by the ```@process``` decorator.

* It checks if the file at input_path can be accessed and read.

* If needed according config, it can rename the input file and change the output to avoid using special symbols (
  although it may not be necessary since we can use quotes around file names).

* Then it checks if we rewrite ```input_path``` since it is not possible to do directly with ffmpeg. If so, it renames
  the input path as 'fn_tmp' and deletes it after function execution.

### Function

* It makes the plural-form arguments equal in length (see below).

* It constructs a command line to be run by subprocess.

* If the length of the command line exceeds 8000, the filter part of the cmd string is saved to cmd_tmp.txt and run by
  -filter_complex_script.

### Arguments

* Arguments whose names end with 's' (plural form) should get a list. If you can pass a list, pass it. This was done on
  purpose to avoid rerendering a 2-hour video each time we make a minor change - we pass the full list of needed
  changes.
* If the length of the plural-form arguments differs from each other, the function will make them equal in length by
  adding the last element to each of them.

    ```
  font_colors = ['red']
  font_sizes = [500, 200]
  # Making them equal
  font_colors = ['red', 'red']
  font_sizes = [500, 200]
    ```

* Path arguments should be passed as strings.
* The argument ```size``` should contain ```[width, height]```, and ```sizes``` should contain a list of them.
* The argument ```x_y_coordinate``` should contain ```[x_coordinate, y_coordinate]```, and ```x_y_coordinates``` should
  contain a list of them.
* ```fonts``` should be passed with full path like ```['C\:\\\\Windows\\\\Fonts\\\\Arial.ttf']```, overwise ffmpeg raise
  error.
* ```colors``` should be passed as strings like 'FFFFFF' or as defaults colors like 'white'
* You can pass ffmpeg things like "1920, -1', 'red', '(w-text_w)/2' to size, color, x_y_coordinate, respectively.
  Check [ffmpeg documentation](https://ffmpeg.org/documentation.html)
*

### Code

::: ffmpeg_python_utils.main