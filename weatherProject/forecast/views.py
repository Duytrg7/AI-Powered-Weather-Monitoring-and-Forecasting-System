from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import requests
import pandas as pd
import numpy as np
import json
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error
from datetime import datetime, timedelta
import pytz

API_KEY = '7b0e0d67fb067d164ddd0bc20c1930bd'
BASE_URL = 'https://api.openweathermap.org/data/2.5/'

# [THAY ĐỔI] Đường dẫn thư mục lưu model .pkl
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

RAIN_MODEL_PATH = os.path.join(MODEL_DIR, 'rain_model.pkl')
TEMP_MODEL_PATH = os.path.join(MODEL_DIR, 'temp_model.pkl')
HUM_MODEL_PATH = os.path.join(MODEL_DIR, 'hum_model.pkl')
LE_PATH = os.path.join(MODEL_DIR, 'label_encoder.pkl')


@csrf_exempt
def receive_sensor_data(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            temperature = body.get('temperature')
            humidity = body.get('humidity')

            if temperature is None or humidity is None:
                return JsonResponse({'status': 'error', 'message': 'Thiếu temperature hoặc humidity'}, status=400)

            cache.set('dht11_temperature', float(temperature), timeout=600)
            cache.set('dht11_humidity', float(humidity), timeout=600)

            print(
                f"[ESP32] Nhận được: Nhiệt độ={temperature}°C, Độ ẩm={humidity}%")
            return JsonResponse({'status': 'ok', 'message': 'Nhận dữ liệu thành công'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'JSON không hợp lệ'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Chỉ chấp nhận POST'}, status=405)


# [THAY ĐỔI] Endpoint mới — xóa .pkl để trigger train lại lần sau
@csrf_exempt
def retrain_models(request):
    if request.method == 'POST':
        deleted = []
        for path, name in [
            (RAIN_MODEL_PATH, 'rain_model'),
            (TEMP_MODEL_PATH, 'temp_model'),
            (HUM_MODEL_PATH,  'hum_model'),
            (LE_PATH,         'label_encoder'),
        ]:
            if os.path.exists(path):
                os.remove(path)
                deleted.append(name)
        return JsonResponse({
            'status': 'ok',
            'message': 'Models sẽ được train lại lần tới',
            'deleted': deleted
        })
    return JsonResponse({'status': 'error', 'message': 'Chỉ chấp nhận POST'}, status=405)


# 1. Fetch current weather
def get_current_weather(lat, lon):
    url = f"{BASE_URL}weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    return {
        'city':           data['name'],
        'current_temp':   round(data['main']['temp']),
        'feels_like':     round(data['main']['feels_like']),
        'temp_min':       round(data['main']['temp_min']),
        'temp_max':       round(data['main']['temp_max']),
        'humidity':       round(data['main']['humidity']),
        'description':    data['weather'][0]['description'],
        'country':        data['sys']['country'],
        'wind_gust_dir':  data['wind']['deg'],
        'pressure':       data['main']['pressure'],
        'Wind_Gust_Speed': data['wind']['speed'],
        'clouds':         data['clouds']['all'],
        'visibility':     data['visibility'],
    }


# 2. Read Historical Data
def read_historical_data(filename):
    df = pd.read_csv(filename)
    df = df.dropna()
    df = df.drop_duplicates()
    return df


# 3. Prepare data for training
def prepare_data(data):
    le = LabelEncoder()
    data['WindGustDir'] = le.fit_transform(data['WindGustDir'])
    data['RainTomorrow'] = le.fit_transform(data['RainTomorrow'])

    x = data[['MinTemp', 'MaxTemp', 'WindGustDir', 'WindGustSpeed',
              'Humidity', 'Pressure', 'Temp', 'Hour']]
    y = data['RainTomorrow']

    return x, y, le


# 4. Train Rain Prediction Model
def train_rain_model(x, y):
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    print("Mean Squared Error for Rain Model:",
          mean_squared_error(y_test, y_pred))

    return model


# 5. Prepare regression data
def prepare_regression_data(data, feature):
    x, y = [], []
    for i in range(len(data) - 1):
        x.append([data[feature].iloc[i], data['Hour'].iloc[i]])
        y.append(data[feature].iloc[i + 1])

    return np.array(x), np.array(y)


# 6. Train Regression Model
def train_regression_model(x, y):
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(x, y)
    return model


# 7. Predict Future
def predict_future(model, current_value, current_hour):
    predictions = []
    value = current_value
    hour = current_hour

    for _ in range(5):
        next_value = model.predict(np.array([[value, hour]]))[0]
        predictions.append(next_value)
        value = next_value
        hour = (hour + 1) % 24

    return predictions


# [THAY ĐỔI] Hàm mới: load .pkl nếu có, ngược lại train mới rồi lưu lại
def get_or_train_models(historical_data):
    models_exist = all(os.path.exists(p) for p in [
        RAIN_MODEL_PATH, TEMP_MODEL_PATH, HUM_MODEL_PATH, LE_PATH
    ])

    if models_exist:
        print("[MODEL] Load model từ file .pkl — bỏ qua train")
        rain_model = joblib.load(RAIN_MODEL_PATH)
        temp_model = joblib.load(TEMP_MODEL_PATH)
        hum_model = joblib.load(HUM_MODEL_PATH)
        le = joblib.load(LE_PATH)
    else:
        print("[MODEL] Không tìm thấy .pkl → train mới và lưu lại")
        x, y, le = prepare_data(historical_data)
        rain_model = train_rain_model(x, y)

        x_temp, y_temp = prepare_regression_data(historical_data, 'Temp')
        x_hum,  y_hum = prepare_regression_data(historical_data, 'Humidity')
        temp_model = train_regression_model(x_temp, y_temp)
        hum_model = train_regression_model(x_hum,  y_hum)

        joblib.dump(rain_model, RAIN_MODEL_PATH)
        joblib.dump(temp_model, TEMP_MODEL_PATH)
        joblib.dump(hum_model,  HUM_MODEL_PATH)
        joblib.dump(le,         LE_PATH)
        print("[MODEL] Đã lưu model vào thư mục models/")

    return rain_model, temp_model, hum_model, le


def weather_view(request):
    if request.method == 'POST':
        lat = request.POST.get('lat')
        lon = request.POST.get('lon')
        if not lat or not lon:
            return render(request, 'weather.html', {
                'error': 'Không lấy được vị trí. Vui lòng cho phép truy cập vị trí.'
            })

        current_weather = get_current_weather(lat, lon)

        dht11_temp = cache.get('dht11_temperature')
        dht11_hum = cache.get('dht11_humidity')
        using_sensor = dht11_temp is not None and dht11_hum is not None

        if using_sensor:
            actual_temp = round(dht11_temp)
            actual_humidity = round(dht11_hum)
            print(
                f"[VIEW] Dùng DHT11: Nhiệt độ={actual_temp}°C, Độ ẩm={actual_humidity}%")
        else:
            actual_temp = current_weather['current_temp']
            actual_humidity = current_weather['humidity']
            print("[VIEW] Không có DHT11, dùng OpenWeather")

        csv_path = os.path.join(BASE_DIR, 'weather.csv')
        historical_data = read_historical_data(csv_path)

        # [THAY ĐỔI] Thay train trực tiếp → load hoặc train tùy trạng thái .pkl
        rain_model, temp_model, hum_model, le = get_or_train_models(
            historical_data)

        wind_deg = current_weather['wind_gust_dir'] % 360
        compass_points = [
            ("N", 0, 11.25),      ("NNE", 11.25, 33.75),  ("NE", 33.75, 56.25),
            ("ENE", 56.25, 78.75), ("E", 78.75, 101.25),   ("ESE", 101.25, 123.75),
            ("SE", 123.75, 146.25), ("SSE", 146.25, 168.75), ("S", 168.75, 191.25),
            ("SSW", 191.25, 213.75), ("SW", 213.75,
                                      236.25), ("WSW", 236.25, 258.75),
            ("W", 258.75, 281.25), ("WNW", 281.25, 303.75), ("NW", 303.75, 326.25),
            ("NNW", 326.25, 348.75),
        ]
        compass_direction = next(
            point for point, start, end in compass_points if start <= wind_deg < end)
        compass_direction_encoded = (
            le.transform([compass_direction])[0]
            if compass_direction in le.classes_ else -1
        )

        timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        now = datetime.now(timezone)
        current_hour = now.hour

        current_data = {
            'MinTemp':       current_weather['temp_min'],
            'MaxTemp':       current_weather['temp_max'],
            'WindGustDir':   compass_direction_encoded,
            'WindGustSpeed': current_weather['Wind_Gust_Speed'],
            'Humidity':      current_weather['humidity'],
            'Pressure':      current_weather['pressure'],
            'Temp':          current_weather['current_temp'],
            'Hour':          current_hour,
        }

        current_df = pd.DataFrame([current_data])
        rain_prediction = rain_model.predict(current_df)[0]

        future_temp = predict_future(temp_model, actual_temp,     current_hour)
        future_hum = predict_future(hum_model,  actual_humidity, current_hour)

        next_hour = (now + timedelta(hours=1)).replace(minute=0,
                                                       second=0, microsecond=0)
        future_times = [(next_hour + timedelta(hours=i)
                         ).strftime("%H:00") for i in range(5)]

        time1, time2, time3, time4, time5 = future_times
        temp1, temp2, temp3, temp4, temp5 = future_temp
        hum1,  hum2,  hum3,  hum4,  hum5 = future_hum

        context = {
            'using_sensor':    using_sensor,
            'current_temp':    actual_temp,
            'MinTemp':         current_weather['temp_min'],
            'MaxTemp':         current_weather['temp_max'],
            'feels_like':      current_weather['feels_like'],
            'humidity':        actual_humidity,
            'clouds':          current_weather['clouds'],
            'description':     current_weather['description'],
            'city':            current_weather['city'],
            'country':         current_weather['country'],

            'rain_prediction': 'Rain' if rain_prediction == 1 else 'No Rain',

            'time':       datetime.now(),
            'date':       datetime.now().strftime("%B %d, %Y"),
            'wind':       current_weather['Wind_Gust_Speed'],
            'pressure':   current_weather['pressure'],
            'visibility': current_weather['visibility'],

            'time1': time1, 'time2': time2, 'time3': time3,
            'time4': time4, 'time5': time5,

            'temp1': f"{round(temp1, 1)}", 'temp2': f"{round(temp2, 1)}",
            'temp3': f"{round(temp3, 1)}", 'temp4': f"{round(temp4, 1)}",
            'temp5': f"{round(temp5, 1)}",

            'hum1': f"{round(hum1, 1)}", 'hum2': f"{round(hum2, 1)}",
            'hum3': f"{round(hum3, 1)}", 'hum4': f"{round(hum4, 1)}",
            'hum5': f"{round(hum5, 1)}",
        }
        return render(request, 'weather.html', context)
    return render(request, 'weather.html')
