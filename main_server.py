
import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# --- MQTT Configuration ---
MQTT_BROKER = "mqtt.eclipseprojects.io"  # Using a public broker for demonstration
MQTT_PORT = 1883
TOPIC_TEMP_AMB82 = "gemini/home/amb82/temperature"
TOPIC_TEMP_ESP32 = "gemini/home/esp32/temperature"
TOPIC_IR_LEARN_REQ = "gemini/home/amb82/ir/learn/request"
TOPIC_IR_LEARN_RES = "gemini/home/amb82/ir/learn/response"
TOPIC_IR_SEND_REQ = "gemini/home/amb82/ir/send/request"

IR_CODES_FILE = "ir_codes.json"

# --- Application State ---
if 'client_status' not in st.session_state:
    st.session_state.client_status = {
        "amb82": {"connected": False, "last_seen": None, "temperature": None},
        "esp32": {"connected": False, "last_seen": None, "temperature": None}
    }
if 'ir_codes' not in st.session_state:
    st.session_state.ir_codes = {}
if 'learning_mode' not in st.session_state:
    st.session_state.learning_mode = False


# --- Helper Functions ---
def load_ir_codes():
    try:
        with open(IR_CODES_FILE, 'r') as f:
            st.session_state.ir_codes = json.load(f)
    except FileNotFoundError:
        st.session_state.ir_codes = {}

def save_ir_codes():
    with open(IR_CODES_FILE, 'w') as f:
        json.dump(st.session_state.ir_codes, f, indent=4)

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    st.write(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe([(TOPIC_TEMP_AMB82, 0), (TOPIC_TEMP_ESP32, 0), (TOPIC_IR_LEARN_RES, 0)])

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    if msg.topic == TOPIC_TEMP_AMB82:
        st.session_state.client_status['amb82']['temperature'] = float(payload)
        st.session_state.client_status['amb82']['last_seen'] = time.time()
        st.session_state.client_status['amb82']['connected'] = True
    elif msg.topic == TOPIC_TEMP_ESP32:
        st.session_state.client_status['esp32']['temperature'] = float(payload)
        st.session_state.client_status['esp32']['last_seen'] = time.time()
        st.session_state.client_status['esp32']['connected'] = True
    elif msg.topic == TOPIC_IR_LEARN_RES:
        st.session_state.learning_mode = False
        # For now, let's just display the learned code.
        # In the future, we'll save it with a name.
        st.session_state.learned_code = payload
        st.rerun()

def setup_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    return client

# --- UI Layout ---
st.set_page_config(layout="wide")
st.title("家用智能管家 (Home Smart Butler)")

# --- Main Application ---
load_ir_codes()
client = setup_mqtt()
client.loop_start()

# Check for client timeouts
for client_name, status in st.session_state.client_status.items():
    if status['last_seen'] and (time.time() - status['last_seen']) > 60:
        st.session_state.client_status[client_name]['connected'] = False

# --- Display Panels ---
st.header("設備狀態與溫度監控")
temp_threshold = st.sidebar.number_input("溫度警示閾值 (°C)", value=30.0, step=0.5)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("Client: amb82")
        status = st.session_state.client_status['amb82']
        st.metric("連線狀態", "🟢 在線" if status['connected'] else "🔴 離線")
        temp = status['temperature']
        if temp is not None and temp > temp_threshold:
            st.metric("溫度", f"{temp}°C", delta="過高", delta_color="inverse")
        else:
            st.metric("溫度", f"{temp}°C" if temp is not None else "N/A")

with col2:
    with st.container(border=True):
        st.subheader("Client: ESP32")
        status = st.session_state.client_status['esp32']
        st.metric("連線狀態", "🟢 在線" if status['connected'] else "🔴 離線")
        temp = status['temperature']
        if temp is not None and temp > temp_threshold:
            st.metric("溫度", f"{temp}°C", delta="過高", delta_color="inverse")
        else:
            st.metric("溫度", f"{temp}°C" if temp is not None else "N/A")


st.divider()

# --- IR Remote Control Panel ---
st.header("紅外線遙控器 (amb82)")

with st.container(border=True):
    st.subheader("遙控器學習")
    if st.button("進入學習模式", disabled=st.session_state.learning_mode):
        client.publish(TOPIC_IR_LEARN_REQ, "START")
        st.session_state.learning_mode = True
        st.session_state.learned_code = None
        st.rerun()

    if st.session_state.learning_mode:
        st.info("等待 amb82 接收紅外線訊號中...")

    if 'learned_code' in st.session_state and st.session_state.learned_code:
        st.success(f"學習到新的 IR Code: {st.session_state.learned_code}")
        new_code_name = st.text_input("請為此遙控碼命名:")
        if st.button("儲存遙控碼"):
            if new_code_name:
                st.session_state.ir_codes[new_code_name] = st.session_state.learned_code
                save_ir_codes()
                st.success(f"已儲存 '{new_code_name}'")
                st.session_state.learned_code = None # Clear after saving
                st.rerun()
            else:
                st.error("請輸入名稱！")


    st.subheader("已存遙控器")
    if not st.session_state.ir_codes:
        st.caption("尚未儲存任何遙控碼。")
    else:
        ir_cols = st.columns(4)
        col_idx = 0
        for name, code in st.session_state.ir_codes.items():
            with ir_cols[col_idx % 4]:
                if st.button(name, key=f"ir_btn_{name}", use_container_width=True):
                    client.publish(TOPIC_IR_SEND_REQ, code)
                    st.toast(f"已傳送 '{name}'")
            col_idx += 1

# Keep the app running
st.rerun()
