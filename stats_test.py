url = 'http://www.example.com/get/content'
user = 'wolframdonat@gmail.com'
token = 'sdfdsf'
api_key = 'sdlkjfd'

latitude = '34.5555'
longitude = '118.2222'
time_string = '2019-01-01 13:33:33'
camp = 1
duration = 2
devices = 45
speed = 44.4
device_id = 4
cur_campaign = 2

stats = [ {"time": time_string, "lat": latitude, "lon": longitude, "start_lat": latitude, "start_lon": longitude, "stop_lat": latitude, 
"stop_lon": longitude, "campaign_id": camp, "duration": duration, "devices": devices, "speed": str(speed)} ]

payload = '{"user": "' + user + '", "code": "' + token + '", "API_KEY": "' + api_key + '", "data": {"lat":' + latitude + ', "lon": ' + longitude + ', "cur_campaign": ' + str(cur_campaign) + ', "device_id": "' + str(device_id) + '", "projector_left": 325, "projector_right": 326, "stats": ' + str(stats) +'}} '


print payload
