from django.urls import path
from . import views

urlpatterns = [
    path('concurso/<url_contest>/', views.contest_home, name="contest_home"),
    path('concurso/<url_contest>/<msn>', views.contest_home, name="contest_home_msn"),
    path('concurso/<url_contest>/register_video/', views.upload_video_action, name="register_video"),
    #path('concurso/<url_contest>/upload_video/', views.upload_video_view, name="upload_video"),
    #path('concurso/upload_video/', views.upload_video_action, name="upload_video"),
]
