import weather_data
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model

data = weather_data.Weather_Data()
test_x = data
scaler_x = MinMaxScaler()
test_x_values = test_x.values
test_x_scaled = scaler_x.fit_transform(test_x_values)
test_x_reshaped = test_x_scaled.reshape((test_x_scaled.shape[0], 1, test_x_scaled.shape[1]))

loaded_model = load_model("pred_model.h5")
predictions = loaded_model.predict(test_x_reshaped)


print(data)

