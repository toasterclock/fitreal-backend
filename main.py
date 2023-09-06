from flask import Flask, request
import firebase_admin
from firebase_admin import credentials, db, storage
from dotenv import load_dotenv
load_dotenv()
import json, os




cred = credentials.Certificate("fitreal-41736-firebase-adminsdk-cdzmk-d8be63ed0b.json")
default_app = firebase_admin.initialize_app(cred, {
	'databaseURL':"https://fitreal-41736-default-rtdb.asia-southeast1.firebasedatabase.app/"
	})
ref = db.reference("/")
app = Flask(__name__)

bucket = storage.bucket("fitreal-41736.appspot.com")

def checkAPIKey(request):
    if "APIKey" not in request.json:
        return False
    if request.json["APIKey"] != os.environ["APIKey"]:
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
        data.pop("APIKey")
        # add to local_db.json
        with open('local_db.json') as json_file:
            local_db = json.load(json_file)
        local_db["users"].append(data)
        with open('local_db.json', 'w') as outfile:
            json.dump(local_db, outfile)
        # replace firebase db
        ref.set(local_db)
        return "Done"


@app.route('/upload_image', methods=['POST'])
def post_image():
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
    
    return blob.public_url


@app.route('/create_user', methods=['POST'])
def create_user():
    if not checkAPIKey(request):
        return "Denied, Invalid API Key"
    else:
    # Push the data to Firebase
        data = request.json
        data.pop("APIKey")
        # add to local_db.json
        with open('local_db.json') as json_file:
            local_db = json.load(json_file)
        local_db.update(data)
        with open('local_db.json', 'w') as outfile:
            json.dump(local_db, outfile)
        # replace firebase db
        ref.set(local_db)
        return "Done"
    



if __name__ == '__main__':
    app.run(debug=True)