import uuid
import os

# check if deviceID has been issued yet
exists = os.path.isfile('deviceID.txt')
if exists:
    with open('deviceID.txt', 'r') as f:
        device_id = f.readline()
else:
    device_id = str(uuid.uuid4().hex).upper()
    with open('deviceID.txt', 'w') as f:
        f.write(device_id)
    with open('deviceID.txt', 'r') as f:
    	device_id = f.readline()

orientation = 'LEFT'  # Default
# orientation = 'RIGHT'

api_key = '21E4E81DF8E9103AAA181228C7B3D111'
base_url = 'https://api.adwayusa.com'
image_dir = ('/home/pi/Adway/images/')
user = 'someone@example.com'
passwd = 'xxx'
