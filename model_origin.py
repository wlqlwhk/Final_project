import pandas as pd
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, LSTM
from sklearn.preprocessing import MinMaxScaler

# 데이터 읽기
train_x = pd.read_csv('weather_actual.csv', parse_dates=True)
train_x = train_x[train_x.columns[1:]]
train_y = pd.read_csv('gens.csv', parse_dates=True)
train_y = train_y[train_y.columns[1:]]
train_y = pd.DataFrame(train_y)

# MinMax 스케일링
scaler_x = MinMaxScaler()
train_x_values = train_x.values
train_x_scaled = scaler_x.fit_transform(train_x_values)
train_x_reshaped = train_x_scaled.reshape((train_x_scaled.shape[0], 1, train_x_scaled.shape[1]))

# train_y를 한 타임스텝 앞으로 이동
train_y_shifted = train_y.shift(-1).fillna(0)
#train_y_shifted = train_y_shifted.astype(float)

# 모델 정의
model = Sequential()
model.add(LSTM(50, input_shape=(1, 7)))
model.add(Dense(1, activation='linear'))  # 활성화 함수를 linear로 변경

# 모델 컴파일
model.compile(loss='mean_squared_error', optimizer='adam', metrics=['mse'])

# 모델 학습
model.fit(train_x_reshaped, train_y_shifted, epochs=50, batch_size=64, shuffle=1)

# 모델과 가중치를 함께 저장
model.save("pred_model.h5")
