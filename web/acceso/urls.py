from django.urls import path
from . import views

urlpatterns = [
    path('', views.info_view, name="info"),
    path('login/', views.login_view, name="login"),
    path('singin/', views.singin_view, name="singin"),
    path('register/', views.register, name="register"),
    path('login_action',views.login_action, name="login_action"),
    path('logout/',views.logout_action, name="logout_action" )
]