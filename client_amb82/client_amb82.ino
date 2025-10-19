// client_amb82.ino for Realtek Ameba AMB82

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <IRremote.h>

// --- Configuration ---
const char* ssid = "YOUR_WIFI_SSID";         // Please change this
const char* password = "YOUR_WIFI_PASSWORD"; // Please change this

const char* mqtt_server = "mqtt.eclipseprojects.io";
const int mqtt_port = 1883;
const char* mqtt_client_id = "amb82_gemini_client";

// MQTT Topics
const char* topic_temp_amb82 = "gemini/home/amb82/temperature";
const char* topic_ir_learn_req = "gemini/home/amb82/ir/learn/request";
const char* topic_ir_learn_res = "gemini/home/amb82/ir/learn/response";
const char* topic_ir_send_req = "gemini/home/amb82/ir/send/request";

// Hardware Pins (Ameba)
#define DHTPIN PA_12
#define DHTTYPE DHT11
int irRecvPin = PA_13;
int irSendPin = PA_14; // Pin for IR LED

// --- Global Objects ---
WiFiClient wifiClient;
PubSubClient client(wifiClient);
DHT dht(DHTPIN, DHTTYPE);
IRrecv irrecv(irRecvPin);
IRsend irsend(irSendPin);
decode_results results; // To store IR receiving results

// --- State Variables ---
long lastMsg = 0;
bool learning_mode = false;

// --- Function Prototypes ---
void setup_wifi();
void reconnect_mqtt();
void mqtt_callback(char* topic, byte* payload, unsigned int length);
void enter_learning_mode();

// --- Setup Function ---
void setup() {
    Serial.begin(115200);
    dht.begin();
    irrecv.enableIRIn(); // Start the IR receiver
    irsend.begin();      // Start the IR sender

    setup_wifi();
    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(mqtt_callback);
}

// --- Main Loop ---
void loop() {
    if (!client.connected()) {
        reconnect_mqtt();
    }
    client.loop();

    // Handle IR Learning Mode
    if (learning_mode) {
        if (irrecv.decode(&results)) {
            // For this project, we'll send the raw data as a string
            // A more robust solution might use a specific protocol format
            String raw_code = "";
            for (int i = 1; i < results.rawlen; i++) {
                raw_code += String(results.rawbuf[i] * USECPERTICK, DEC);
                if (i < results.rawlen - 1) {
                    raw_code += ",";
                }
            }
            Serial.println("Learned new IR code:");
            Serial.println(raw_code);

            // Publish the learned code
            client.publish(topic_ir_learn_res, raw_code.c_str());
            
            learning_mode = false; // Exit learning mode after one capture
            irrecv.resume(); // Continue receiving
        }
        return; // Don't do other tasks while in learning mode
    }

    // Regular temperature check (every 30 seconds)
    long now = millis();
    if (now - lastMsg > 30000) {
        lastMsg = now;
        float t = dht.readTemperature();

        if (isnan(t)) {
            Serial.println("Failed to read from DHT sensor!");
            return;
        }

        Serial.print("Temperature: ");
        Serial.print(t);
        Serial.println(" *C");

        char tempString[8];
        dtostrf(t, 4, 2, tempString);
        client.publish(topic_temp_amb82, tempString);
    }
}

// --- WiFi & MQTT Functions ---
void setup_wifi() {
    delay(10);
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(ssid);

    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println("\nWiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
}

void reconnect_mqtt() {
    while (!client.connected()) {
        Serial.print("Attempting MQTT connection...");
        if (client.connect(mqtt_client_id)) {
            Serial.println("connected");
            // Subscribe to the topics
            client.subscribe(topic_ir_learn_req);
            client.subscribe(topic_ir_send_req);
        } else {
            Serial.print("failed, rc=");
            Serial.print(client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
    Serial.print("Message arrived on topic: ");
    Serial.print(topic);
    Serial.print(". Message: ");
    String message;
    for (int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    Serial.println(message);

    if (strcmp(topic, topic_ir_learn_req) == 0) {
        if (message == "START") {
            enter_learning_mode();
        }
    } else if (strcmp(topic, topic_ir_send_req) == 0) {
        // The payload should be the raw code string we saved earlier
        // We need to parse it back into an array of unsigned ints
        // This is a simplified parser. A robust implementation should handle errors.
        int* raw_array = new int[100]; // Assuming max length 100
        int count = 0;
        char* token = strtok((char*)message.c_str(), ",");
        while(token != NULL && count < 99){
            raw_array[count++] = atoi(token);
            token = strtok(NULL, ",");
        }
        
        Serial.println("Sending IR Code...");
        irsend.sendRaw(raw_array, count, 38); // 38KHz is common
        delete[] raw_array;
        Serial.println("Sent.");
    }
}

void enter_learning_mode() {
    Serial.println("Entering IR learning mode...");
    learning_mode = true;
    irrecv.resume(); // Make sure receiver is ready
}
