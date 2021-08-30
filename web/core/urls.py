from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name="home"),
    
    path('create/', views.create_new_contest_view, name="create_contest"),
    path('create_contest/', views.create_new_contest_action, name="register_contest"),

    path('update/', views.update_contest_view, name="update_contest"),
    path('update_contest/', views.update_contest_action, name="save_contest"),

    path('delete/', views.delete_contest, name="delete_contest"),

    path('test_post/', views.test_post, name="test_post"),
]


