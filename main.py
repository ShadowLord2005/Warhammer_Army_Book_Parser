from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import pytesseract as pt
from pytesseract import Output

if TYPE_CHECKING:
    from cv2.typing import MatLike

def img_from_str_path(path : str) -> MatLike:
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError

    image = cv2.imread(path_obj)

    if type(image) == type(None):
        raise Exception("Image not opened correctly")
    else:
        assert image is not None
        return image

def imgs_from_str_folder(folder_path : str, img_type_extension : str) -> list[tuple[MatLike, str]]:
    images : list[tuple[MatLike, str]] = []

    if img_type_extension[0] != ".":
        img_type_extension = "." + img_type_extension

    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError

    for file in folder.iterdir():
        if file.suffix == img_type_extension:
            image = cv2.imread(file)
            if type(image) == type(None):
                raise Exception("Image not opened correctly")
            else:
                assert image is not None

                images.append((image, file.name))

    print(f"Found {len(images)} images of type {img_type_extension} in folder {folder_path}")

    return images

def draw_bounding_boxes(image : MatLike, output_name : str):

    #Data processing
    data = pt.image_to_data(image, output_type= Output.DICT)
    box_num = len(data["text"]) #Gets the number of words detected

    for i in range(box_num):
        if data["conf"][i] == -1:
            continue
            #Skips any word where the confidence is -1 meaning a box is drawn around a block of text rather than a word

        #Coords
        #Left is the distance from the left of the bounding box to the left of the image, top follows
        x, y = data["left"][i], data["top"][i]

        w, h = data["width"][i], data["height"][i]

        #Corners
        top_left = (x, y)
        bottom_right = (x+w, y+h)

        #RGB Tuple with vals up to 255 inclusive
        colour = (255, 0, 0)
        border_width = 3 #Number of pixels

        #Draw box
        cv2.rectangle(image,top_left, bottom_right, colour, border_width)

    cv2.imwrite(output_name, image)

    print(Path(output_name).exists())


def draw_many_boxes(images : list[tuple[MatLike,str]], output_dir : str):
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir()

    for image in images:
        name, extension = image[1].split(".")
        output_file = output_dir + "/" + name + "_with_boxes." + extension
        print(output_file)
        draw_bounding_boxes(image[0], output_file)


img_folder = "test_images"

images = imgs_from_str_folder(img_folder, ".png")

draw_many_boxes(images, "test_images/output")

