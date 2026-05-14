# 🌤️ Hệ thống Theo dõi và Dự báo Thời tiết

Hệ thống theo dõi thời tiết thời gian thực kết hợp AI dự báo, sử dụng Django, RandomForest và cảm biến DHT11/ESP32.

---

## ✨ Tính năng

- Hiển thị thời tiết hiện tại theo vị trí GPS
- Dự báo nhiệt độ và độ ẩm **24 giờ tiếp theo** bằng AI (RandomForest)
- Dự báo **mưa ngày mai** (Rain / No Rain)
- Hỗ trợ dữ liệu từ **cảm biến DHT11/ESP32** (ưu tiên) hoặc fallback **OpenWeather API**
- Giao diện fullscreen, scrollable timeline, tự động đổi ảnh nền theo thời tiết

---

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Backend | Python, Django |
| AI Model | scikit-learn (RandomForestClassifier, RandomForestRegressor) |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Dữ liệu thời tiết | OpenWeather API |
| Dữ liệu lịch sử | Visual Crossing (hourly, ~8640 dòng) |
| Phần cứng | ESP32 + DHT11 |

---

## ⚙️ Cài đặt và chạy

### Yêu cầu
- Python 3.10+
- pipenv (hoặc pip)

### Bước 1 — Clone repo
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>/weatherProject
```

### Bước 2 — Cài dependencies
```bash
# Dùng pipenv
pipenv install -r requirements.txt
pipenv shell

# Hoặc dùng pip thông thường
pip install -r requirements.txt
```

### Bước 3 — Tạo file `.env`
```bash
cp .env.example .env
```
Mở file `.env` và điền API key OpenWeather của bạn:
```
OPENWEATHER_API_KEY=your_api_key_here
```

### Bước 4 — Chạy server
```bash
python manage.py runserver
```

Truy cập tại: **http://127.0.0.1:8000**

---

## 🤖 AI Model

Hệ thống sử dụng 3 model RandomForest:

| Model | Loại | Mục đích |
|---|---|---|
| `rain_model.pkl` | Classifier | Dự báo mưa ngày mai |
| `temp_model.pkl` | Regressor | Dự báo nhiệt độ 24h |
| `hum_model.pkl` | Regressor | Dự báo độ ẩm 24h |

**Lần đầu chạy:** model sẽ tự train từ `weather.csv` (~15–20 giây) và lưu vào thư mục `models/`.  
**Các lần sau:** load trực tiếp từ file `.pkl` (~0.1 giây).  
**Khi cập nhật data mới:** gọi `POST /api/retrain/` để xóa `.pkl` cũ và trigger train lại.

---

## 📡 API Endpoints

| Endpoint | Method | Mô tả |
|---|---|---|
| `/` | GET/POST | Giao diện web chính |
| `/api/sensor/` | POST | Nhận dữ liệu từ ESP32/DHT11 |
| `/api/retrain/` | POST | Xóa model cũ, trigger retrain |

### Ví dụ gửi dữ liệu từ ESP32
```json
POST /api/sensor/
{
  "temperature": 31.5,
  "humidity": 70.2
}
```

---

## 📁 Cấu trúc project

```
weatherProject/
├── forecast/               # Django app chính
│   ├── templates/          # HTML templates
│   ├── views.py            # Logic AI + API
│   └── urls.py
├── static/
│   ├── css/styles.css
│   ├── js/chartSetup.js
│   └── img/
├── models/                 # File .pkl (được tạo tự động)
├── weather.csv             # Dữ liệu training (~8640 dòng)
├── .env                    # API key (không commit)
├── .env.example            # Template cho .env
└── manage.py
```

---

## 📊 Dữ liệu Training

Dữ liệu hourly từ **Visual Crossing** — TP. Hồ Chí Minh, 01/01/2025 đến 26/12/2025.

| Đặc điểm | Chi tiết |
|---|---|
| Tổng dòng | ~8,640 |
| Tần suất | Hourly (1 dòng/giờ) |
| Bao phủ | Đủ mùa khô + mùa mưa |
| Features | MinTemp, MaxTemp, WindGustDir, WindGustSpeed, Humidity, Pressure, Temp, Hour, Month |