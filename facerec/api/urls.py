from django.urls import path
from .views import EmployeeAttendance, LoadFaceEmbeddings

# Create your urls here.

urlpatterns = [
    path("check/", EmployeeAttendance.as_view(), name="EmployeeAttendance"),
    path("load-embeddings/", LoadFaceEmbeddings.as_view(), name="LoadFaceEmbeddings"),
]
