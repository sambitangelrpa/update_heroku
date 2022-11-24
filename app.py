
import json
from flask import Flask,jsonify
from flask.wrappers import Response
from flask.globals import request, session
import requests
from dotenv import load_dotenv
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
import google
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import os, pathlib
from functools import wraps
from connect_db import connect_db, insert_into_UserDeatils_db,insert_into_IP_Details_db,update_into_IP_Details_db,find_ip_details
import jwt
from flask_cors import CORS
from all_scraping_data import main_output
from config_reader import ConfigReader



config_reader = ConfigReader()
configuration = config_reader.read_config()
app = Flask(__name__)

CORS(app)
app.config['Access-Control-Allow-Origin'] = '*'
app.config["Access-Control-Allow-Headers"]="Content-Type"

# bypass http
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
app.secret_key = configuration['SECRET_KEY']
GOOGLE_CLIENT_ID = configuration["GOOGLE_CLIENT_ID"]
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client-secret.json")
algorithm = configuration["ALGORITHM"]
BACKEND_URL=configuration["BACKEND_URL"]
FRONTEND_URL=configuration["FRONTEND_URL"]
print('BACKEND_URL',BACKEND_URL)
#database connection
connect_db()

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
    redirect_uri=BACKEND_URL+"/callback",
)


# wrapper
def login_required(function):
    def wrapper(*args, **kwargs):
        
        encoded_jwt=request.headers.get("Authorization").split("Bearer ")[1]
        if encoded_jwt==None:
            return abort(401)
        else:
            return function()
    wrapper.__name__ = function.__name__
    return wrapper

def Generate_JWT(payload):
    encoded_jwt = jwt.encode(payload, app.secret_key,algorithm=algorithm)
    return encoded_jwt


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    request_session = requests.session()
    token_request = google.auth.transport.requests.Request(session=request_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token, request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    session["google_id"] = id_info.get("sub")
    
    # removing the specific audience, as it is throwing error
    del id_info['aud']
    print(id_info)
    jwt_token=Generate_JWT(id_info)
    insert_into_UserDeatils_db(
        id_info.get('name'),
        id_info.get('email'),
        id_info.get('picture')
    )
    return redirect(f"{FRONTEND_URL}?jwt={jwt_token}")
    # return Response(
    #     response=json.dumps({'JWT':jwt_token}),
    #     status=200,
    #     mimetype='application/json'
    # ) 


@app.route("/auth/google")
def login():
    authorization_url, state = flow.authorization_url()
    # Store the state so the callback can verify the auth server response.
    session["state"] = state
    return Response(
        response=json.dumps({'auth_url':authorization_url}),
        status=200,
        mimetype='application/json'
    )



@app.route("/")
@login_required

def home_page_user():
    # print('i am in home')
    # print(request.headers.get("Authorization").split("Bearer ")[1])
    encoded_jwt=request.headers.get("Authorization").split("Bearer ")[1]
    try:
        decoded_jwt=jwt.decode(encoded_jwt, app.secret_key,algorithms=algorithm)
        print(decoded_jwt)
    except Exception as e: 
        return Response(
            response=json.dumps({"message":"Decoding JWT Failed", "exception":e.args}),
            status=500,
            mimetype='application/json'
        )
    return Response(
        response=json.dumps(decoded_jwt),
        status=200,
        mimetype='application/json'
    )

@app.route("/api/getResult_outside",methods=['POST'])
def ip_count():
    #clear the local storage from frontend
    # data={
    # "country_code": "IN",
    # "country_name": "India",
    # "city": None,
    # "postal": "799001",
    # "latitude": 23.8364,
    # "longitude": 91.275,
    # "IPv4": "157.40.185.547",
    # "state": "Tripura",
    # "search_count": 0,
    # "login": 0
    # }


    # print("get result", request.get_json())
    payloadData = request.get_json()
    keyword = payloadData["keyword"]
    country = payloadData["country"]
    region =payloadData["region"]
    data = payloadData["data"]
    location = region+","+country

    print(payloadData["data"])

    # keyword="iphone"
    # region="california,united states"
    insert_into_IP_Details_db(
        data["country_code"],
        data["country_name"],
        data["city"],
        data["postal"],
        data["latitude"],
        data["longitude"],
        data["IPv4"],
        data["state"],
        data["search_count"],
        data["login"]
         )

    print("request ip" ,data["IPv4"])    

    jwt_token=Generate_JWT(data)
    
    result=main_output(keyword,location)
    


    update_into_IP_Details_db(data['IPv4'])

    return Response(
        response=json.dumps({"result":result,"token":jwt_token}),
        status=202,
        mimetype='application/json'
    )

@app.route("/api/find_ip_count",methods=['POST'])
def find_ip_count():
    #clear the local storage from frontend

   
    # print("get login ", request.get_json())
    data=request.get_json()

    ip_data=find_ip_details(data['IPv4'])
    print('ip data:',ip_data)
    return Response(
        response=json.dumps({'result':ip_data}),
        status=202,
        mimetype='application/json'
    )





@app.route("/api/getResult",methods=['POST'])
@login_required

def result_data():
    
    
    payloadData = request.get_json()
    keyword = payloadData["keyword"]
    country = payloadData["country"]
    region =payloadData["region"]
    location = region+","+country

    print(payloadData)

    result=main_output(keyword,location)
            
    return Response(
        response=json.dumps({"result":result}),
        status=200,
        mimetype='application/json'
    )


if __name__ == "__main__":

    app.run(debug=True, port=5000, host="127.0.0.1")   
    


