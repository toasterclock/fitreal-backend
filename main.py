from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db, storage
from dotenv import load_dotenv
load_dotenv()
import json, os
import copy



cred = credentials.Certificate("../fitreal-41736-firebase-adminsdk-cdzmk-d8be63ed0b.json")
default_app = firebase_admin.initialize_app(cred, {
	'databaseURL':"https://fitreal-41736-default-rtdb.asia-southeast1.firebasedatabase.app/"
	})
ref = db.reference("/")
app = Flask(__name__)

bucket = storage.bucket("fitreal-41736.appspot.com")


def checkAPIKey(request):
    if "APIKey" not in request.headers:
        return False
    if request.headers["APIKey"] != os.environ["APIKey"]:
        return False
    
    return True



@app.route('/')
def main():
    
    return 'Main Page Route'

@app.route('/upload_something', methods=['POST'])
def post_data():
    data = request.json  # Assuming the data is sent in JSON format
    if not checkAPIKey(request):
        return "Denied, Invalid API Key"
    else:
        # data.pop("APIKey")
        # add to local_db.json
        with open('local_db.json') as json_file:
            local_db = json.load(json_file)
        local_db["users"].append(data)
        with open('local_db.json', 'w') as outfile:
            json.dump(local_db, outfile)
        # replace firebase db
        ref.set(local_db)
        return "Done"

@app.route('/new_activity', methods=['POST'])
def new_activity():
    data = request.json

    print(data)

    # add to local_db.json
    with open('local_db.json') as json_file:
        local_db = json.load(json_file)
    
    


    # update local_db with new activity
    local_db[data["fireAuthID"]]["activities"] = data

    fireAuthID = local_db[data["fireAuthID"]]["fireAuthID"]
    local_db.pop(fireAuthID)


    # update local_db with new activity
    with open('local_db.json', 'w') as outfile:
        json.dump(local_db, outfile)
    
        # add to firebase
    ref.set(local_db)
    return "Done"

@app.route('/fetch_user', methods=['POST'])
def fetch_user():
    data = request.json
    
    with open('local_db.json') as json_file:
        local_db = json.load(json_file)
    # return user data
    
    if data["userID"] not in local_db:
        return "User not found"
    else:
        return jsonify(local_db[data["userID"]])




@app.route('/upload_image', methods=['POST'])
def post_image():
    user_id = request.form["userID"]
    activity_id = request.form["activityID"]
    api_key = request.headers.get('APIKey')
    print(api_key)
    if not api_key == os.environ["APIKey"]:
        return "Denied, Invalid API Key"

    if 'image' not in request.files:
        return "No image file provided"

    image = request.files['image']

    if image.filename == '':
        return "No selected file"

    # Check if the content type is supported (e.g., 'image/jpeg', 'image/png', etc.)
    allowed_content_types = ['image/jpeg', 'image/png', 'image/gif', 'image/jpg']
    if image.content_type not in allowed_content_types:
        return "Unsupported media type"

    # Push the data to Firebase Storage
    blob = bucket.blob(image.filename)
    blob.upload_from_string(image.read(), content_type=image.content_type)
    blob.make_public()
    
    # add to local_db.json
    with open('local_db.json') as json_file:
        local_db = json.load(json_file)
    # add the image url to the activity
    local_db[user_id]["activities"][activity_id]["imageURL"] = blob.public_url
    
    #ref.set(local_db)

    return blob.public_url

@app.route('/create_user', methods=['POST'])
def create_user():
    
    if not checkAPIKey(request):
        return "Denied, Invalid API Key"
    else:
    # Push the data to Firebase
        data = request.json
        # data.pop("APIKey")
        # add to local_db.json
        with open('local_db.json') as json_file:
            local_db = json.load(json_file)
        
        local_db[data["fireAuthID"]] = data
        with open('local_db.json', 'w') as outfile:
            json.dump(local_db, outfile)
        # replace firebase db
        ref.set(local_db)
        return "Done"
    
@app.route('/update_user', methods=['POST'])
def update_user():
    pass

@app.route('/update_feed', methods=['POST'])
def update_feed():
    #user requests to update feed with user id

    user_id = request.json["user_id"]
    
    #update user feed with friends list
    with open('local_db.json') as json_file:
        local_db = json.load(json_file)
    friends_list = local_db[user_id]["friends"]
    
    #retrieve friends' feed
    friends_feed = []
    for friend in friends_list:
        # get activities of friend
        friend_activities = list(local_db[friend]["activities"].keys())
        print(friend_activities)
        for activity in friend_activities:
            if local_db[friend]["activities"][activity]["missed"]:
                pass

            else:
                friends_feed.append({
                    "ownerID":friend,
                    "ownerName:":local_db[friend]["name"],
                    "imageURL":local_db[friend]["activities"][activity]["imageURL"],
                    "activityID":activity,
                    "activityType":local_db[friend]["activities"][activity]["type"],
                })
        # if activity missed, do not include in feed
        

    # we now have each key (acitvity), next check firebase storage for each image
    print(friends_feed)

    # return image url + activity data + return using the activityid

    return friends_feed


@app.route('/next_workout', methods=['POST'])
def next_workout():
    local_db = {}
    with open("local_db.json", "r") as f:
        local_db = json.load(f)

    # using ISO 8601 format
    if "userID" not in request.json:
        return "Please provide the userID."
    if "nextWorkoutDatetime" not in request.json:
        return "Please provide the datetime of the next workout."
   
    
    if request.json["userID"] in local_db:
        return "User not found."
    
    local_db[request.json["userID"]]["nextWorkout"] = request.json["nextWorkoutDatetime"]
    
    # update rtdb
    ref.set(local_db)

    return "Success"


# @app.route('/add_friend', methods=['POST'])
# def add_friend():
#     data = request.json
#     # check api key in header
#     if not checkAPIKey(request):
#         return "Denied, Invalid API Key"
#     else:
#         # add to local_db.json
#         with open('local_db.json') as json_file:
#             local_db = json.load(json_file)
#         local_db[data["userID"]]["friends"].append(data["friendID"])
#         with open('local_db.json', 'w') as outfile:
#             json.dump(local_db, outfile)
#         # replace firebase db
#         ref.set(local_db)
#         return "Done"

# @app.route('/pending_requests', methods=['POST'])
# def pending_requests():
#     data = request.json
#     # check api key in header
#     if not checkAPIKey(request):
#         return "Denied, Invalid API Key"
#     else:
#         # add to local_db.json
#         with open('local_db.json') as json_file:
#             local_db = json.load(json_file)
#         # return pending requests if there are any

#         return local_db[data["userID"]]["friendRequests"]
    


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)