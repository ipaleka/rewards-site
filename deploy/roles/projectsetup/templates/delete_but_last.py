# !/usr/bin/python3

import os
from pathlib import Path


def delete_from_parent(parent):
    for root, _, files in os.walk(parent, topdown=False):
        if len(files):
            newest = newest_filename(root)
            if newest:
                for name in files:
                    if newest.name != name:
                        os.remove(os.path.join(root, name))


def newest_filename(root):
    return next(
        iter(sorted(Path(root).iterdir(), key=os.path.getmtime, reverse=True)), ""
    )


if __name__ == "__main__":
    for root in ("escrow", "dex"):
        DATA_PATH = "{{ site_path }}/data/"
        delete_from_parent(f"{DATA_PATH}/{root}")
