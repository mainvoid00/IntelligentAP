import socket
import time
import threading
import os
import struct
import pickle

sender_ip = '127.0.0.1'
sender_port = 2222
video_file = './output.ts'
audio_file = './audio.mp3'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sender_ip, sender_port))
print("Sender IP:" ,sender_ip)

lock = threading.Lock()  # Lock 

def recv_message():
    if command == 'm':
        repeat = 600
    elif command == 'a':
        repeat = 200
    elif command == 'v':
        repeat = 200
        
    with lock:

        for i in range(repeat):
            
            data = s.recv(1024)
            client_time = time.time()
            
            message = data.decode()
            print("message:", message, i)
            ack="a"
            s.send(ack.encode())


def recv_video():
    if command == 'm':
        repeat = 200
    elif command == 'a':
        repeat = 200
    elif command == 'v':
        repeat = 600
        
   
    output_directory = "./output_video/"
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
    for i in range(repeat):

        file_size = int(s.recv(1024).decode())
        s.send(b"ACK")  # ACK 
        
        
        received_data = b""
        received_size = 0

        with open("./output_video/"+"1"+".mp4", 'wb') as file:
            
            while received_size < file_size:
                chunk = s.recv(4096)
                if not chunk:
                    break
                file.write(chunk)
                received_size += len(chunk)
                
                
                
                
        file.close()
               
                                
            
        print("i:", i)
        ack = "a"
        s.send(ack.encode())
        print("ACK")


        

    


def recv_audio():
    if command == 'm':
        repeat = 200
    elif command == 'a':
        repeat = 600
    elif command == 'v':
        repeat = 200
        
    output_directory = "./output_audio/"
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
        
    for i in range(repeat):

        file_size = int(s.recv(1024).decode())
        s.send(b"ACK")  # ACK
        
        
        received_data = b""
        received_size = 0

        with open("./output_audio/"+str(i)+".mp3", 'wb') as file:
            
            while received_size < file_size:
                chunk = s.recv(2048)
                if not chunk:
                    break
                file.write(chunk)
                received_size += len(chunk)
                
                
                
                
        file.close()
               
                                
            
        print("i:", i)
        ack = "a"
        s.send(ack.encode())
        print("ACK")



def iperf_test(iperf_cmd):
    result = os.popen(iperf_cmd).read()
    print(result)


def ping_test(ping_cmd):
    result = os.popen(ping_cmd).read()
    print(result)


while True:
    command = input()
    iperf_cmd = "iperf -c " + sender_ip + " -t 10 -i 1 -f M"
    ping_cmd = "ping " + sender_ip+ " -c 10"
    #iperf_test(iperf_cmd)
    if(command == "q"):
        s.send(command.encode())
        break
    
    elif(command == "v"):
        s.send(command.encode())
        recv_video()
        recv_message()
        recv_audio()

        #recv_video_cv2()
        

    elif(command == "m"):
        s.send(command.encode())
        Th1 = threading.Thread(target= iperf_test, args=(iperf_cmd,))
        Th2 = threading.Thread(target=ping_test, args=(ping_cmd,))
        Th1.start()
        Th2.start()
        
        
        recv_message()
        recv_audio()
        recv_video()
        Th1.join()
        Th2.join()
        
    
    elif(command == "a"):
        s.send(command.encode())
        recv_audio()
        recv_video()
        recv_message()


    else:
        print("command retry")
    



s.close()
