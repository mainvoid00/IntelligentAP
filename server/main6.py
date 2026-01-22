
import threading
import os
import socket
#import delay
import time
import csv
import sys
import struct
import pickle

HOST = '0.0.0.0'
PORT = 2222
message= "Hello this is testHello this is testHello this is testHello this is test"
video_file = "./output.ts"
audio_file = "./audio.mp3"

number = []



lock = threading.Lock()  # Lock

def write_to_csv(filename, rtt, throughput, service, device):
    # CSV not exists
    if os.path.exists(filename) == False:
        with open(filename, mode='a', newline='') as file:
            writer= csv.writer(file)
            writer.writerow(["rtt","throughput","service","device"])

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        # CSV
        writer.writerow([rtt, throughput, service, device])

def send_message_func(conn, addr, command, device):
    
    message_size_bytes = len(message.encode())
    print(message_size_bytes, " byte")
    data_size_mb = message_size_bytes / (1024* 1024)
    print("data_size_MB=",data_size_mb)
   
    if command == 'm':
        repeat = 600
    elif command == 'a':
        repeat = 200
    elif command == 'v':
        repeat = 200
        
    for i in range(repeat):
        with lock:
            server_time = time.time()
            conn.send(message.encode())
            send_complete_time = time.time()
            #conn.send("end")
            if(conn.recv(1024).decode() == "a"):
                client_time = time.time()


            rtt= client_time - server_time
            ##
            throughput = (data_size_mb / (0.5 + (send_complete_time-server_time)))  # MB/sec
            print(number.index(addr) + 1,"i:", i)
            print(f"rtt = {rtt:.4f} sec, throughput = {throughput:.4f} MB/sec")
    
            write_to_csv('./log/log.csv', rtt, throughput, 2, device)
            #time.sleep(0.1)
            
            
    



def send_video_func(conn, addr, command, device):
    if command == 'm':
        repeat = 200
    elif command == 'a':
        repeat = 200
    elif command == 'v':
        repeat = 600
        
    for i in range(repeat):
        with open(video_file, 'rb') as file:
            file_size = os.path.getsize(video_file)

            #print("file size = ", file_size)
            conn.sendall(str(file_size).encode())
            conn.recv(1024) #ack 
            
            

            print("")
            server_time = time.time()
            
            while True:
                

                block = file.read(4096)

                if not block:
                    break

                conn.sendall(block)
            
            
            send_complete_time = time.time()
            print("")
            #time.sleep(0.03)
            #conn.send("endend".encode())

        while True:
            ack = conn.recv(1024).decode()
            client_time = time.time()
            print("ack")
            
            print(ack)
            if(ack == "a"):
                break
            else:
                print("ack")
                continue

        rtt = client_time - server_time
        throughput = (file_size /(1024*1024) / (send_complete_time - server_time))
        print(number.index(addr) + 1,"i:", i)
        print(f"rtt = {rtt:.4f} sec, throughput = {throughput:.4f} MB/sec, ")
        write_to_csv('./log/log.csv', rtt, throughput, 0, device)





def send_audio_func(conn, addr, command, device):
    if command == 'm':
        repeat = 200
    elif command == 'a':
        repeat = 600
    elif command == 'v':
        repeat = 200
        
    for i in range(repeat):
        with open(audio_file, 'rb') as file:
            file_size = os.path.getsize(audio_file)

            print("file size = ", file_size)
            conn.sendall(str(file_size).encode())
            conn.recv(1024) #ack
            
            

            print("")
            server_time = time.time()
            
            while True:
                

                block = file.read(2048)

                if not block:
                    break

                conn.sendall(block)
            
            
            send_complete_time = time.time()
            print("")
            #time.sleep(0.03)
            

        while True:
            ack = conn.recv(1024).decode()
            client_time = time.time()
            print("ack")
            
            print(ack)
            if(ack == "a"):
                break
            else:
                print("ack")
                continue

        rtt = client_time - server_time
        throughput = (file_size / (1024*1024) / (send_complete_time - server_time))
        print(number.index(addr) + 1,"i:", i)
        print(f"rtt = {rtt:.4f} sec, throughput = {throughput:.4f} MB/sec")
        write_to_csv('./log/log.csv', rtt, throughput, 1, device)




def handle_client(conn, addr):
    while True:
        command = conn.recv(1024)
        command = command.decode()
        print(command)
        if(command == "q"):
            break

        elif(command == "m"):
            device=2
            send_message_func(conn, addr, command, device)
            send_audio_func(conn, addr, command, device)
            send_video_func(conn, addr, command, device)

        elif(command == "v"):
            device=1
            send_message_func(conn, addr, command, device)
            send_audio_func(conn, addr, command, device)
            send_video_func(conn, addr, command, device)
            
        elif(command == "a"):
            device=0
            send_message_func(conn, addr, command, device)
            send_audio_func(conn, addr, command, device)
            send_video_func(conn, addr, command, device)
            
        else:
            print("command retry")

    conn.close()
    #s.close()

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(5)
        print("Server is ready...")
        while True:
            conn, addr = s.accept()
            number.append(addr)
            print(f"Connected to {addr}")
            handle_thread = threading.Thread(target=handle_client, args=(conn, addr))
            handle_thread.start()
    
if __name__ == "__main__":
    main()


'''

while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        print("ready...")
        s.listen()
        conn, addr = s.accept()
        print ('Connected by', addr)
        handle_thread = threading.Thread(target=handle_client, args=(conn,))
        handle_thread.start()

'''