import pymysql
import json

class DataBase:
    def connect(self):
        return pymysql.connect(host="127.0.0.1", user="root", database="DBGame", charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)

    
    
    def getVT(self, user_id, time_date):
        connect = self.connect()
        cursor = connect.cursor()
        query = "SELECT * FROM vt WHERE user = %s AND DATE(time) = %s ORDER BY time ASC"
        cursor.execute(query, (user_id, time_date))
        result = cursor.fetchall()
        output = []
        
        previous_stress_level = None
        
        if len(result) > 0:
            for i in result:
                game_logs = json.loads(i["game_logs"])
                
                if len(game_logs) > 0:
                    for j in game_logs:
                        stress_level = i["stress_lv"]
                        
                        if stress_level is None:
                            stress_level = previous_stress_level
                        
                        tmp = {
                            "time": str(i["time"]),
                            "stress_level": stress_level,
                        }
                        tmp.update(j)
                        output.append(tmp)
                        
                        previous_stress_level = stress_level

        return output


    
    
     
        
    # initial code
    def setED(self, user_id, time_date, stress_level):
        connect = self.connect()
        cursor = connect.cursor()
        query = "SELECT * FROM vt WHERE user = %s AND time = %s"
        cursor.execute(query, (user_id, time_date))
        result = cursor.fetchall()

        if len(result) == 0:
            # No existing record, create a new one with stress_level
            insert_query = "INSERT INTO vt (user, time, stress_lv) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (user_id, time_date, stress_level))
            connect.commit()
            return {"status": True, "msg": "New data created"}
        else:
            # Existing record found, update stress_level
            update_query = "UPDATE vt SET stress_lv = %s WHERE user = %s AND time = %s"
            cursor.execute(update_query, (stress_level, user_id, time_date))
            connect.commit()
            return {"status": True, "msg": "Data updated"}
        
    
    
    
    def setGame(self, user_id, time_date, game):
        connect = self.connect()
        cursor = connect.cursor()
        query = "SELECT * FROM vt WHERE user = %s AND time = %s"
        cursor.execute(query, (user_id, time_date))
        result = cursor.fetchone()

        if result:
            oldGame = json.loads(result["game_logs"])
            if game in oldGame:
                connect.close()  # Close the database connection
                return {"status": False, "msg": "Log already exists"}  # Indicate that the log already exists

            oldGame.append(game)
            game = json.dumps(oldGame)
            update_query = "UPDATE vt SET game_logs = %s WHERE id = %s"
            cursor.execute(update_query, (game, result["id"]))
            connect.commit()
            connect.close()  # Close the database connection
            return {"status": True, "msg": "Data updated"}

        else:
            game = json.dumps([game])
            insert_query = "INSERT INTO vt (user, time, game_logs) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (user_id, time_date, game))
            connect.commit()
            connect.close()  # Close the database connection
            return {"status": True, "msg": "New data created"}

    
    
    
    
    def getUserAndDate(self):
        connect = self.connect()
        cursor = connect.cursor()
        query = "SELECT DISTINCT user, DATE(time) as date FROM vt"
        cursor.execute(query)
        result = cursor.fetchall()
        connect.close()  # Close the database connection
        
        return result
    
    
    
    def getDatesByUser(self, user):
        connect = self.connect()
        cursor = connect.cursor()
        query = "SELECT DISTINCT DATE(time) as date FROM vt WHERE user = %s"
        cursor.execute(query, (user,))
        result = cursor.fetchall()
        connect.close()  # Close the database connection

        dates = [str(res['date']) for res in result]
        return dates
    
    
    
    

    
    