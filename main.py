from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
import pytesseract as pt
from pytesseract import Output

if TYPE_CHECKING:
    from cv2.typing import MatLike


#Image loading Functions

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


#Bounding Box functions

def draw_bounding_boxes(image : MatLike, processed_image: MatLike, output_name : str):

    #Image Pre_Processing



    #Data processing
    data = pt.image_to_data(processed_image, output_type= Output.DICT)
    box_num = len(data["text"]) #Gets the number of words detected

    for i in range(box_num):
        if data["conf"][i] == -1:
            continue
            #BGR Tuple with vals up to 255 inclusive
            colour = (0,0,255)
        else:
            colour = (255, 0, 0)


        #Coords
        #Left is the distance from the left of the bounding box to the left of the image, top follows
        x, y = data["left"][i], data["top"][i]

        w, h = data["width"][i], data["height"][i]

        #Corners
        top_left = (x, y)
        bottom_right = (x+w, y+h)

        #BGR Tuple with vals up to 255 inclusive

        border_width = 1 #Number of pixels

        #Draw box
        cv2.rectangle(image,top_left, bottom_right, colour, border_width)

    cv2.imwrite(output_name, image)

    if Path(output_name).exists():
        print("Bounding Boxes successfully added")
    else:
        print("Error")



def draw_many_boxes(images : list[tuple[MatLike,str]], output_dir : str):
    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir()

    for image in images:
        name, extension = image[1].split(".")
        output_file = output_dir + "/" + name + "_with_boxes." + extension
        print(output_file)
        #draw_bounding_boxes(image[0], output_file)


#img_folder = "test_data/test_profiles/one_per_page"

#images = imgs_from_str_folder(img_folder, ".jpg")

#draw_many_boxes(images, "test_data/test_profiles/one_per_page/output")

img_path = "test_data/test_profiles/one_per_page/bandobras_took.jpg"

img = img_from_str_path(img_path)

#Version 0


#Version 1
def sharpen(image):
   kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
   return cv2.filter2D(image, -1, kernel)

#Version 2
def sharpen2(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 9, 75,75)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return sharpened

#Version 3
def sharpen3(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 9, 75,75)
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return sharpened

#Version 4
def sharpen4(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 7, 75,75)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return sharpened

#Version 5
def sharpen5(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 5, 75,75)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return sharpened

#Version 6
def sharpen6(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 5, 75,75)
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return sharpened


#Version 7
def sharpen7(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 3, 75,75)
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return sharpened

#Version 8
def sharpen8(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 3, 75,75)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    return sharpened


draw_bounding_boxes(img,sharpen8(img), "boxed_image_8.jpg")
