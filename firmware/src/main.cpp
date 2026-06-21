#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h"

DHT dht(26, DHT11);

const char *ssid = WIFI_SSID;
const char *password = WIFI_PASSWORD;
// Thay 192.168.x.x bằng địa chỉ IP IPv4 của máy tính chạy Django
const char *serverName = SERVER_NAME;

void setup()
{
  Serial.begin(9600);
  delay(2000);
  dht.begin();

  // Thêm phần kết nối WiFi
  Serial.println("\nConnecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected to WiFi network!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void reconnectWiFi()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("WiFi mất kết nối, đang kết nối lại...");
    WiFi.disconnect();
    WiFi.begin(ssid, password);
    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 20)
    {
      delay(500);
      Serial.print(".");
      retry++;
    }
    if (WiFi.status() == WL_CONNECTED)
      Serial.println("\nKết nối lại thành công!");
    else
      Serial.println("\nKết nối lại thất bại!");
  }
}

void loop()
{
  float temp = dht.readTemperature();
  float humidity = dht.readHumidity();

  Serial.print("Temp: ");
  Serial.print(temp);
  Serial.print(" C ");
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.println(" % ");

  if (isnan(temp) || isnan(humidity))
  {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }
  reconnectWiFi();
  if (WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;

    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    String httpRequestData = "{\"temperature\": " + String(temp) + ", \"humidity\": " + String(humidity) + "}";

    int httpResponseCode = http.POST(httpRequestData);

    if (httpResponseCode > 0)
    {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      Serial.println("Server reply: " + http.getString());
    }
    else
    {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }
  else
  {
    Serial.println("WiFi Disconnected");
  }

  delay(10000);
}