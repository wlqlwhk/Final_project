import pandas as pd
import requests
import json
import datetime

#   데이터 전처리 완료
#   POP(강수확률), PTY(강수형태), PCP(강수량), REH(습도), SNO(적설량), SKY(하늘), TMP(기온), VEC(풍향), WSD(풍속)
#   현재 날짜로부터 다음날 23시까지 날씨 데이터 가져옴
#   json형식
#   사용자로부터 nx, ny를 입력받는건데,, 음 지역 이름이랑 nx, ny가 대응되도록 해야됨
def Weather_Data():
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
              'nx': '55',
              'ny': '127',
              }

    response = requests.get(url, params=params)
    original_data = json.loads(response.content)

    filtered_data = []  # 필요한 데이터만 추출
    exclude_categories = {'TMN', 'TMX', 'UUU', 'VVV', 'WAV', 'POP', 'PTY' }  # 제외할 데이터 목록
    exclude_date = {next2_date_str, next3_date_str, }
    # 응답 데이터의 'response' -> 'body' -> 'items' -> 'item' 에서 각각의 아이템을 가져옴
    items = original_data['response']['body']['items']['item']

    # 데이터 전처리
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
    #예측할 때 시간은 필요없음
    delete_date = ['fcstDate', 'fcstTime']
    provided_data = df_pivoted.drop(delete_date, axis =1)
    new_order = ['SKY', 'TMP', 'REH', 'WSD', 'VEC', 'PCP', 'SNO']
    new_names = {'SKY': 'cloud', 'TMP': 'temp', 'REH': 'humidity', 'WSD': 'wind_speed', 'VEC': 'wind_dir', 'PCP': 'rain', 'SNO': 'snow'}
    value_mapping = {1: 0, 3: 50, 4: 100}
    weather_data = provided_data[new_order]
    weather_data = weather_data.rename(columns=new_names)
    weather_data = weather_data.apply(pd.to_numeric, errors='coerce')
    weather_data.wind_speed =weather_data.wind_speed.multiply(1000)
    weather_data.snow =weather_data.snow.multiply(0.01)
    weather_data['cloud'] = weather_data['cloud'].replace(value_mapping)
    return weather_data
