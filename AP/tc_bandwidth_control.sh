#!/bin/bash
# =============================================================================
# Intelligent AP - Bandwidth Control Script using TC (Traffic Control)
# 대중교통 내 효율적인 통신 환경 제공을 위한 지능형 AP 시스템
# =============================================================================

# 네트워크 인터페이스 설정 (환경에 맞게 수정)
INTERFACE="wlan0"

# 서비스별 대역폭 설정 (논문 기준)
# main6.py 기준: 0=Video, 1=Audio, 2=Message
BANDWIDTH_VIDEO="1mbit"
BANDWIDTH_AUDIO="500kbit"
BANDWIDTH_MESSAGE="10kbit"

# 전체 대역폭
TOTAL_BANDWIDTH="10mbit"

# =============================================================================
# 함수 정의
# =============================================================================

tc_reset() {
    echo "[INFO] Resetting TC rules on $INTERFACE..."
    tc qdisc del dev $INTERFACE root 2>/dev/null
    echo "[INFO] TC rules cleared."
}

tc_init() {
    echo "[INFO] Initializing HTB Qdisc on $INTERFACE..."
    tc qdisc add dev $INTERFACE root handle 1: htb default 99
    tc class add dev $INTERFACE parent 1: classid 1:1 htb rate $TOTAL_BANDWIDTH
    tc class add dev $INTERFACE parent 1:1 classid 1:99 htb rate 1mbit ceil $TOTAL_BANDWIDTH
    echo "[INFO] HTB Qdisc initialized."
}

# Usage: allocate_bandwidth <IP_ADDRESS> <SERVICE_TYPE> <CLASS_ID>
allocate_bandwidth() {
    local IP=$1
    local SERVICE_TYPE=$2
    local CLASS_ID=$3
    
    case $SERVICE_TYPE in
        0)  BANDWIDTH=$BANDWIDTH_VIDEO; SERVICE_NAME="Video" ;;
        1)  BANDWIDTH=$BANDWIDTH_AUDIO; SERVICE_NAME="Audio" ;;
        2)  BANDWIDTH=$BANDWIDTH_MESSAGE; SERVICE_NAME="Message" ;;
        *)  echo "[ERROR] Unknown service type: $SERVICE_TYPE"; return 1 ;;
    esac
    
    echo "[INFO] Allocating $BANDWIDTH to $IP (Service: $SERVICE_NAME, Class: 1:$CLASS_ID)"
    
    tc class del dev $INTERFACE classid 1:$CLASS_ID 2>/dev/null
    tc class add dev $INTERFACE parent 1:1 classid 1:$CLASS_ID htb rate $BANDWIDTH ceil $BANDWIDTH
    tc filter add dev $INTERFACE protocol ip parent 1:0 prio 1 u32 match ip dst $IP/32 flowid 1:$CLASS_ID
    tc filter add dev $INTERFACE protocol ip parent 1:0 prio 1 u32 match ip src $IP/32 flowid 1:$CLASS_ID
    
    echo "[INFO] Bandwidth allocated successfully."
}

tc_status() {
    echo "=============================================="
    echo "Current TC Configuration on $INTERFACE"
    echo "=============================================="
    echo "[Qdisc]"
    tc qdisc show dev $INTERFACE
    echo "[Classes]"
    tc class show dev $INTERFACE
    echo "[Filters]"
    tc filter show dev $INTERFACE
    echo "=============================================="
}

set_client_bandwidth() {
    local IP=$1
    local SERVICE_TYPE=$2
    local CLASS_ID=$(echo $IP | awk -F. '{print $4}')
    [ "$CLASS_ID" -eq 0 ] && CLASS_ID=100
    allocate_bandwidth $IP $SERVICE_TYPE $CLASS_ID
}

# =============================================================================
# 메인 실행
# =============================================================================

case "$1" in
    init)       tc_reset; tc_init ;;
    reset)      tc_reset ;;
    status)     tc_status ;;
    allocate)
        [ $# -lt 4 ] && { echo "Usage: $0 allocate <IP> <SERVICE_TYPE> <CLASS_ID>"; exit 1; }
        allocate_bandwidth $2 $3 $4 ;;
    set)
        [ $# -lt 3 ] && { echo "Usage: $0 set <IP> <SERVICE_TYPE>"; exit 1; }
        set_client_bandwidth $2 $3 ;;
    *)
        echo "Usage: $0 {init|reset|status|allocate|set}"
        echo "Service Types: 0=Video(1Mbps), 1=Audio(500Kbps), 2=Message(10Kbps)"
        exit 1 ;;
esac
exit 0
