from django.urls import path
from .views import get_sun_predictions, index, list, introduce, predict_result

# app_name = 'weather'

urlpatterns = [
    path('',index, name='index'),  # pred.html을 기본 페이지로 설정
    path('get_sun_predictions/', get_sun_predictions, name='get_sun_predictions'), # 예측값 가져오는 경로
    path('list/',list,name='list'),
    path('introduce/',introduce,name='introduce'),
    path('predict-result/', predict_result, name='predict_result'),

]
