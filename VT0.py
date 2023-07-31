from tkinter import *
# from PIL import Image, ImageTk
from multiprocessing import *
# from tkinter.ttk import *
from tkinter.filedialog import askopenfile
from tkinter import filedialog
from tkinter import ttk
from multiprocessing import Process
# import psutil
import multiprocessing
import subprocess
from time import sleep
import threading
from threading import Thread
import sys
import os
import runpy
from datetime import datetime
# import keyboard
from flask import Flask
from flask import jsonify
import json
import time
# import keyboard
import random
import socket
import netifaces
from flask import Flask
from subprocess import PIPE, Popen
from subprocess import run
import requests



proclist = []
running = False


def start_server():
    proc = subprocess.Popen(['python3', 'server.py'])
    proclist.append(proc)
    
    # for script in ('edDummy.py', 'server.py'):
    #     # for script in (ED_entry.get()):
    #     proc = subprocess.Popen(['python3', script])
    #     proclist.append(proc)
    
    


def start_game():
    game_path = Game_entry.get()
    for file in os.listdir(game_path):
        if file.endswith(".app"):
            filename = os.path.join(game_path, file)
            proc = subprocess.Popen(['open', '-a', filename])
            proclist.append(proc)
        
        

def upload_game_logs(server_url, file_path, user_id):
    time.sleep(5)  # Wait for 5 seconds before starting the loop

    while running:
        with open(file_path, 'r') as file:
            log_data = json.load(file)

        for log in log_data['logs']:
            time_date = log['time']
            game = {
                    'scene': log['scene'],
                    'asset': log['asset'],
                    'events': log['events'],
                    'task': log['task']
                }

            payload = {
                    'userID': user_id,
                    'timeDate': time_date,
                    'game': game
                }

            response = requests.post(f'{server_url}/api/setGame', json=payload)

            if response.status_code == 200:
                result = response.json()
                if not result['status']:
                    print(f"Log already exists and updated: {result['msg']}")
                else:
                    print(f"Log uploaded successfully: {result['msg']}")
            else:
                print("Error occurred while uploading the log.")
                print(f"Status code: {response.status_code}")
                print(f"Response content: {response.text}")

        time.sleep(1)  # Adjust the interval between uploads if needed



#start ed dummy, to be deleted after 
def start_ed():
    proc = subprocess.Popen(['python3', 'edDummy.py'])
    proclist.append(proc)





def start():
    global running
    proclist.clear()
    start_server()
    start_game()

    game_path = Game_entry.get()
    file_game_log = None
    for file in os.listdir(game_path):
        if file.endswith(".json"):
            file_game_log = os.path.join(game_path, file)
            break

    if file_game_log:
        server_url = 'http://127.0.0.1:5000'  # Update with your server URL
        user_id = user_entry.get()

        running = True
        upload_thread = threading.Thread(target=upload_game_logs, args=(server_url, file_game_log, user_id))
        upload_thread.start()



def locHostIP():
    iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
    a = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
    # b = request.environ['REMOTE_PORT']
    b = "5000"
    c = str(a)+":"+b
    Ip_Address.insert(END, a)
    linkIPAccess.insert(END, c)




def locHostIP():
    iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
    a = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
    # b = request.environ['REMOTE_PORT']
    b = "5000"
    c = str(a)+":"+b+"/api/setED/<player_name>"
    Ip_Address.insert(END, a)
    linkIPAccess.insert(END, c)
    
    
    
    
def localHostLink():
    b= requests.environ['REMOTE_PORT']
    linkIPAccess.insert(END, b)



def stop():
    global running
    running = False

    for proc in proclist:
        if proc and proc.poll() is None:
            proc.kill()
    proclist.clear()
    main_window.destroy()

def open_filepathGame():
    filepath = filedialog.askdirectory()
    Game_entry.insert(END, filepath)
    


main_window = Tk()
main_window.title("GVT")

Label(main_window, text="Running on").grid(row=1, column=1)
Label(main_window, text="ED End Point").grid(row=2, column=1)
Label(main_window, text="Player Name").grid(row=3, column=1)
Label(main_window, text="Game Folder").grid(row=4, column=1)
Label(main_window, text="").grid(row=5, column=1)


# Endpoint_entry = Entry(main_window, width=50, borderwidth=5)
# Endpoint_entry.grid(row=1, column=2)
# Endpoint_entry.insert(0, "http://127.0.0.1:5000/")
# ED_entry = Entry(main_window, width=50, borderwidth=5)
# ED_entry.grid(row=2, column=2)
# ED_entry.insert(0, "http://127.0.0.1:5000/api/setED/<player_name>")


linkIPAccess = Entry(main_window, width=50, borderwidth=5)
linkIPAccess.grid(row=2, column=2)
Ip_Address = Entry(main_window, width=50, borderwidth=5)
Ip_Address.grid(row=1, column=2)
user_entry = Entry(main_window, width=50, borderwidth=5)
user_entry.grid(row=3, column=2)
Game_entry = Entry(main_window, width=50, borderwidth=5)
Game_entry.grid(row=4, column=2)




openGame = Button(main_window, text="Open", command=open_filepathGame)
openGame.grid(row=4, column=3)

IpAddress = Button(main_window, text="Get", command=locHostIP).grid(row=1, column=3)
Button(main_window, text="Reset", command=lambda: [user_entry.delete(0, END), Game_entry.delete(0, END)]).grid(row=6, column=3)
Button(main_window, text="Start", command=start).grid(row=6, column=2)
Button(main_window, text="Stop", command=stop).grid(row=7, column=3)

main_window.mainloop()



