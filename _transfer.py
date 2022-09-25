import glob
from pathlib import Path
import os

from PIL import ImageFile, Image
import pillow_heif

pillow_heif.register_heif_opener()
ImageFile.LOAD_TRUNCATED_IMAGES = True

from tqdm import tqdm
import shutil
import json
import piexif
import pytz
import datetime

ALL_FILES = glob.glob("*/**/*", recursive=True)
JSON_FILES = [s for s in ALL_FILES if s.endswith(".json")]


def smart_glob(glob_pattern, extensions):
    found = []

    for filename in glob.glob(glob_pattern, recursive=True):
        base, ext = os.path.splitext(filename)
        if ext.lower() in extensions:
            found.append(filename)

    return found


class DataTransfer:
    def __init__(self, parent_dir: str, destination_dir: str) -> None:
        self.parent_dir = parent_dir

        os.makedirs(destination_dir, exist_ok=True)
        self.all_files = glob.glob(parent_dir + "/*")
        self.destination_dir = destination_dir

    def is_live(self, filepath: str) -> bool:
        photo_extensions = [".jpeg", ".jpg", ".heic"]
        if filepath.lower().endswith((".mp4", ".mov")):
            name, _ = os.path.splitext(filepath)

            for ph_ext in photo_extensions:
                if os.path.exists(name + ph_ext):
                    return True

        return False

    @staticmethod
    def is_image(path):
        return os.path.splitext(path)[1].upper() in [
            ".JPEG",
            ".JPG",
            ".HEIC",
            ".PNG",
            ".DNG",
        ]

    def __transfer(self, image_path: str) -> str:

        new_path = self.destination_dir + "/" + f"{Path(image_path).name}"
        is_live = self.is_live(image_path)

        if is_live and os.path.exists(new_path):
            os.remove(new_path)

        if not os.path.exists(new_path) and not is_live:
            shutil.copy2(image_path, new_path)


        return new_path

    @staticmethod
    def find_json(image_path):
        matches = [
            s for s in JSON_FILES if Path(s).name == Path(image_path + ".json").name
        ]
        if matches:
            with open(matches[0]) as f:
                return json.load(f)
        return None

    @staticmethod
    def fixmeta(path) -> bool:

        if not DataTransfer.is_image(path):
            return False

        img = Image.open(path)
        meta = DataTransfer.find_json(path)
        if not meta:
            return False
        exif_dict = img.info.get("Exif")
        if not exif_dict:
            exif_dict = {}
            exif_dict["Exif"] = {}
        else:
            exif_dict = piexif.load(exif_dict)

        exif_dict["Exif"][
            piexif.ExifIFD.DateTimeOriginal
        ] = datetime.datetime.fromtimestamp(
            int(meta["photoTakenTime"]["timestamp"]), tz=pytz.timezone("UTC")
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        exif_bytes = piexif.dump(exif_dict)
        img.save(path, exif=exif_bytes)

        return True

    def transfer(self):
        print(f"Transfering {self.parent_dir} --> {self.destination_dir}")
        paths = [
            p
            for p in glob.glob(f"{self.parent_dir}/**/*.*", recursive=True)
            if not (
                p.endswith(".json")
                or p.endswith(".py")
                or p.endswith(".AAE")
                or p.endswith(".ini")
            )
        ]
        for p in tqdm(paths):
            self.__transfer(p)
            DataTransfer.fixmeta(p)
            
