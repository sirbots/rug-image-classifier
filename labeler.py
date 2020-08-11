#!/usr/bin/python 

import sys

if sys.version_info.major != 3:
    print("WARNING: This program requires python 3 to run,")
    print("you ran it with the following python version:")
    print()
    print(sys.version)
    sys.exit(1)

from tkinter import Tk, Label, Frame, PhotoImage, Listbox, END, NW, NE, TOP, BOTH, VERTICAL, LEFT, HORIZONTAL, Button, Entry, mainloop, Canvas

from contextlib import contextmanager
import os
import tempfile
import subprocess
from itertools import cycle
from collections import defaultdict
import shutil
import csv

base = os.environ.get('BASE')

if not base:
    print("WARNING: Run the script like this:")
    print()
    print("Get the path name of your 'classify' directory")
    print("(instructions https://osxdaily.com/2015/11/05/copy-file-path-name-text-mac-os-x-finder/)")
    print()
    print("Then open your terminal, and run this command (replacing the string to the right of BASE with your path - in single quotes)")
    print()
    print("BASE='/Users/sjobs/Documents/classify/' python labeler.py")
    print()
    sys.exit(1)

if base and not os.path.isdir(base):
    print("WARNING: BASE must point to a valid directory")
    print()
    print("You provided '%s'" % base)
    print()
    sys.exit(1)



raw_subpath_name = 'raw'

raw_image_extensions = ['.tif']

FILE_CHANGE_LOG = []

def _dump_logs(rug):
    csv_columns = ["operation", "source", "target"]
    csv_file_name = "%s_files_change_log.csv" % rug
    
    try:
        with open(csv_file_name, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in FILE_CHANGE_LOG:
                writer.writerow(data)
    except Exception as e:
        print("WARNING: failed to write logs, error was:")
        print(e)

@contextmanager
def temporary_png_copies():
    global base
    global raw_image_extensions
    global raw_subpath_name

    directories = os.listdir(base)
    rugs = [p for p in directories if not p.startswith('.')]

    assert len(rugs) == 1, 'You may only work on one rug at a time'

    rug_base = os.path.join(base, rugs[0])
    img_paths = [os.path.join(rug_base, p) for p in os.listdir(rug_base)]

    if raw_subpath_name in os.listdir(rug_base):
        print("WARNING: looks like there is already a '%s' directory for this rug - canceling" %
              raw_subpath_name)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        image_map = {}

        for p in img_paths:
            if not p.startswith('.'):
                name, extension = os.path.splitext(p.lower())
                if extension in raw_image_extensions:
                    image_map[os.path.split(
                        name)[-1]] = os.path.join(rug_base, p)

        sips_commands = []
        for p in image_map.values():
            name, extension = os.path.splitext(p.lower())
            if extension in raw_image_extensions:
                cmd = 'sips -Z 600 -s format png -s formatOptions 20 {original_path} --out {target_dir}'.format(
                    original_path=p,
                    target_dir=str(tmpdir),
                )
                sips_commands.append(cmd)

        print("beginning generating thumbnails (can take up to 30 seconds)")
        procs = [subprocess.Popen(
            c.split(' '),
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        ) for c in sips_commands]

        for proc in procs:
            proc.communicate()

        print("finished generating thumbnails")

        for p in os.listdir(tmpdir):
            name, extension = os.path.splitext(p.lower())
            image_map[name] = dict(
                original=image_map.get(name),
                thumbnail=os.path.join(tmpdir, p),
                name=name,
            )

        yield list(image_map.values()), rugs[0]


def rename_files(mappings, rug_id):
    global base
    global raw_subpath_name

    rug_path = os.path.join(base, rug_id)
    raw_subpath = os.path.join(rug_path, raw_subpath_name)

    rug_file_paths = os.listdir(rug_path)

    os.mkdir(raw_subpath)

    counter = defaultdict(lambda: 0)
    for mapping in mappings:
        position = mapping.get('position')
        counter[position] += 1

        target_file_name = "{rug_id}-{index}-{position}".format(
            rug_id=rug_id,
            index=mapping.get('index'),
            position=position,
        )

        count = counter.get(position)
        if count > 1:
            target_file_name += '(copy_%d)' % (count - 1)

        target_file_name += mapping.get('extension')

        source = mapping.get('original')
        target = os.path.join(raw_subpath, target_file_name)
        FILE_CHANGE_LOG.append({
            "operation": "rename",
            "source": source,
            "target": target,
        })
        os.rename(
            src=source,
            dst=target,
        )

    for p in os.listdir(rug_path):
        abspath = os.path.join(rug_path, p)
        if not os.path.isdir(abspath):
            _, ext = os.path.splitext(p.lower())
            if ext not in raw_image_extensions:
                FILE_CHANGE_LOG.append({
                    "operation": "delete",
                    "source": abspath,
                    "target": None,
                })
                os.remove(abspath)

    for position, images in photos.items():
        for same_position_counter, (p, i, base) in enumerate(images):
            _, ext = os.path.splitext(base)

            same_position_label = ""
            if same_position_counter > 0:
                same_position_label = "(copy_%d)" % same_position_counter

            pretty = "%s-%s_%s%s%s" % (rug_path, str(i), position,
                                       same_position_label, ext,)
            working_copy_target = os.path.join(path, pretty)

            os.rename(
                src=p,
                dst=working_copy_target,
            )

    for p in paths_to_delete:
        full_path = os.path.join(path, p)
        print("deleting file %s" % full_path)
        os.remove(full_path)


classifier_options = [
    'Over',
    'Angle',
    'Corner_Light',
    'Corner_Grey',
    'Corner_Dark',
    'Back',
    'Detail',
    'Lifestyle',
]


def render_option_labels(
    classified,
    options,
):
    for i, option in enumerate(classifier_options):
        count = len([
            classified for classified in classified_images if classified.get("position") == option
        ])

        label_text = "{index}: {option} {count}".format(
            index=i,
            option=option,
            count="(%d)" % count if count else "",
        )

        option_labels[i].configure(text=label_text)
        option_labels[i].text = label_text


with temporary_png_copies() as (thumbnail_list, rug_id):
    window = Tk()
    window.title('Image labeler')
    window.geometry('1000x1000')

    thumbnails = iter(thumbnail_list)

    classified_images = []
    option_labels = []

    _current_image = next(thumbnails)
    _current_option = None
    _latest_position = None

    image = PhotoImage(file=_current_image.get("thumbnail"))
    label = Label(window, bd=5, height=1000, width=400, image=image)
    label.pack(side=LEFT, anchor=NW)

    def render_next_thumbnail():
        global _current_image
        global _latest_position
        global label
        global option_labels
        global classifier_options

        try:
            _current_image['index'] = len(classified_images)

            _, extension = os.path.splitext(_current_image.get('original'))
            _current_image['extension'] = extension

            classified_images.append(_current_image)
            _current_image = next(thumbnails)
            thumbnail_path = _current_image.get("thumbnail")
            image.configure(file=thumbnail_path)
            image.file = thumbnail_path
            _highlight(None)

            render_option_labels(
                classified=classified_images,
                options=classifier_options,
            )

        except StopIteration:
            _current_image = None
            _latest_position = None
            _highlight(None)
            label.pack_forget()

            for o in option_labels:
                o.forget()

            rename_files(classified_images, rug_id)
            _dump_logs(rug=rug_id)

            print("Done moving files, quitting")
            sys.exit(0)

    def _highlight(position):
        index = classifier_options.index(position) if position else -1
        for i, label in enumerate(option_labels):
            if i == index:
                label.configure(bg='red')
            else:
                label.configure(bg='white')

    def handle_backspace_press(event):
        _highlight(None)

    def handle_enter_press(event):
        global _latest_position
        global _current_image

        if not _latest_position:
            return

        if not _current_image:
            return

        _current_image['position'] = _latest_position
        _latest_position = None
        render_next_thumbnail()

    def handle_up_press(event):
        global _latest_position

        if _latest_position is None:
            _latest_position = classifier_options[-1]
        else:
            i = classifier_options.index(_latest_position)

            if i != 0:
                _latest_position = classifier_options[i - 1]

        _highlight(_latest_position)

    def handle_down_press(event):
        global _latest_position

        if _latest_position is None:
            _latest_position = classifier_options[0]
        else:
            i = classifier_options.index(_latest_position)

            if i != len(classifier_options) - 1:
                _latest_position = classifier_options[i + 1]

        _highlight(_latest_position)

    def handle_key_press(event):
        global _latest_position

        try:
            max_index = len(classifier_options)
            index = int(event.char)
            position = classifier_options[index]

            _latest_position = position
            _highlight(_latest_position)

        except (IndexError, ValueError):
            print("You must choose a number between 0 and %d" % max_index)

        # render_next_thumbnail()
        # img2 = PhotoImage(file='buttons.png')
        # label.configure(image=img2)
        # label.image = img2

    window.bind("<Key>", handle_key_press)
    window.bind("<Return>", handle_enter_press)
    window.bind("<BackSpace>", handle_backspace_press)
    window.bind("<Up>", handle_up_press)
    window.bind("<Down>", handle_down_press)

    options_list_frame = Frame(window)
    options_list_frame.pack(side=LEFT, anchor=NE)

    def make_label_click_handler(index):

        def _handler(event):
            global _latest_position
            _latest_position = classifier_options[index]
            _highlight(_latest_position)

        return _handler

    for i, opt in enumerate(classifier_options):
        choice = Label(
            options_list_frame,
            text='',
            anchor='w',
        )
        option_labels.append(choice)
        choice.bind('<Button-1>', make_label_click_handler(i))
        choice.pack(fill=BOTH)

    render_option_labels(
        classified=[],
        options=option_labels,
    )

    window.mainloop()
