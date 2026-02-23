from django.urls import path
from . import views

urlpatterns = [
    path("", views.tenancy_list, name="tenancy_list"),
    path("create/", views.tenancy_create, name="tenancy_create"),

]
