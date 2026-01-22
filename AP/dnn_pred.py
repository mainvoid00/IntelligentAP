import numpy as np
import sys
import tensorflow as tf
import os
import matplotlib.pyplot as plt
import pandas as pd
import keras
import datetime
import time
import subprocess
from sklearn.model_selection import train_test_split

from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense


# =============================================================================
# TC 대역폭 제어 설정
# =============================================================================

INTERFACE = "wlan0"  # 네트워크 인터페이스 (환경에 맞게 수정)

# 서비스별 대역폭 (main6.py 기준: 0=Video, 1=Audio, 2=Message)
BANDWIDTH_CONFIG = {
    0: "1mbit",      # Video Streaming - 1Mbps
    1: "500kbit",    # Audio Streaming - 500Kbps
    2: "10kbit",     # Message - 10Kbps
}

SERVICE_NAMES = {
    0: "Video Streaming",
    1: "Audio Streaming",
    2: "Message"
}


def find_max_columns(matrix):
    max_columns = []
    for row in matrix:
        max_val = max(row)
        max_col = row.index(max_val)
        max_columns.append(max_col)
    return max_columns


def init_tc():
    """TC(Traffic Control) 초기화 - HTB Qdisc 설정"""
    try:
        # 기존 규칙 제거
        subprocess.run(
            ["sudo", "tc", "qdisc", "del", "dev", INTERFACE, "root"],
            capture_output=True, check=False
        )
        # HTB root qdisc 생성
        subprocess.run(
            ["sudo", "tc", "qdisc", "add", "dev", INTERFACE, "root", 
             "handle", "1:", "htb", "default", "99"],
            check=True
        )
        # 루트 클래스 생성
        subprocess.run(
            ["sudo", "tc", "class", "add", "dev", INTERFACE, "parent", "1:",
             "classid", "1:1", "htb", "rate", "10mbit"],
            check=True
        )
        # 기본 클래스
        subprocess.run(
            ["sudo", "tc", "class", "add", "dev", INTERFACE, "parent", "1:1",
             "classid", "1:99", "htb", "rate", "1mbit", "ceil", "10mbit"],
            check=True
        )
        print("[INFO] TC initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] TC initialization failed: {e}")
        return False


def set_bandwidth_for_client(ip_address, service_type):
    """특정 클라이언트에 대역폭 할당"""
    if service_type not in BANDWIDTH_CONFIG:
        print(f"[ERROR] Unknown service type: {service_type}")
        return False
    
    bandwidth = BANDWIDTH_CONFIG[service_type]
    service_name = SERVICE_NAMES[service_type]
    
    # IP의 마지막 옥텟을 클래스 ID로 사용
    class_id = int(ip_address.split('.')[-1])
    if class_id == 0:
        class_id = 100
    
    try:
        # 기존 클래스 삭제
        subprocess.run(
            ["sudo", "tc", "class", "del", "dev", INTERFACE, 
             "classid", f"1:{class_id}"],
            capture_output=True, check=False
        )
        # 새 클래스 생성
        subprocess.run(
            ["sudo", "tc", "class", "add", "dev", INTERFACE, "parent", "1:1",
             "classid", f"1:{class_id}", "htb", "rate", bandwidth, "ceil", bandwidth],
            check=True
        )
        # 목적지 IP 필터
        subprocess.run(
            ["sudo", "tc", "filter", "add", "dev", INTERFACE, "protocol", "ip",
             "parent", "1:0", "prio", "1", "u32", "match", "ip", "dst",
             f"{ip_address}/32", "flowid", f"1:{class_id}"],
            check=True
        )
        # 출발지 IP 필터
        subprocess.run(
            ["sudo", "tc", "filter", "add", "dev", INTERFACE, "protocol", "ip",
             "parent", "1:0", "prio", "1", "u32", "match", "ip", "src",
             f"{ip_address}/32", "flowid", f"1:{class_id}"],
            check=True
        )
        
        print(f"[INFO] {ip_address} -> {bandwidth} ({service_name})")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to set bandwidth for {ip_address}: {e}")
        return False


def handdle_bandwidth(max_colums, device_ip):
    """
    각 클라이언트의 주 사용 서비스에 따라 대역폭 할당
    
    Args:
        max_colums: 각 디바이스별 가장 많이 사용하는 서비스 타입 리스트
        device_ip: 각 디바이스의 IP 주소 리스트
    """
    print("=" * 50)
    print("Intelligent AP - Bandwidth Allocation")
    print("=" * 50)
    
    # TC 초기화
    if not init_tc():
        print("[ERROR] TC initialization failed. Aborting.")
        return
    
    # 각 클라이언트에 대역폭 할당
    for i in range(len(max_colums)):
        service_type = max_colums[i]
        ip_address = device_ip[i]
        
        if ip_address is None:
            print(f"[WARNING] Device {i}: No IP address")
            continue
        
        if service_type == 0:
            # Video Streaming - 1Mbps
            set_bandwidth_for_client(ip_address, 0)
        elif service_type == 1:
            # Audio Streaming - 500Kbps
            set_bandwidth_for_client(ip_address, 1)
        else:
            # Message - 10Kbps
            set_bandwidth_for_client(ip_address, 2)
    
    print("=" * 50)
    print("Bandwidth allocation completed")
    print("=" * 50)


def extract_ip(ip_data):
    ip_address = ip_data.split(',')[0].strip("('")
    return ip_address


def predict_func():

    print(os.getcwd())
    
    model = keras.models.load_model('./model.h5')

    df = pd.read_csv("./log3.csv")


    x_data = df[['rtt','throughput']]

    y_data= df['service']
    Y_data = tf.keras.utils.to_categorical(y_data)
    device_data = df['device']
    
    ip_add= df['ip_add'].apply(extract_ip)


    print(ip_add)

    y_pred = model.predict(x_data)
    predicted_classes = np.argmax(y_pred, axis=1)



    raw =max(device_data)

    device_ip = [None] * (max(device_data) + 1)
    for i in range(len(device_data)):
        device_ip[device_data[i]] = ip_add[i]

    

    client_service= []

    for i in range(raw+1):
        line = []
        for i in range(3):
            line.append(0)
        client_service.append(line)
        


    for i in range(len(y_data)):
        client_service[device_data[i]][y_data[i]]+=1
        
    
    print("client_service:", client_service)

    max_columns = find_max_columns(client_service)
    print("max_columns:", max_columns)

    print("device_ip:", device_ip)

    # 대역폭 할당 호출
    handdle_bandwidth(max_columns, device_ip)


def main():
    #predict_func()
    start_time=datetime.datetime.now()
    while True:
        now=datetime.datetime.now()
        elapsed_time = now - start_time
        print(now-start_time)
        if elapsed_time.total_seconds() > 1:
            predict_func()
            break

        time.sleep(1)
        
        

        
    



if __name__ == "__main__":
    main()