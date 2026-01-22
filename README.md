# 🚌 Intelligent AP System for Public Transportation

대중교통 내 효율적인 통신 환경 제공을 위한 지능형 AP 시스템

> DNN 기반 서비스 예측 및 Linux Traffic Control을 활용한 동적 대역폭 할당 시스템

## 📋 Overview

본 프로젝트는 대중교통(버스, 지하철 등) 환경에서 제한된 네트워크 대역폭을 효율적으로 분배하기 위한 지능형 AP 시스템입니다. DNN(Deep Neural Network)을 활용하여 클라이언트의 서비스 사용 패턴을 분석하고, Linux TC(Traffic Control)를 통해 서비스 유형별로 최적화된 대역폭을 동적으로 할당합니다.

### 주요 기능

- **서비스 유형 분류**: RTT, Throughput 데이터를 기반으로 3가지 서비스 유형 분류
- **DNN 기반 예측**: 클라이언트별 주 사용 서비스 예측
- **동적 대역폭 할당**: Linux TC의 HTB Qdisc를 활용한 실시간 대역폭 제어

### 서비스 유형 및 대역폭

| Service Type | Description | Bandwidth |
|:------------:|-------------|:---------:|
| 0 | Video Streaming | 1 Mbps |
| 1 | Audio Streaming | 500 Kbps |
| 2 | Message (Text) | 10 Kbps |

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Intelligent AP (Server)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │   main6.py  │───▶│  log.csv    │───▶│  dnn_pred.py    │  │
│  │  (Server)   │    │ (RTT, Thru) │    │  (Prediction)   │  │
│  └─────────────┘    └─────────────┘    └────────┬────────┘  │
│                                                  │           │
│                                                  ▼           │
│                                        ┌─────────────────┐  │
│                                        │ TC Bandwidth    │  │
│                                        │ Control (HTB)   │  │
│                                        └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ Client 0 │      │ Client 1 │      │ Client 2 │
    │ (Video)  │      │ (Audio)  │      │ (Message)│
    │  1Mbps   │      │ 500Kbps  │      │  10Kbps  │
    └──────────┘      └──────────┘      └──────────┘
```

## 📁 Project Structure

```
IntelligentAP/
├── AP/
│   ├── main6.py              # AP 서버 (메인)
│   ├── dnn_pred.py           # DNN 예측 및 대역폭 할당
│   ├── tc_bandwidth_control.sh  # TC 제어 스크립트
│   ├── model.h5              # 학습된 DNN 모델
│   ├── output.ts             # 테스트용 비디오 파일
│   ├── audio.mp3             # 테스트용 오디오 파일
│   └── log/
│       └── log.csv           # 수집된 네트워크 로그
├── Client/
│   └── client_main3.py       # 클라이언트 프로그램
└── README.md
```

## 🚀 Getting Started

### Prerequisites

**Server (Raspberry Pi / Linux)**
```bash
# Python 패키지
pip install tensorflow numpy pandas keras scikit-learn matplotlib

# TC (Traffic Control) - 대부분의 Linux 배포판에 기본 설치됨
sudo apt-get install iproute2
```

**Client**
```bash
pip install numpy
```

### Installation

```bash
# 저장소 클론
git clone https://github.com/yourusername/IntelligentAP.git
cd IntelligentAP

# TC 스크립트 실행 권한 부여
chmod +x AP/tc_bandwidth_control.sh
```

### Configuration

`dnn_pred.py`에서 네트워크 인터페이스 설정:
```python
INTERFACE = "wlan0"  # 무선 인터페이스 이름 (ifconfig로 확인)
```

`main6.py`에서 서버 설정:
```python
HOST = '0.0.0.0'
PORT = 2222
```

`client_main3.py`에서 서버 IP 설정:
```python
sender_ip = '192.168.32.1'  # AP 서버 IP
sender_port = 2222
```

## 💻 Usage

### 1. AP 서버 실행

```bash
cd AP
sudo python3 main6.py
```

### 2. 클라이언트 연결

```bash
cd Client
python3 client_main3.py
```

클라이언트 명령어:
- `v` : Video 주 사용자로 테스트 (Video 600회, Audio 200회, Message 200회)
- `a` : Audio 주 사용자로 테스트 (Audio 600회, Video 200회, Message 200회)
- `m` : Message 주 사용자로 테스트 (Message 600회, Video 200회, Audio 200회)
- `q` : 종료

### 3. DNN 예측 및 대역폭 할당 실행

```bash
cd AP
sudo python3 dnn_pred.py
```

### 4. TC 스크립트 직접 사용

```bash
# TC 초기화
sudo ./tc_bandwidth_control.sh init

# 특정 클라이언트에 대역폭 할당
sudo ./tc_bandwidth_control.sh set 192.168.32.4 2    # Message (10Kbps)
sudo ./tc_bandwidth_control.sh set 192.168.32.9 1    # Audio (500Kbps)
sudo ./tc_bandwidth_control.sh set 192.168.32.2 0    # Video (1Mbps)

# 현재 TC 상태 확인
sudo ./tc_bandwidth_control.sh status

# TC 규칙 초기화
sudo ./tc_bandwidth_control.sh reset
```

## 🧠 Algorithm

### Service Prediction and Bandwidth Allocation (Algorithm 1)

```
Input: Pre-trained DNN model, Network log data
Output: Bandwidth allocation per client

1.  model ← load pre-trained model from './model.h5'
2.  df ← read data from './log.csv'
3.  x_data ← select columns 'RTT', 'Throughput' from df
4.  y_pred ← predict service type using model with x_data
5.  predicted_classes ← argmax(y_pred)
6.  device_data ← select column 'device' from df
7.  max_device_index ← max(device_data)
8.  Initialize client_service[max_device_index + 1][3] to 0
9.  for i = 0 to len(predicted_classes):
10.     client_service[device_data[i]][predicted_classes[i]] += 1
11. end for
12. max_columns ← argmax(client_service, axis=1)
13. call handle_bandwidth(max_columns, device_ip)
```

### 대역폭 할당 플로우

```
┌─────────────────┐
│ 네트워크 로그    │
│ (RTT, Throughput)│
└────────┬────────┘
         ▼
┌─────────────────┐
│ DNN 모델 예측    │
│ (서비스 유형 분류)│
└────────┬────────┘
         ▼
┌─────────────────┐
│ 클라이언트별     │
│ 주 사용 서비스   │
│ 집계            │
└────────┬────────┘
         ▼
┌─────────────────┐
│ TC 대역폭 할당   │
│ (HTB Qdisc)     │
└─────────────────┘
```

## 📊 Expected Results

### 서비스 분류 결과 예시

```
predict class result
---------------------------------------------
| Client  | Video | Audio | Message |
---------------------------------------------
| client 0|    12 |    40 |      20 |  → Audio
| client 1|    22 |     8 |      18 |  → Video
| client 2|     4 |    12 |      60 |  → Message
---------------------------------------------

most used service
-----------------------------------
| Client0 | Client1 | Client2 |
-----------------------------------
|    1    |    0    |    2    |
-----------------------------------
```

### 대역폭 할당 결과

```
==================================================
Intelligent AP - Bandwidth Allocation
==================================================
[INFO] TC initialized successfully
[INFO] 192.168.32.4 -> 500kbit (Audio Streaming)
[INFO] 192.168.32.9 -> 1mbit (Video Streaming)
[INFO] 192.168.32.2 -> 10kbit (Message)
==================================================
Bandwidth allocation completed
==================================================
```

## 🔧 TC (Traffic Control) Details

본 시스템은 Linux TC의 HTB(Hierarchical Token Bucket) Qdisc를 사용합니다.

### HTB 구조

```
root (1:)
  └── class 1:1 (10Mbit - Total)
        ├── class 1:4   (Client 0 - Service based)
        ├── class 1:9   (Client 1 - Service based)
        ├── class 1:2   (Client 2 - Service based)
        └── class 1:99  (Default - 1Mbit)
```

### 필터 규칙

각 클라이언트의 IP 주소를 기반으로 트래픽을 분류하고 해당 클래스로 라우팅합니다.

## 📝 Log Format

`log.csv` 파일 형식:

| Column | Description | Example |
|--------|-------------|---------|
| rtt | Round Trip Time (sec) | 0.0234 |
| throughput | Throughput (MB/sec) | 1.5432 |
| service | Service Type (0/1/2) | 1 |
| device | Device ID | 0 |
| ip_add | Client IP Address | 192.168.32.4 |

## 🛠️ Troubleshooting

### TC 권한 오류
```bash
# sudo 권한 필요
sudo python3 dnn_pred.py
```

### 네트워크 인터페이스 확인
```bash
# 무선 인터페이스 이름 확인
ifconfig
# 또는
ip link show
```

### TC 규칙 확인
```bash
# 현재 적용된 규칙 확인
tc qdisc show dev wlan0
tc class show dev wlan0
tc filter show dev wlan0
```

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- **Your Name** - *Initial work*

## 🙏 Acknowledgments

- 본 연구는 대중교통 환경에서의 네트워크 효율성 향상을 목표로 수행되었습니다.
- Linux Traffic Control 및 TensorFlow/Keras 프레임워크를 활용하였습니다.
