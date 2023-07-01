from setuptools import setup

version = '0.0.5'

description = 'Python scripts constructing ffmpeg commands and running them by subprocess.'

long_description = ''' Python scripts constructing ffmpeg commands and running them by subprocess.
                    Check documentation: https://lionelcrowl.github.io/ffmpeg-python-utils/
                    '''

setup(
    name='ffmpeg_python_utils',
    version=version,

    author='LionelCrowl',
    author_email='mr.lihenko@yandex.ru',

    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/LionelCrowl/ffmpeg-python-utils',
    download_url=f'https://github.com/LionelCrowl/ffmpeg-python-utils/archive/v{version}.zip',

    license='MIT License, see LICENSE file',
    packages=['ffmpeg_python_utils'],
    install_requires=['numpy', 'librosa', 'matplotlib', 'pydub', 'scipy'],

    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
