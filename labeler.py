import os
import signal
import subprocess
import shutil
import tempfile
from collections import defaultdict


def partition(mappings):
    photos = defaultdict(list)
    videos = defaultdict(list)

    for position, images in mappings.items():
        for (p, i, base) in images:
            _, extension = os.path.splitext(p.lower())

            if extension == ".mov":
                videos[position].append((p, i, base))
            elif extension in [".cr2", ".nef"]:
                photos[position].append((p, i, base))
            else:
                print("WARNING: ignoring unknown file type %s" % extension)
                print("file path is: %s" % p)

    return photos, videos


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def to_jpg(origin, destination):
    cmd = [
        'sips',
        '-s',
        'format',
        'jpeg',
        origin,
        '--out',
        destination,
    ]

    subprocess.run(cmd)


def count_image_files(path):
    return len([p for p in os.listdir(path) if p.lower().endswith('.nef') or p.lower().endswith('.cr2')])


def main():
    base_dir = '/Users/mbildner/workspace/image_labeler/classify/'

    rug_paths = os.listdir(base_dir)

    for rug_path in rug_paths:
        # ignore hidden files
        if rug_path.startswith('.'):
            continue

        path = base_dir + rug_path
        raw_subpath = os.path.join(path, "raw")

        mappings = defaultdict(list)
        paths_to_delete = []

        images_to_process = count_image_files(path)
        processed = 0
        for img_path in os.listdir(path):
            absolute_image_path = r"" + os.path.abspath(
                os.path.join(
                    path, img_path
                )
            )

            if img_path.lower().endswith(".xmp"):
                paths_to_delete.append(img_path)

            elif img_path.lower().endswith(".mov"):
                mappings['Video'].append((
                    absolute_image_path,
                    -1,
                    os.path.basename(absolute_image_path),
                ))

            elif img_path.lower().endswith(".nef") or img_path.lower().endswith(".cr2"):
                processed += 1
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

                proc = subprocess.Popen([
                    "open",
                    "-a",
                    "Preview",
                    absolute_image_path
                ])

                pid = proc.pid

                prompt = "\n\n\nClassifying %s (%d/%d)\n\n" % (img_path,
                                                         processed, images_to_process)
                prompt += "Please choose: \n"
                prompt += "(or choose Q/q to quit)\n\n"
                for i, option in enumerate(classifier_options):
                    prior_choice = mappings.get(option)

                    if prior_choice:
                        prompt += "%d: %s (%d)\n" % (i, option,
                                                     len(prior_choice),)
                    else:
                        prompt += "%d: %s\n" % (i, option,)

                prompt += "\n> "

                option_index = None
                while option_index == None:
                    clear()
                    unprocessed = input(prompt).strip()
                    if unprocessed in ['Q', 'q']:
                        import sys
                        print("exiting...")
                        sys.exit(0)
                    else:
                        try:
                            possible_index = int(unprocessed)

                            if possible_index <= len(classifier_options):
                                option_index = possible_index

                        except ValueError as e:
                            print("invalid choice, please try again")

                choice = classifier_options[option_index]

                mappings[choice].append((
                    absolute_image_path,
                    option_index,
                    os.path.basename(absolute_image_path),
                ))

                option_index = None
                # this is the wrong pid, need to find the pid created for preview. not by `open`
                os.kill(proc.pid, signal.SIGKILL)

        if mappings:
            if not os.path.isdir(raw_subpath):
                print("creating raw subdirectory")
                os.mkdir(raw_subpath)
            else:
                print("raw subdirectory exists already, no need to create")

            photos, videos = partition(mappings)

            for position, images in photos.items():
                for same_position_counter, (p, i, base) in enumerate(images):
                    _, ext = os.path.splitext(base)

                    same_position_label = ""
                    if same_position_counter > 0:
                        same_position_label = "(copy_%d)" % same_position_counter

                    pretty = "%s-%s_%s%s%s" % (rug_path, position,
                                               str(i), same_position_label, ext,)
                    working_copy_target = os.path.join(path, pretty)

                    os.rename(
                        src=p,
                        dst=working_copy_target,
                    )

            video_counter = len(photos) - 1
            for position, video_list in videos.items():
                for (p, _, base) in video_list:

                    i = video_counter
                    i += 1

                    _, ext = os.path.splitext(base)
                    pretty = "%s-Video_%d%s" % (rug_path, i, ext,)
                    working_copy_target = os.path.join(path, pretty)

                    os.rename(
                        src=p,
                        dst=working_copy_target,
                    )

                    shutil.copyfile(
                        src=working_copy_target,
                        dst=os.path.join(raw_subpath, pretty)
                    )

            for p in paths_to_delete:
                full_path = os.path.join(path, p)
                print("deleting file %s" % full_path)
                os.remove(full_path)


if __name__ == '__main__':
    main()
