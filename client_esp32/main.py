# main.py for ESP32

import machine
import dht
import time
from umqtt.simple import MQTTClient
import network

# --- Configuration ---
WIFI_SSID = "Owner"  # Please change this to your WiFi SSID
WIFI_PASSWORD = "qwertyui" # Please change this to your WiFi password

MQTT_BROKER = "mqtt.eclipseprojects.io"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "esp32_gemini_client"
TOPIC_TEMP_ESP32 = b"gemini/home/esp32/temperature"

# Hardware Pins
DHT_PIN = machine.Pin(4)  # Assuming DHT11 data pin is connected to GPIO 4

# --- Global Variables ---
station = network.WLAN(network.STA_IF)
client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, port=MQTT_PORT)
d = dht.DHT11(DHT_PIN)

# --- Functions ---
def connect_wifi():
    """Connects to the WiFi network."""
    print("Connecting to WiFi...", end="")
    station.active(True)
    station.connect(WIFI_SSID, WIFI_PASSWORD)
    while not station.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print(f"\nConnected! Network config: {station.ifconfig()}")

def connect_mqtt():
    """Connects to the MQTT broker."""
    print("Connecting to MQTT broker...")
    client.connect()
    print("Connected to MQTT broker.")

# --- Main Loop ---
def main():
    """Main loop to read sensor and publish data."""
    connect_wifi()
    connect_mqtt()

    while True:
        try:
            print("\nReading sensor...")
            d.measure()
            temp = d.temperature()
            # hum = d.humidity() # Uncomment if you want to use humidity
            
            if isinstance(temp, (int, float)):
                print(f"Temperature: {temp}°C")
                client.publish(TOPIC_TEMP_ESP32, str(temp).encode('utf-8'))
                print("Published temperature to MQTT.")
            else:
                print("Failed to read sensor.")

            # Wait for 30 seconds before the next reading
            print("Waiting for 30 seconds...")
            time.sleep(30)

        except OSError as e:
            print(f"Error: {e}. Reconnecting...")
            try:
                client.disconnect()
            except:
                pass
            connect_mqtt()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("Rebooting in 10 seconds...")
            time.sleep(10)
            machine.reset()

if __name__ == "__main__":
    main()
