# IMAGE SOURCE: https://www.star.nesdis.noaa.gov/GOES/index.php

import platform
if platform.system() != 'Windows':
    print('Live Earth Wallpaper only supports Windows systems.')
    input('')
    exit()

# IMPORTS

from PIL import Image
import pyautogui
import traceback
import requests
import ctypes
import time
import os

# GLOBALS

IMAGE_URL = 'https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/5424x5424.jpg'
HASH_URL = 'https://cdn.star.nesdis.noaa.gov/GOES19/ABI/FD/GEOCOLOR/GOES19-ABI-FD-GEOCOLOR-10848x10848.tif.sha256'
IMAGES_DIR = 'images'
MAX_CACHE_SIZE: int = 10
TOP_MARGIN: int = 50 # in pixels
BOTTOM_MARGIN: int = 100 # in pixels
SCREEN_WIDTH: int
SCREEN_HEIGHT: int
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

latest_image_filename: str | None = None
latest_image_hash: bytes | None = None

# FUNCTION DEFINITIONS

def set_wallpaper() -> None:
    # Source: https://www.geeksforgeeks.org/how-to-change-desktop-background-with-python/

    image_path: str = os.path.abspath(os.path.join(IMAGES_DIR, latest_image_filename))
    ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 0x01 | 0x02)

def get_image() -> bool:
    global latest_image_filename
    global latest_image_hash

    # Cancel if nothing has changed
    r: requests.Response = requests.get(HASH_URL)
    new_hash: bytes = r.content
    if latest_image_hash is not None:
        if new_hash == latest_image_hash:
            return False
    latest_image_hash = new_hash

    # Create file paths
    formatted_time: str = time.strftime('%Y-%m-%d_%H-%M-%S')
    original_image_filename: str = 'original_' + formatted_time + '.jpg'
    edited_image_filename: str = 'edited_' + formatted_time + '.jpg'
    original_image_path: str = os.path.join(IMAGES_DIR, original_image_filename)
    edited_image_path: str = os.path.join(IMAGES_DIR, edited_image_filename)

    # Send request
    r: requests.Response = requests.get(IMAGE_URL)
    image_data: bytes = r.content

    # Write file
    with open(original_image_path, 'wb') as f:
        f.write(image_data)

    # Fit image to screen resolution
    new_im: Image = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0))
    im: Image = Image.open(original_image_path).convert('RGB')
    box_width: int = SCREEN_WIDTH
    box_height: int = SCREEN_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
    old_width, old_height = im.size
    if (old_width - box_width) > (old_height - box_height):
        new_width: int = box_width
        new_height: int = round((old_height / old_width) * box_width)
    else:
        new_width: int = round((old_width / old_height) * box_height)
        new_height: int = box_height
    im = im.resize((new_width, new_height))
    paste_x: int = round((box_width - new_width) / 2)
    paste_y: int = round((box_height - new_height) / 2) + TOP_MARGIN
    new_im.paste(im, (paste_x, paste_y))

    # Write file
    new_im.save(edited_image_path)
    latest_image_filename = edited_image_filename

    # Remove old images from cache if full
    cached_image_filenames: list[str] = [i for i in os.listdir(IMAGES_DIR) if i.startswith('original_')]
    cache_size: int = len(cached_image_filenames)
    if cache_size > MAX_CACHE_SIZE:
        cached_image_filenames.sort(reverse=True) # Because of the filenames' structure, this should sort by timestamp
        for _ in range(cache_size - MAX_CACHE_SIZE):
            filename: str = cached_image_filenames.pop()
            edited_filename: str = filename.replace('original_', 'edited_')
            os.remove(os.path.join(IMAGES_DIR, filename))
            if os.path.isfile(os.path.join(IMAGES_DIR, edited_filename)):
                os.remove(os.path.join(IMAGES_DIR, edited_filename))

    return True

# MAIN

def main() -> None:
    # Set terminal window title
    os.system('title Live Earth Wallpaper')

    # Create images directory
    if not os.path.isdir(IMAGES_DIR):
        os.mkdir(IMAGES_DIR)

    # Update wallpaper every minute
    while True:
        os.system('cls')
        print('LIVE EARTH WALLPAPER')
        print('')
        print(f'Screen resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}')
        print('')
        print('Downloading image...')
        # noinspection PyBroadException
        try:
            new_image: bool = get_image()
        except Exception as e:
            if isinstance(e, KeyboardInterrupt):
                exit()
            print('Failed to download image! Check your internet connection.')
            print('')
            print(traceback.format_exc())
        else:
            if new_image:
                print('Setting wallpaper...')
                # noinspection PyBroadException
                try:
                    set_wallpaper()
                except Exception as e:
                    if isinstance(e, KeyboardInterrupt):
                        exit()
                    print('Failed to set wallpaper!')
                    print('')
                    print(traceback.format_exc())
                else:
                    print(f'Set wallpaper to "{latest_image_filename}".')
            else:
                print('Image has not changed yet.')
        time.sleep(60)

if __name__ == '__main__':
    main()
