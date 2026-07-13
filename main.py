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

    #First upscale the image to increase the DPI
    upscaled = image

    #Then convert the image to black and white only using a threshold filter
    gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
    val, bw = cv2.threshold(gray,float(150),255, cv2.THRESH_BINARY)


    #Data processing
    data = pt.image_to_data(processed_image, output_type= Output.DICT)
    box_num = len(data["text"]) #Gets the number of words detected


    for i in range(box_num):
        if data["conf"][i] == -1:
            continue
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


for threshold in np.arange(120,180,10,dtype=float):
    #for scalef in np.arange(2.5,3.6,0.10,dtype=float):
        scalef=3.0
        scaled = cv2.resize(img,None,None,scalef,scalef,cv2.INTER_CUBIC)
        gray = cv2.cvtColor(scaled,cv2.COLOR_BGR2GRAY)
        erode_kernel = np.ones([5,5],np.uint8)
        erode = cv2.erode(gray, erode_kernel, iterations=1)
        ret, thresh = cv2.threshold(erode,threshold,255,cv2.THRESH_BINARY)
        cv2.imwrite(f"outputs/with_erosion_51/{threshold}_thresh_{scalef:.2f}_scale_image.jpg",thresh)

        text = pt.image_to_string(thresh)
        with open(f"outputs/with_erosion_51/{threshold}_thresh_{scalef:.2f}_scale_text.txt","w+") as text_output:
            text_output.write(text)
        print(text)

