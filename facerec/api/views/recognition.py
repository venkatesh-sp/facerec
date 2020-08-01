import base64
import face_recognition as fr
import os
import numpy as np


from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from django.conf import settings

from .detection import detect_mask


def mask_func(input_image):
    label = detect_mask(input_image)
    if label == "Mask":
        return {"status": "Masked"}
    elif label == "No Mask":
        return {"status": "UnMasked"}
    else:
        return {"status": "No Face"}


def compare_faces(file1):
    image1 = fr.load_image_file(file1)
    face_location = fr.face_locations(image1)
    # convert the face image to encoding
    face_encoding = fr.face_encodings(image1, face_location)[0]

    for known_embedding in settings.EMBEDDINGS:
        known_embed = np.load(known_embedding)
        results = fr.compare_faces([known_embed], face_encoding, tolerance=0.5)
        if results[0]:
            return {
                "status": True,
                "msg": os.path.basename(known_embedding).rstrip(".npy"),
            }
    return {"status": False, "msg": "UnKnown User"}


class EmployeeAttendance(APIView):
    def post(self, request):
        image_uri = base64.b64decode(request.data.get("image").get("base64"))
        attendance_image = open("attendance.png", "wb")

        attendance_image.write(image_uri)
        attendance_image.close()
        status_mask = mask_func("attendance.png")

        if status_mask["status"] == "Masked":
            os.remove(attendance_image.name)
            return Response(
                {"mask_status": status_mask["status"], "status": False},
                status=status.HTTP_200_OK,
            )
        elif status_mask["status"] == False:
            os.remove(attendance_image.name)
            return Response(
                {"mask_status": status_mask["status"], "status": False},
                status=status.HTTP_200_OK,
            )

        try:
            check_status = compare_faces("attendance.png")
        except IndexError:
            return Response(
                {
                    "mask_status": status_mask["status"],
                    "user": "UnKnown User",
                    "status": False,
                },
                status=status.HTTP_200_OK,
            )
        print(check_status, "face match")
        os.remove(attendance_image.name)
        return Response(
            {
                "mask_status": status_mask["status"],
                "user": check_status["msg"],
                "status": check_status["status"],
            },
            status=status.HTTP_201_CREATED,
        )


class LoadFaceEmbeddings(APIView):
    def get(self, request):
        for filename in settings.FACES:
            name = os.path.splitext(os.path.basename(filename))[0]

            # Load image of each employee using face_recognition
            loaded_face = fr.load_image_file(filename)

            # Extract face location and convert it into an embedding
            known_embedding = fr.face_encodings(loaded_face, model="small")[0]

            # Saving each face_embedding array as a .npy array with the employee name as filename. Ex: venkatesh.npy
            save_path = f"{settings.STATICFILES_DIRS[0]}/embeddings/{name}"
            np.save(save_path, known_embedding)
        return Response(True, status=status.HTTP_201_CREATED)
