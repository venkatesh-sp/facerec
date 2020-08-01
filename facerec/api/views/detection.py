from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
import numpy as np
import argparse
import cv2
import os

from django.conf import settings

face_model = settings.MODEL_FILES.get("caffemodel")
face_prototxt = settings.MODEL_FILES.get("prototxt")
mask_model = settings.MODEL_FILES.get("model")
confidence_thershold = 0.5


def detect_mask(input_image):
    # load our serialized face detector model from disk
    print("[INFO] loading face detector model...")
    face_detect = cv2.dnn.readNet(face_prototxt, face_model)

    # load the face mask detector model from disk
    print("[INFO] loading face mask detector model...")
    mask_detect = load_model(mask_model)

    # load the input image from disk, clone it, and grab the image spatial
    # dimensions
    image = cv2.imread(input_image)
    orig = image.copy()
    (h, w) = image.shape[:2]

    # construct a blob from the image
    blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), (104.0, 177.0, 123.0))

    # pass the blob through the network and obtain the face detections
    print("[INFO] computing face detections...")
    face_detect.setInput(blob)
    detections = face_detect.forward()
    label = False

    # loop over the detections
    for i in range(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with
        # the detection
        confidence = detections[0, 0, i, 2]

        # filter out weak detections by ensuring the confidence is
        # greater than the minimum confidence
        if confidence > confidence_thershold:
            # compute the (x, y)-coordinates of the bounding box for
            # the object
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # ensure the bounding boxes fall within the dimensions of
            # the frame
            (startX, startY) = (max(0, startX), max(0, startY))
            (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

            # extract the face ROI, convert it from BGR to RGB channel
            # ordering, resize it to 224x224, and preprocess it
            face = image[startY:endY, startX:endX]
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            face = img_to_array(face)
            face = preprocess_input(face)
            face = np.expand_dims(face, axis=0)

            # pass the face through the model to determine if the face
            # has a mask or not
            (mask, withoutMask) = mask_detect.predict(face)[0]

            # determine the class label and color we'll use to draw
            # the bounding box and text
            label = "Mask" if mask > withoutMask else "No Mask"

            color = (0, 255, 0) if label == "Mask" else (0, 0, 255)

            # include the probability in the label
            # label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)
    return label


# label = detect_mask()
# print(label)
