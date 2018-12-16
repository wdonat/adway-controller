# Testing requests library functionality

import requests
import json

api_key = "21E4E81DF8E9103AAA181228C7B3D111"
login_url = "https://api.adwayusa.com/user/login"
logout_url = "https://api.adwayusa.com/logout"
content_url = "https://api.adwayusa.com/get/content"
init_url = "https://api.adwayusa.com/init/device"
user = "wolframdonat@gmail.com"
password = "5mudg301"
location = (34.103, -118.326)
device_id = '11E7436CB16BC8A6901B0638FE7E49F8'
device_sess_token = ''

headers = {"Content-Type": "application/json", "cache-control": "no-cache"}
#payload = '{"user": "wolframdonat@gmail.com", "API_KEY": "21E4E81DF8E9103AAA181228C7B3D111", "data":{"secret": "5mudg301", "lat": 121.12, "lon": 321.12}}'
payload = '{"user": "' + user + '", "API_KEY": "' + api_key + '", "data": {"secret": "' + password + \
              '", "lat": ' + str(location[0]) + ', "lon": ' + str(location[1]) + '}}'

#payload = '{"user": "' + user + '", "API_KEY": "' + api_key + '", "code": "' + token + '"}}'
#payload = '{"user": "wolframdonat@gmail.com", "code": "11E8F05A4A1F6161BB700699960A031A", "API_KEY": "21E4E81DF8E9103AAA181228C7B3D111"}'
response = requests.request("POST", login_url, data=payload, headers=headers)
x = json.loads(response.text)
token = x['data'][0]['token']
print response.text


# Initialize device
payload = '{"API_KEY": "' + api_key + '", "data": {"device_id": "' + device_id + '", "lat": ' + str(location[0]) + ', "lon": ' + str(location[1]) + '} }'
# payload = '{"API_KEY": "' + api_key + '", "data": {"device_id": "87E4E81DF8E9103AAA181228C7B3DFA3", "lat": 121.12, "lon": 321.12} }'
response = requests.request("POST", init_url, data=payload, headers=headers)
x = json.loads(response.text)
device_sess_token = x['data'][0]['token']
print response.text


# Load content
payload = '{"user": "' + user + '", "code": "' + token + '", "API_KEY": "' + api_key + '", "data": {"lat": ' + str(location[0]) + ', \
"lon": ' + str(location[1]) + ', "cur_campaign": 2342, "device_id": "' + device_id + '", "projector_left": 325, "projector_right": 326, \
"stats": [ {"time": "2017-02-21 13:32:21", "lat": 231, "lon": -23.22, "start_lat": 231, "start_lon": -23.22, "stop_lat":231, \
"stop_lon": -23.22, "campaign_id": 1, "duration": 10, "speed": 17, "RT_impressions": 4}, {"time": "2017-02-21 13:32:32", "lat": 231, "lon": -23.2201, \
"start_lat": 231, "start_lon": -23.22, "stop_lat": 231, "stop_lon": -23.22, "campaign_id": 2, "duration": 15, "speed": 45, "RT_impressions": 5}, \
{"time": "2017-02-21 13:32:47", "lat": 231, "lon": -23.2203, "start_lat": 231, "start_lon": -23.22, "stop_lat": 231, \
"stop_lon": -23.22, "campaign_id":1, "duration": 10, "speed": 43, "RT_impressions": 4} ] } }'
 
response = requests.request("POST", content_url, data=payload, headers=headers)
print response.text

# Logout
payload = '{"user": "' + user + '", "API_KEY": "' + api_key + '", "code": "' + token + '"}'

response = requests.request("POST", logout_url, data=payload, headers=headers)
print response.text


