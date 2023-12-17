from django.urls import path
from .views import get_sun_predictions, index

# app_name = 'weather'

urlpatterns = [
    path('',index, name='index'),  # pred.html을 기본 페이지로 설정
    path('get_sun_predictions/', get_sun_predictions, name='get_sun_predictions'), # 예측값 가져오는 경로
]
