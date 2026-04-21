import tkinter as tk
import subprocess
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# 遠端桌面資訊
# 固定IP及帳號密碼
# 使用者不會知道
REMOTE_HOST = os.getenv("RDP_HOST")
USERNAME = os.getenv("RDP_USER")
PASSWORD = os.getenv("RDP_PWD")
RDP_FILE = "198.rdp"
STATUS_URL = os.getenv("API_ENDPOINT")  # Web API URL


def check_server_status():
    # 透過Web API獲取Server上接收遠端工作機登入狀態
    try:
        response = requests.get(STATUS_URL)
        if response.status_code == 200:
            data = response.json()  # 處理JSON格式的回應
            status = data.get("content", "ERROR")  # 取得content鍵的值
            return status.strip()  # 返回狀態值
        else:
            print("無法取得狀態，伺服器連線錯誤")
            return "ERROR"
    except Exception as e:
        print(f"錯誤: {e}")
        return "ERROR"


def save_credentials():
    # 儲存 Windows憑證"
    cmd = f'cmdkey /generic:{REMOTE_HOST} /user:{USERNAME} /pass:{PASSWORD}'
    subprocess.run(cmd, shell=True)


def create_rdp_file():
    #建立 .rdp 設定檔
    rdp_content = f"""screen mode id:i:2
desktopwidth:i:1280
desktopheight:i:720
session bpp:i:32
full address:s:{REMOTE_HOST}
username:s:{USERNAME}
enablecredsspsupport:i:1
authentication level:i:2
prompt for credentials:i:0
"""
    with open(RDP_FILE, "w") as file:
        file.write(rdp_content)


def delete_credentials():
    # 刪除儲存的憑證
    cmd = f'cmdkey /delete:{REMOTE_HOST}'
    subprocess.run(cmd, shell=True)


def connect_rdp():
    # 檢查伺服器的狀態
    server_status = check_server_status()

    if server_status == "IN USE":
        status_label.config(text="目前有人使用中唷", fg="red")
        connect_button.config(state=tk.DISABLED)
        return
    elif server_status == "FREE":
        status_label.config(text="可以連線囉", fg="green")
        connect_button.config(state=tk.NORMAL)
    else:
        status_label.config(text="連線錯誤，請通知資訊部處理", fg="orange")
        connect_button.config(state=tk.DISABLED)

    # 如果伺服器是FREE(無人連線))，則可以執行連線
    if server_status == "FREE":
        save_credentials()  # 儲存帳密
        create_rdp_file()   # 產生RDP設定檔

        # 啟動RDP連線
        subprocess.Popen(["mstsc", RDP_FILE], shell=True)

        # 等待遠端桌面啟動(15秒)
        time.sleep(15)

        # 刪除遠端憑證，確保有人透過該程式登入
        delete_credentials()

        # 刪除產生的RDP設定檔
        try:
            os.remove(RDP_FILE)
        except:
            pass #略過

        status_label.config(text="連線成功", fg="green")


def update_status():
    server_status = check_server_status()

    #如果有人使用中，則禁用連線按鈕
    if server_status == "IN USE":
        status_label.config(text="目前有人使用中唷", fg="red")
        connect_button.config(state=tk.DISABLED)
    #否則啟用連線按鈕
    elif server_status == "FREE":
        status_label.config(text="可以連線囉", fg="green")
        connect_button.config(state=tk.NORMAL)
    else:
    #當接收到的API有誤時，顯示錯誤訊息並禁用連線按鈕
        status_label.config(text="連線錯誤，請通知資訊部處理", fg="orange")
        connect_button.config(state=tk.DISABLED)

    # 5秒後再次檢查
    root.after(5000, update_status)


# GUI介面
root = tk.Tk()
root.title("遠端AutoCAD連線")
root.geometry("300x200")

label = tk.Label(root, text=f"連線到 {REMOTE_HOST}", font=("Arial", 12))
label.pack(pady=10)

connect_button = tk.Button(root, text="連線", command=connect_rdp, font=("Arial", 12), width=10)
connect_button.pack(pady=10)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack()

update_status()

root.mainloop()
