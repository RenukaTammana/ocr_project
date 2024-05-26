from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_image, name='upload_image'),
    path('upload/vscard.html', views.visitor_card_template, name='visitor_card_template'),
    # path('capture/', views.capture_image, name='capture_image'),
]
