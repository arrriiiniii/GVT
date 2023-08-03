from db import DataBase
import time
from flask import Flask, render_template, make_response
from flask import jsonify, request
import json
import random
import netifaces
from flask import Flask, request
import datetime
from datetime import timedelta
import csv
from datetime import datetime
from flask import make_response
from flask import send_file
import os
import collections
from collections import OrderedDict
import statistics

# import bluetooth
# import math


DB = DataBase()








app = Flask(__name__)



# ====================================== main route ====================================

@app.route('/api/getVT', methods=['GET'])
def vt():
    # data = request.get_json()
    user = request.args.get('user')
    date = request.args.get('date')
    return jsonify(DB.getVT(user, date))



@app.route('/api/setED/<user>', methods=['POST'])
def setED(user):
    # print ("WOWOWWWWWW")
    data = request.get_json()
    print(data)
    time_date = data.get('date_time')
    stress_level = data.get('current_stress_level')

    if time_date:
        # Convert the time string to a datetime object
        time_date = datetime.strptime(time_date, '%Y-%m-%d %H:%M:%S.%f')
        # Remove milliseconds from the datetime object
        time_date = time_date.replace(microsecond=0)
        # Convert the datetime object back to a string
        time_date = datetime.strftime(time_date, '%Y-%m-%d %H:%M:%S')
    

    print (time_date, stress_level)
    # return jsonify(DB.setED(time_date, stress_level))
    return jsonify(DB.setED(user, time_date, stress_level))
    # return ""





@app.route('/api/setGame', methods=['POST'])
def setGame():
    data = request.get_json()
    user_id = data.get('userID')
    time_date = data.get('timeDate')
    game = data.get('game')
    # game = json.dumps(game)
    # Perform any necessary operations with the user ID, timeDate, and stressLv
    return jsonify(DB.setGame(user_id,time_date,game))





# ================================= additional single analysis ============================================


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part in the request', 400

    file = request.files['file']

    if file.filename == '':
        return 'No selected file', 400
    return 'File uploaded successfully', 200





@app.route('/get_player_names_date')
def get_player_names_date():
    results = DB.getUserAndDate()
    player_dict = {}
    
    for result in results:
        user = result['user']
        date = str(result['date'])
        
        if user not in player_dict:
            player_dict[user] = [date]
        elif date not in player_dict[user]:
            player_dict[user].append(date)
    
    players = [{'name': user, 'dates': dates} for user, dates in player_dict.items()]
    return jsonify(players)



@app.route('/get_dates_by_user')
def get_dates_by_user():
    user = request.args.get('user')
    dates = DB.getDatesByUser(user)
    return jsonify(dates)





# =================================== calculation for single analysis ==========================================


@app.route('/saveRawVt', methods=['POST'])
def save_raw_vt():
    rawData = request.get_json()
    with open('rawVT.json', 'w') as json_file:
        json.dump(rawData, json_file, indent=4)
    return rawData





@app.route('/mergeTimeVt')
def mergeTimeVt():
    with open("rawVT.json", "r") as f:
        vtDataTime = json.load(f)

    # Perform additional time-related operations
    time_accumulation = timedelta(0)
    for i in range(len(vtDataTime)):
        time_spent = timedelta(0)
        if i < len(vtDataTime) - 1:
            time_spent = datetime.fromisoformat(vtDataTime[i+1]["time"]) - datetime.fromisoformat(vtDataTime[i]["time"])
        else:
            time_spent = timedelta(0)
        time_accumulation += time_spent
        time_spent_datetime = datetime(1, 1, 1) + time_spent
        time_accumulation_datetime = datetime(1, 1, 1) + (time_accumulation - time_spent)
        vtDataTime[i]["time_spent"] = time_spent_datetime.strftime("%H:%M:%S")
        vtDataTime[i]["time_accumulation"] = time_accumulation_datetime.strftime("%H:%M:%S")

    with open("vtTime.json", "w") as f:
        json.dump(vtDataTime, f, indent=4)

    return jsonify(vtDataTime)
   



@app.route('/finalVT')
def analyzePerScene():
    with open("vtTime.json", "r") as f:
        vtDataFinal = json.load(f)
    
    scenes = []
    for activity in vtDataFinal:
        scene = activity["scene"]
        scene_found = next((s for s in scenes if s["scene"] == scene), None)
        if scene_found is None:
            scene_data = {
                "scene": scene,
                "total_time_in_scene": timedelta(0),
                "activities": [],
                "avg_stress": 0
            }
            scenes.append(scene_data)
        else:
            scene_data = scene_found
        scene_data["activities"].append(activity)
        scene_data["total_time_in_scene"] += timedelta(
            hours=int(activity["time_spent"].split(":")[0]),
            minutes=int(activity["time_spent"].split(":")[1]),
            seconds=int(activity["time_spent"].split(":")[2])
        )
        scene_data["avg_stress"] += int(activity["stress_level"]) * int(activity["time_spent"].split(":")[2])
    
    for scene in scenes:
        total_time = scene["total_time_in_scene"]
        hours = total_time.seconds // 3600
        minutes = (total_time.seconds % 3600) // 60
        seconds = total_time.seconds % 60
        scene["total_time_in_scene"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        avg_stress = scene["avg_stress"] / total_time.seconds if total_time.seconds > 0 else 0
        scene["avg_stress"] = int(avg_stress)
        # Additional functions to calculate statistics
        stress_levels = [activity["stress_level"] for activity in scene["activities"]]
        scene["min_stress"] = min(stress_levels)
        scene["max_stress"] = max(stress_levels)
        scene["mode_stress"] = statistics.mode(stress_levels) if stress_levels else None
        scene["quartile_stress"] = statistics.quantiles(stress_levels, n=4) if stress_levels else None
        scene["std_stress"] = statistics.stdev(stress_levels) if len(stress_levels) >= 2 else None
    
    with open("finalVT.json", "w") as f:
        json.dump(scenes, f, indent=4)
        
    with open("finalVT.json", "r") as c:
        vtDataFinal = json.load(c)
    
    return jsonify(vtDataFinal)






# ========================================== multi analysis ======================================================


@app.route('/get_multi_vt', methods=['GET'])
def get_multi_vt():
    selected_combinations = request.args.get('selected_combinations')
    selected_combinations = json.loads(selected_combinations)

    multi_raw_vt = {}  # Dictionary to store the merged VT data

    for combination in selected_combinations:
        user = combination['user']
        date = combination['date']
        vt_data = DB.getVT(user, date)

        # Add the VT data to the multi_raw_vt dictionary
        key = f"{user}/{date}"
        multi_raw_vt[key] = vt_data

    # Save the merged VT data to MultiRawVT.json file
    with open('MultiRawVT.json', 'w') as json_file:
        json.dump(multi_raw_vt, json_file, indent=4)

    return jsonify(multi_raw_vt)



@app.route('/merge_multi_time_vt')
def merge_multi_time_vt():
    with open("MultiRawVT.json", "r") as f:
        multi_raw_vt = json.load(f)

    multi_vt_time = {}  # Dictionary to store the merged VT data with time-related information

    for combination, vt_data in multi_raw_vt.items():
        vt_data_time = vt_data.copy()
        time_accumulation = timedelta(0)

        for i in range(len(vt_data)):
            time_spent = timedelta(0)

            if i < len(vt_data) - 1:
                time_spent = datetime.fromisoformat(vt_data[i+1]["time"]) - datetime.fromisoformat(vt_data[i]["time"])
            else:
                time_spent = timedelta(0)

            time_accumulation += time_spent
            time_spent_datetime = datetime(1, 1, 1) + time_spent
            time_accumulation_datetime = datetime(1, 1, 1) + (time_accumulation - time_spent)
            vt_data_time[i]["time_spent"] = time_spent_datetime.strftime("%H:%M:%S")
            vt_data_time[i]["time_accumulation"] = time_accumulation_datetime.strftime("%H:%M:%S")

        multi_vt_time[combination] = vt_data_time

    # Save the merged VT data with time-related information to MultiVtTime.json file
    with open("MultiVtTime.json", "w") as f:
        json.dump(multi_vt_time, f, indent=4)

    return jsonify(multi_vt_time)




@app.route('/analyze_multi_per_scene')
def analyze_multi_per_scene():
    with open("MultiVtTime.json", "r") as f:
        multi_vt_time = json.load(f)

    multi_final_vt = []  # List to store the final VT data with scene-based analysis

    for combination, vt_data_time in multi_vt_time.items():
        scenes = []
        for activity in vt_data_time:
            scene = activity["scene"]
            scene_found = next((s for s in scenes if s["scene"] == scene), None)
            if scene_found is None:
                scene_data = {
                    "scene": scene,
                    "total_time_in_scene": timedelta(0),
                    "activities": [],
                    "avg_stress": 0
                }
                scenes.append(scene_data)
            else:
                scene_data = scene_found
            scene_data["activities"].append(activity)
            scene_data["total_time_in_scene"] += timedelta(
                hours=int(activity["time_spent"].split(":")[0]),
                minutes=int(activity["time_spent"].split(":")[1]),
                seconds=int(activity["time_spent"].split(":")[2])
            )
            scene_data["avg_stress"] += int(activity["stress_level"]) * int(activity["time_spent"].split(":")[2])

        for scene in scenes:
            total_time = scene["total_time_in_scene"]
            hours = total_time.seconds // 3600
            minutes = (total_time.seconds % 3600) // 60
            seconds = total_time.seconds % 60
            scene["total_time_in_scene"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            avg_stress = scene["avg_stress"] / total_time.seconds if total_time.seconds > 0 else 0
            scene["avg_stress"] = int(avg_stress)

        multi_final_vt.append({combination: scenes})

    # Save the final VT data with scene-based analysis to MultiFinalVT.json file
    with open("MultiFinalVT.json", "w") as f:
        json.dump(multi_final_vt, f, indent=4)

    return jsonify(multi_final_vt)



@app.route('/extract_main_multi_analysis')
def extract_main_multi_analysis():
    with open("MultiFinalVT.json", "r") as f:
        multi_final_vt = json.load(f)

    main_multi_analysis = []  # List to store the extracted data

    for combination_data in multi_final_vt:
        for combination, scenes in combination_data.items():
            extracted_data = {
                "user": combination.split("/")[0],
                "date": combination.split("/")[1],
                "scenes": []
            }
            for scene in scenes:
                extracted_scene = {
                    "scene": scene["scene"],
                    "total_time_in_scene": scene["total_time_in_scene"],
                    "avg_stress": scene["avg_stress"]
                }
                extracted_data["scenes"].append(extracted_scene)

            main_multi_analysis.append(extracted_data)

    # Save the extracted data to MainMultiAnalysis.json file
    with open("MainMultiAnalysis.json", "w") as f:
        json.dump(main_multi_analysis, f, indent=4)

    return jsonify(main_multi_analysis)




@app.route('/getMainMultiAnalysis')
def getMainMultiAnalysis():
    with open("MainMultiAnalysis.json", "r") as c:
        MainMultiAnalysis = json.load(c)

    return jsonify(MainMultiAnalysis)




# @app.route('/generate_assessment_result')
# def generate_assessment_result():
#     with open("MainMultiAnalysis.json", "r") as f:
#         main_multi_analysis = json.load(f)

#     # Group the scenes together
#     scene_groups = {}
#     overall_total_time = timedelta(0)
#     overall_stress_level_time = timedelta(0)

#     for data in main_multi_analysis:
#         scenes = data["scenes"]
#         for scene in scenes:
#             scene_name = scene["scene"]
#             if scene_name not in scene_groups:
#                 scene_groups[scene_name] = {
#                     "scene": scene_name,
#                     "avg_total_time": timedelta(0),
#                     "avg_stress_level": 0,
#                     "total_users": 0
#                 }
#             scene_group = scene_groups[scene_name]
#             total_time = datetime.strptime(scene["total_time_in_scene"], "%H:%M:%S").time()
#             total_time_seconds = timedelta(hours=total_time.hour, minutes=total_time.minute, seconds=total_time.second)
#             scene_group["avg_total_time"] += total_time_seconds
#             scene_group["avg_stress_level"] += scene["avg_stress"]
#             scene_group["total_users"] += 1

#             overall_total_time += total_time_seconds 
#             overall_stress_level_time += total_time_seconds * scene["avg_stress"]

#     # Calculate the average total time and stress level for each scene
#     assessment_result = []
#     for scene_name, scene_group in sorted(scene_groups.items(), key=lambda x: x[0]):
#         avg_total_time = scene_group["avg_total_time"] / scene_group["total_users"]
#         avg_total_time_seconds = avg_total_time.total_seconds()
#         avg_total_time_hours = int(avg_total_time_seconds // 3600)
#         avg_total_time_minutes = int((avg_total_time_seconds % 3600) // 60)
#         avg_total_time_seconds = int(avg_total_time_seconds % 60)

#         avg_total_time_str = f"{avg_total_time_hours:02d}:{avg_total_time_minutes:02d}:{avg_total_time_seconds:02d}"
#         avg_stress_level = round(scene_group["avg_stress_level"] / scene_group["total_users"], 1)

#         assessment_data = {
#             "scene": scene_name,
#             "avg_total_time": avg_total_time_str,
#             "avg_stress_level": avg_stress_level,
#             "total_users": scene_group["total_users"]
#         }
#         assessment_result.append(assessment_data)

#     # Calculate the overall stress level and overall time spent in the game
#     overall_time_seconds = sum(datetime.strptime(data["avg_total_time"], "%H:%M:%S").time().second for data in assessment_result)
#     overall_time_hours = int(overall_time_seconds // 3600)
#     overall_time_minutes = int((overall_time_seconds % 3600) // 60)
#     overall_time_seconds = int(overall_time_seconds % 60)
#     overall_time_str = f"{overall_time_hours:02d}:{overall_time_minutes:02d}:{overall_time_seconds:02d}"

#     # Create the final JSON structure
#     final_result = {
#         "overall_stress": round(overall_stress_level_time.total_seconds() / overall_total_time.total_seconds(), 1),
#         "overall_time": overall_time_str,
#         "details": assessment_result
#     }

#     # Save the assessment result to AssessmentResult.json file
#     with open("AssessmentResult.json", "w") as f:
#         json.dump(final_result, f, indent=4)

#     with open("AssessmentResult.json", "r") as c:
#         assessment_result = json.load(c)

#     return jsonify(assessment_result)








@app.route('/generate_assessment_result')
def generate_assessment_result():
    with open("MainMultiAnalysis.json", "r") as f:
        main_multi_analysis = json.load(f)

    # Group the scenes together
    scene_groups = {}
    overall_total_time = timedelta(0)
    overall_stress_level_time = timedelta(0)

    for data in main_multi_analysis:
        scenes = data["scenes"]
        for scene in scenes:
            scene_name = scene["scene"]
            if scene_name not in scene_groups:
                scene_groups[scene_name] = {
                    "scene": scene_name,
                    "avg_total_time": timedelta(0),
                    "avg_stress_level": 0,
                    "total_users": 0
                }
            scene_group = scene_groups[scene_name]
            total_time = datetime.strptime(scene["total_time_in_scene"], "%H:%M:%S").time()
            total_time_seconds = timedelta(hours=total_time.hour, minutes=total_time.minute, seconds=total_time.second)
            scene_group["avg_total_time"] += total_time_seconds
            scene_group["avg_stress_level"] += scene["avg_stress"]
            scene_group["total_users"] += 1

            overall_total_time += total_time_seconds 
            overall_stress_level_time += total_time_seconds * scene["avg_stress"]

    # Calculate the average total time and stress level for each scene
    assessment_result = []
    for scene_name, scene_group in sorted(scene_groups.items(), key=lambda x: x[0]):
        avg_total_time = scene_group["avg_total_time"] / scene_group["total_users"]
        avg_total_time_seconds = avg_total_time.total_seconds()
        avg_total_time_hours = int(avg_total_time_seconds // 3600)
        avg_total_time_minutes = int((avg_total_time_seconds % 3600) // 60)
        avg_total_time_seconds = int(avg_total_time_seconds % 60)

        avg_total_time_str = f"{avg_total_time_hours:02d}:{avg_total_time_minutes:02d}:{avg_total_time_seconds:02d}"
        avg_stress_level = round(scene_group["avg_stress_level"] / scene_group["total_users"], 1)

        assessment_data = {
            "scene": scene_name,
            "avg_total_time": avg_total_time_str,
            "avg_stress_level": avg_stress_level,
            "total_users": scene_group["total_users"]
        }
        assessment_result.append(assessment_data)

    # Calculate the overall stress level and overall time spent in the game
    overall_time_seconds = sum(datetime.strptime(data["avg_total_time"], "%H:%M:%S").time().second for data in assessment_result)
    overall_time_hours = int(overall_time_seconds // 3600)
    overall_time_minutes = int((overall_time_seconds % 3600) // 60)
    overall_time_seconds = int(overall_time_seconds % 60)
    overall_time_str = f"{overall_time_hours:02d}:{overall_time_minutes:02d}:{overall_time_seconds:02d}"

    # Create the final JSON structure
    final_result = {
        "overall_stress": round(overall_stress_level_time.total_seconds() / overall_total_time.total_seconds(), 1),
        "overall_time": overall_time_str,
        "details": assessment_result
    }

    # Save the assessment result to AssessmentResult.json file
    with open("AssessmentResult.json", "w") as f:
        json.dump(final_result, f, indent=4)

    with open("AssessmentResult.json", "r") as c:
        assessment_result = json.load(c)

    return jsonify(assessment_result)




































# =========================================== main route page ====================================================




@app.route("/")
def home():
    return render_template('home.html')



@app.route('/singleAnalysis')
def singleAnalysis():
    return render_template('index.html')



@app.route('/multiAnalysis')
def multiAnalysis():
    return render_template('multiAnalysis.html')

@app.route("/about")
def about():
    return render_template('about.html')



@app.route("/trial")
def trial():
    return render_template('trial.html')



if __name__ == '__main__':
    # app.run()
    app.run(host='0.0.0.0')
    




























