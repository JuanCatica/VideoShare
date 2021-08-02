import cv2
import os

def get_image_from_video(video_file):
    vidcap = cv2.VideoCapture(video_file)
    success,image = vidcap.read()
    if success:
        return image
    else:
        return None

def trim_reshape_save_image(image, outdir, name, rate=1.5, width=220):
    output_shape=(width,int(width/rate))
    y, x, z = image.shape
    dx = dy = 0
    if float(x/y) >= rate:
        dx = int((x-(y*rate))/2.0)
    else:
        dy = int((y-(x/rate))/2.0)
    sliced_image = image[dy:y-dy, dx:x-dx, :]
    rechaped = cv2.resize(sliced_image, output_shape, interpolation = cv2.INTER_AREA)
    path = os.path.join(outdir,"img_{}.jpg".format(name))
    cv2.imwrite(os.path.join(path), rechaped)
    return path