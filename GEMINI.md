# 專案：家用智能管家 (Home Smart Butler)

本專案是一個物聯網應用，包含一個中央伺服器和多個客戶端裝置，旨在監控和控制家庭環境。

## 🚀 Agent 快速上手指南

歡迎接手！請依循以下指南快速了解專案狀態與工作流程。

### 1. 版本控制 (GitHub)

*   **倉庫地址：** [https://github.com/love54125/AI_Project](https://github.com/love54125/AI_Project)
*   **認證方式：** 請確保您的環境中已設定 `GITHUB_PAT` 環境變數。此 PAT (Personal Access Token) 必須擁有 `repo` 權限，以便您提交程式碼。
*   **工作流程：** 所有變更都應透過 Git 提交，並推送到此倉庫。

### 2. 任務管理 (Google Tasks)

*   **用途：** 我們使用 Google Tasks 來追蹤專案的待辦事項。
*   **認證檔案：**
    *   `credentials.json`: 包含 Google Cloud 的 OAuth 2.0 用戶端憑證。**此檔案已設定完成。**
    *   `google_task_token.json`: 包含用來存取 Google Tasks API 的授權權杖。
*   **如何連線/操作：**
    *   **初次授權：** 如果 `google_task_token.json` 遺失或過期，請執行 `python generate_google_token.py`。此腳本會引導您完成瀏覽器授權，並產生新的權杖檔案。
    *   **新增任務：** 執行 `python task_manager.py` 可以將預設的專案任務新增到您的 Google Tasks 中。您可以修改此腳本來新增客製化任務。

### 3. 專案結構

*   `main_server.py`:
    *   **用途：** 基於 Streamlit 的視覺化伺服器。
    *   **功能：** 接收並顯示來自客戶端的數據、發送控制命令。
    *   **如何啟動：** `streamlit run main_server.py`

*   `client_esp32/`:
    *   **晶片：** ESP32
    *   **程式：** `main.py` (MicroPython)
    *   **功能：** 讀取 DHT11 溫度並透過 MQTT 回報。

*   `client_amb82/`:
    *   **晶片：** Realtek Ameba (AMB82)
    *   **程式：** `client_amb82.ino` (C++/Arduino)
    *   **功能：** 讀取 DHT11 溫度、學習紅外線訊號、發送紅外線訊號。

*   `requirements.txt`: 包含所有 Python 依賴套件。

---

## 原始專案需求 (摘要)

*   **核心功能：**
    *   即時監控 `amb82` 和 `ESP32` 的溫度。
    *   `amb82` 需具備紅外線遙控器的學習與發射能力。
*   **伺服器規格：**
    *   使用 Python 視覺化框架 (已選用 Streamlit)。
    *   與客戶端透過 MQTT 通訊。
    *   溫度超標時需有警示。
*   **通訊協議 (MQTT):**
    *   **Broker:** `mqtt.eclipseprojects.io`
    *   **Topics:**
        *   `gemini/home/esp32/temperature` (ESP32 -> Server)
        *   `gemini/home/amb82/temperature` (AMB82 -> Server)
        *   `gemini/home/amb82/ir/learn/request` (Server -> AMB82)
        *   `gemini/home/amb82/ir/learn/response` (AMB82 -> Server)
        *   `gemini/home/amb82/ir/send/request` (Server -> AMB82)
