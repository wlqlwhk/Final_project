# views.py
import base64
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.template import context
from keras.models import load_model
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import requests
import json
import datetime
import io
from django.views.decorators.csrf import csrf_exempt




#   데이터 전처리 완료
#   POP(강수확률), PTY(강수형태), PCP(강수량), REH(습도), SNO(적설량), SKY(하늘), TMP(기온), VEC(풍향), WSD(풍속)
#   현재 날짜로부터 다음날 23시까지 날씨 데이터 가져옴
#   json형식
#   사용자로부터 nx, ny를 입력받는건데,, 음 지역 이름이랑 nx, ny가 대응되도록 해야됨
def fetch_weather_data(nx,ny):
    url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'

    current_date = datetime.datetime.now()
    current_date_str = datetime.datetime.now().strftime('%Y%m%d')
    next2_date = current_date + datetime.timedelta(days=2)
    next3_date = current_date + datetime.timedelta(days=3)
    next2_date_str = next2_date.strftime('%Y%m%d')
    next3_date_str = next3_date.strftime('%Y%m%d')


    params = {'serviceKey': 'S22VmKa5ZPKoMXlsIClyPXtl0CThRnTvuWz6M5D1GJ/x1J1RWFc3kcFMDhtUCV0kvGGDL9BHPZcnrndGHj4l5w==',
              'pageNo': '1',
              'numOfRows': '1000',
              'dataType': 'json',
              'base_date': current_date_str,
              'base_time': '0500',
              'nx': nx,
              'ny': ny,
              }

    response = requests.get(url, params=params)
    original_data = json.loads(response.content)

    filtered_data = []  # 필요한 데이터만 추출
    exclude_categories = {'TMN', 'TMX', 'UUU', 'VVV', 'WAV', 'POP', 'PTY' }  # 제외할 데이터 목록
    exclude_date = {next2_date_str, next3_date_str, }
    # 응답 데이터의 'response' -> 'body' -> 'items' -> 'item' 에서 각각의 아이템을 가져옴
    items = original_data['response']['body']['items']['item']

    for item in items:
        if item.get('category') not in exclude_categories:
            if item.get('fcstDate') not in exclude_date:
                fcst_value = item.get('fcstValue')
                filtered_data.append(item)

    filtered_data = pd.DataFrame(filtered_data)
    delete_columns = ['baseDate', 'baseTime', 'nx', 'ny']
    data_df = filtered_data.drop(delete_columns, axis =1)

    df_pivoted = data_df.pivot_table(index=["fcstDate", "fcstTime"],
                            columns='category',
                            values='fcstValue',
                            aggfunc='first').reset_index()
    df_pivoted.columns.name = None
    df_pivoted.reset_index(inplace=True, drop=True)
    df_pivoted['PCP'] = df_pivoted['PCP'].apply(lambda x: 0 if x == '강수없음' else float(x[:-2]) if x.endswith('mm') else x)
    df_pivoted['SNO'] = df_pivoted['SNO'].apply(lambda x: 0 if x == '적설없음' else x)

    delete_date = ['fcstDate', 'fcstTime']
    provided_data = df_pivoted.drop(delete_date, axis =1)
    #train_x랑 열 이름,순서 동일하게
    new_order = ['SKY', 'TMP', 'REH', 'WSD', 'VEC', 'PCP', 'SNO']
    new_names = {'SKY': 'cloud', 'TMP': 'temp', 'REH': 'humidity', 'WSD': 'wind_speed', 'VEC': 'wind_dir', 'PCP': 'rain', 'SNO': 'snow'}
    #구름 양 수치화
    value_mapping = {1: 0, 3: 50, 4: 100}

    weather_data = provided_data[new_order]
    weather_data = weather_data.rename(columns=new_names)
    weather_data = weather_data.apply(pd.to_numeric, errors='coerce')
    weather_data.wind_speed =weather_data.wind_speed.multiply(1000)
    weather_data.snow =weather_data.snow.multiply(0.01)
    weather_data['cloud'] = weather_data['cloud'].replace(value_mapping)
    return weather_data

def get_sun_predictions(request):
    dong_name = request.GET.get('search-input', '')
    # 격자 좌표를 얻습니다.
    grid_x, grid_y = find_grid_coordinates(dong_name)
    if grid_x is None or grid_y is None:
        return HttpResponse("입력한 동의 좌표를 찾을 수 없습니다.")

    test_x = fetch_weather_data(grid_x,grid_y)
    scaler_x = MinMaxScaler()
    test_x_values = test_x.values
    test_x_scaled = scaler_x.fit_transform(test_x_values)
    test_x_reshaped = test_x_scaled.reshape((test_x_scaled.shape[0], 1, test_x_scaled.shape[1]))

    loaded_model = load_model("pred_model.h5")
    predictions = loaded_model.predict(test_x_reshaped)

    a = predictions

    #스타일
    plt.style.use('dark_background')  # 스타일링 테마 적용
    plt.figure(figsize=(14, 6))
    plt.plot(a, color='limegreen', label='Amount',marker='o', linestyle='--')  # 색상과 레이블 변경
    plt.title('Sun Prediction Amount Over Time')  # 타이틀 추가
    plt.ylabel('pred amount')  # y축 레이블 추가
    plt.grid(True)  # 그리드 추가
    # plt.tight_layout()  # 레이아웃 조정


    # 버퍼 생성 및 그래프 저장
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()

    # Base64로 인코딩
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    # 이미지 데이터를 컨텍스트에 추가
    context = {'image_base64': image_base64}

    # HTML 템플릿에 컨텍스트 전달
    return render(request, 'weather/sunpredict.html', context)
    # 버퍼의 내용을 HTTP 응답으로 반환
    #return HttpResponse(buf.getvalue(), content_type='image/png')

    #return render(request, 'weather/sunpredict.html')

def index(request):
    # 여기에 날씨 데이터 넣으면 날씨 정보도 볼 수 있음
    return render(request, 'weather/pred.html')

def find_grid_coordinates(dong_name):
    """
    동 이름을 입력받아 해당 동의 격자 X, Y 좌표를 반환하는 함수

    :param dong_name: 동 이름 (str)
    :param file_path: 격자 정보가 포함된 엑셀 파일의 경로 (str)
    :return: (격자 X, 격자 Y) 좌표의 튜플, 해당 동이 없는 경우 None 반환
    """
    file_path = 'C:\\Users\\jhkim\\Documents\\pragmatic_drf\\기상청41_단기예보 조회서비스_오픈API활용가이드_격자_위경도(20231130).xlsx'
    try:
        grid_df = pd.read_excel(file_path)
    except Exception as e:
        print(f"파일 로드 중 오류 발생: {e}")
        return None

    filtered_data = grid_df[grid_df['3단계'] == dong_name]

    if not filtered_data.empty:
        grid_x = filtered_data.iloc[0]['격자 X']
        grid_y = filtered_data.iloc[0]['격자 Y']
        return grid_x, grid_y

    return None
def list(request):
    file_path = 'C:\\Users\\jhkim\\Documents\\pragmatic_drf\\기상청41_단기예보 조회서비스_오픈API활용가이드_격자_위경도(20231130).xlsx'
    df = pd.read_excel(file_path)
    df = df[['1단계', '2단계', '3단계']]  # 필요한 열 선택
    html_table = df.to_html(classes='dataframe table', border=1, index=False)
    html_table = html_table.replace('<table ', '<table id="data-table" ')
    # HTML 테이블을 컨텍스트에 추가
    context = {'html_table': html_table}
    return render(request, 'weather/list.html', context)
def introduce(request):

    return render(request,'weather/introduce.html')


def predict_result(request):
    dong_name = request.GET.get('dong', '')

    # 여기서 dong_name을 사용하여 예측 결과를 처리하고
    # 그 결과를 사용자에게 보여주는 로직을 구현합니다.

    return render(request, 'weather/predict_result.html', context)
