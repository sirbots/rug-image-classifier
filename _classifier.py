import os
from PIL import Image
import numpy as np


PURE_WHITE = 255
WHITE_PIXEL_TOLERANCE = 2

CORNER_DARK = 150
CORNER_DARK_PIXEL_TOLERANCE = 10


# of 1145px wide, left, top, right, bottom 45 should be white pixels
# 1/25 on left/right
# 1/17 on top/bottom

# NW, NE anchored white boxes proportions 1/4.5


def _get_top_border(image):
    width, height = image.size
    left = 0
    top = 0
    bottom = float(height) / 25
    right = width

    return image.crop((left, top, right, bottom))


def _get_bottom_border(image):
    width, height = image.size
    left = 0
    top = 16 * (float(height) / 17)
    bottom = height
    right = width

    return image.crop((left, top, right, bottom))


def _get_left_border(image):
    width, height = image.size
    left = 0
    top = 0
    bottom = height
    right = float(width) / 25

    return image.crop((left, top, right, bottom))


def _get_right_border(image):
    width, height = image.size
    left = 24 * (float(width) / 25)
    top = 0
    bottom = height
    right = width

    return image.crop((left, top, right, bottom))


def _get_top_right_box(image):
    width, height = image.size
    top = 0
    bottom = height * 1/4
    left = width * 4/5
    right = width

    return image.crop((left, top, right, bottom))


def _get_top_left_box(image):
    width, height = image.size
    top = 0
    bottom = height * 1/4
    left = 0
    right = width * 1/5

    return image.crop((left, top, right, bottom))


def _has_twin_white_top_corner_boxes(image):
    top_left_box = _get_top_left_box(image)
    top_right_box = _get_top_right_box(image)

    return all([
        _image_is_white(top_left_box),
        _image_is_white(top_right_box)
    ])


def _image_is_corner_dark(image):
    return CORNER_DARK - np.average(image) <= CORNER_DARK_PIXEL_TOLERANCE


def _image_is_white(image):
    return PURE_WHITE - np.average(image) <= WHITE_PIXEL_TOLERANCE


def _has_white_1_25th_border(image):

    left = _average_color(_get_left_border(image))
    right = _average_color(_get_right_border(image))
    top = _average_color(_get_top_border(image))
    bottom = _average_color(_get_bottom_border(image))

    cumulative_average = np.average([left, right, top, bottom])

    left_is_white = _image_is_white(left)
    right_is_white = _image_is_white(right)
    top_is_white = _image_is_white(top)
    bottom_is_white = _image_is_white(bottom)
    cumulative_average_is_white = _image_is_white(cumulative_average)

    return all([
        left_is_white,
        right_is_white,
        top_is_white,
        bottom_is_white,
        cumulative_average_is_white,
    ])


def _average_color(image):
    height, width, _ = np.shape(image)
    # calculate the average color of each row of our image
    avg_color_per_row = np.average(image, axis=0)
    # calculate the averages of our rows
    bgr_avg_colors = np.average(avg_color_per_row, axis=0)
    int_averages = np.array(bgr_avg_colors, dtype=np.uint8)
    return int_averages


def _get_bottom_right_corner(image):
    # 1/6 width
    # 1/2 height

    width, height = image.size
    top = 1/2 * height
    bottom = height
    left = width * 5/6
    right = width

    return image.crop((left, top, right, bottom))


def _get_bottom_left_corner(image):
    # 1/6 width
    # 1/2 height

    width, height = image.size
    top = 1/2 * height
    bottom = height
    left = 0
    right = width * 1/6

    return image.crop((left, top, right, bottom))


test_image_dir = '/Users/mbildner/workspace/image_labeler/examples/Finished Example/05110-0002/'


image_paths = [
    os.path.join(test_image_dir, p) for p
    in os.listdir(test_image_dir)
    if p.endswith('.jpg')
]

images = {
    "Over": [],
    "Angle": [],
    "Corner_Dark": [],
}

for path in image_paths:
    img = Image.open(path)

    if _has_white_1_25th_border(img):
        if _has_twin_white_top_corner_boxes(img):
            images.get("Over").append(path)
        else:
            images.get("Angle").append(path)
    else:
        bl = _get_bottom_left_corner(img)
        br = _get_bottom_right_corner(img)

        print(path)
        print("_image_is_corner_dark(bl)")
        print(_image_is_corner_dark(bl))
        
        print("_image_is_corner_dark(br)")
        print(_image_is_corner_dark(br))
        if _image_is_corner_dark(bl) and _image_is_corner_dark(br):
            images.get("Corner_Dark").append(path)

        # _get_bottom_left_corner


print(images)
