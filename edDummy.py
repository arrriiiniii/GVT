import json
import time
import random
import datetime
import requests

status = True

data = []

while status:
    gsr = random.randint(0, 300)
    current_stress_level = random.randint(1, 5)
    date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    ed_data = {
        'gsr': gsr,
        'current_stress_level': current_stress_level,
        'date_time': date_time
    }

    data.append(ed_data)
    print(ed_data)

    # Send the data to the server
    url = 'http://127.0.0.1:5000/api/setED/arininrohmah'
    response = requests.post(url, json=ed_data)

    if response.status_code == 200:
        print('Data sent successfully')
    else:
        print('Failed to send data')

    time.sleep(1)
