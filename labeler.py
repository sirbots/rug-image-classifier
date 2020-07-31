import os
import signal
import subprocess
import shutil
import tempfile


def partition(mappings):
    photos = {}
    videos = {}

    for position, (p, i, base) in mappings.items():
        _, extension = os.path.splitext(p.lower())

        if extension == ".mov":
            videos[position] = (p, i, base)
        elif extension in [".cr2", ".nef"]:
            photos[position] = (p, i, base)
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


def main():
    base_dir = '/Users/mbildner/workspace/image_labeler/classify/'

    rug_paths = os.listdir(base_dir)

    for rug_path in rug_paths:
        # ignore hidden files
        if rug_path.startswith('.'):
            continue

        path = base_dir + rug_path
        raw_subpath = os.path.join(path, "raw")

        mappings = {}
        paths_to_delete = []

        with tempfile.TemporaryDirectory() as temp_jpg_dir:
            for img_path in os.listdir(path):
                absolute_image_path = r"" + os.path.abspath(
                    os.path.join(
                        path, img_path
                    )
                )

                if img_path.lower().endswith(".xmp"):
                    paths_to_delete.append(img_path)

                elif img_path.lower().endswith(".mov"):
                    mappings['Video'] = (
                        absolute_image_path,
                        -1,
                        os.path.basename(absolute_image_path),
                    )

                elif img_path.lower().endswith(".nef") or img_path.lower().endswith(".cr2"):
                    temp_jpg_image_path = os.path.join(
                        temp_jpg_dir,
                        img_path,
                    ).replace(".nef", ".jpg").replace(".cr2", ".jpg")

                    cmd = [
                        "sips",
                        "-s",
                        "format",
                        "jpeg",
                        "-s",
                        "formatOptions",
                        "10",
                        absolute_image_path,
                        "--out",
                        temp_jpg_image_path,
                    ]

                    subprocess.run(cmd)

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
                        # absolute_image_path
                        temp_jpg_image_path,
                    ])

                    pid = proc.pid

                    clear()
                    prompt = "Please choose: \n"
                    for i, option in enumerate(classifier_options):
                        prior_choice = mappings.get(option, False)

                        if prior_choice:
                            prompt += "%d: %s (replace)\n" % (i, option,)
                        else:
                            prompt += "%d: %s\n" % (i, option,)

                    option_index = int(input(prompt).strip())
                    choice = classifier_options[option_index]

                    mappings[choice] = (
                        absolute_image_path,
                        option_index,
                        os.path.basename(absolute_image_path),
                    )

                    print("attempting to kill...")
                    os.kill(proc.pid, signal.SIGKILL)

        if mappings:
            if not os.path.isdir(raw_subpath):
                print("creating raw subdirectory")
                os.mkdir(raw_subpath)
            else:
                print("raw subdirectory exists already, no need to create")

            photos, videos = partition(mappings)

            for position, (p, i, base) in photos.items():
                _, ext = os.path.splitext(base)
                pretty = "%s-%s_%d%s" % (rug_path, position, i, ext,)
                working_copy_target = os.path.join(path, pretty)

                os.rename(
                    src=p,
                    dst=working_copy_target,
                )

            video_counter = len(photos) - 1
            for position, (p, _, base) in videos.items():

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
