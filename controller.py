import time
import datetime
import subprocess
import json
import sysparam
import os
import requests
from picamera import PiCamera

api_key = sysparam.api_key
base_url = sysparam.base_url
device_id = sysparam.device_id
header = {'Content-Type': 'application/json', 'cache-control': 'no-cache'}
state = {}

global token
global device_token


active_campaigns = []  # List of campaigns to show
# Use models.CampaignModel as a template

displayed_campaigns = []  # List of displayed campaigns & stats to send to server
# Use models.DisplayedModel as a template


def initiateState():
    global state
    state['login'] = 'OFF'
    state['projector_status'] = 'OFF'
    state['location'] = (0, 0)
    state['current_campaign'] = 0
    if sysparam.orientation == 'LEFT':
        state['orientation'] = 'LEFT'
    else:
        state['orientation'] = 'RIGHT'
    print state
    return


def displayImage(img, dur):
    # Display image
    time.sleep(dur)
    # Clear image
    return


def displayDefaultImage():
    default_image = sysparam.image_dir + 'default.png'
    displayImage(default_image, 9)
    return


def getCurrentLocation():
    """
    Read from GPS unit, update state with current location
    :return:
    """
    global state
    lat = '181.005'
    lon = '45.6'
    location = (lat, lon)
    state['location'] = location
    print state['location']
    return


def initiateProjector():
    global state
    state['projector_status'] = 'ON'
    print 'Projector on'
    return


# This function only works on the Raspberry Pi
def takePhoto(advertiser, campaign, location):
    camera = PiCamera()
    camera.resolution = (1024, 768)
    camera.start_preview()  # perhaps not necessary?
    # See if correct directory exists; if not, create it:
    if not os.path.exists(sysparam.image_dir + '/' + advertiser):
        os.makedirs(sysparam.image_dir + '/' + advertiser)
    camera.capture(sysparam.image_dir + '/' + advertiser + '/' + str(campaign) + '_' + str(location[0]) + '_' +
                   str(location[1]) + datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + '.jpg')


def displayCampaign(campaign):
    """
    Displays images associated with campaign
    :param campaign: dict - see models.CampaignModel for template
    :return:
    """
    global state
    global displayed_campaigns
    displayed_campaign = {}
    duration = campaign['duration']
    if state['orientation'] == 'LEFT':
        image = campaign['image_left']
    else:
        image = campaign['image_right']
    getCurrentLocation()
    takePhoto(campaign['advertiser'], campaign['id'], state['location'])
    displayed_campaign['lat'] = state['location'][0]
    displayed_campaign['lon'] = state['location'][1]
    displayed_campaign['time_run'] = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    displayed_campaign['start_lat'] = state['location'][0]
    displayed_campaign['start_lon'] = state['location'][1]
    displayImage(image, duration)
    getCurrentLocation()
    displayed_campaign['stop_lat'] = state['location'][0]
    displayed_campaign['stop_lon'] = state['location'][1]
    displayed_campaign['duration'] = duration

    displayed_campaigns.append(displayed_campaign)
    return


def login(user, password, location):
    """
    Logs user into system and sets global session token
    :param user: string
    :param password: string
    :param location: tuple: (lat, lon) as floats
    :return:
    """
    global token
    global state
    url = base_url + '/user/login'
    payload = '{"user": "' + user + '", "API_KEY": "' + api_key + '", "data": {"secret": "' + password + \
              '", "lat": ' + str(state['location'][0]) + ', "lon": ' + str(state['location'][1]) + '}}'
    # payload = "{\"user\": \"wolframdonat@gmail.com\", \"API_KEY\": \"21E4E81DF8E9103AAA181228C7B3D111\",
    # \"data\":{\"secret\": \"5mudg301\", \"lat\": 121.12, \"lon\": 321.12}}\n"
    response = requests.request("POST", url, data=payload, headers=header)
    x = json.loads(response.text)
    token = x['data'][0]['token']
    print token
    state['login'] = 'ON'
    print 'Logged in'
    return


def logout(user):
    """
    Logs user out of system and deactivates tokens
    :param user: string
    :return:
    """
    global token
    global state
    url = base_url + '/logout'
    payload = '{"user": "' + user + '", "code": "' + token + '", "API_KEY": "' + api_key + '"}'
    requests.request("POST", url, data=payload, headers=header)
    state['login'] = 'OFF'
    return


def initializeDevice(user, location):
    """
    Creates device and initializes global device token
    :param user: string
    :param location: tuple: (lat, lon) as floats
    :return:
    """
    global token
    global device_token
    url = base_url + '/init/device'
    payload = '{"API_KEY": "' + api_key + '", "data": {"device_id": "' + device_id + '", "lat": ' + str(location[0]) + \
              ', "lon": ' + str(location[1]) + '}}'
    response = requests.request('POST', url, data=payload, headers=header)
    print response
    print 'device initialized'
    return


def getContent(user):
    """
    Sends current device data as well as getting new data from the server
    regarding campaigns
    :param user: string
    :param location: tuple (lat, lon) as floats
    :param CampaignModel: see models.py
    :return:
    """
    global token
    global active_campaigns
    global displayed_campaigns
    global state
    getCurrentLocation()
    url = base_url + '/get/content'

    payload = '{"user": "' + user + '", "code": "' + token + '", "API_KEY": "' + api_key + '", "data": {"lat":' + \
              str(state['location'][0]) + ', "lon": ' + str(state['location'][1]) + ', "cur_campaign": ' + \
              str(state['current_campaign']) + ', "device_id": "' + device_id + '", "projector_left": 325, \
              "projector_right": 326, "stats": ' + str(displayed_campaigns) + '}}'

    # payload = '{"user": "' + user + '", "code": "' + token + '", "API_KEY": "' + api_key + \
    #           '", "data": {"lat":' + str(location[0]) + ', "lon": ' + str(location[1]) + ', "cur_campaign": 2342, "device_id": "' + device_id + \
    #           '", "projector_left": 325, "projector_right": 326, "stats": [ {"time": "2017-02-21 13:32:21", \
    #           "lat": 234, "lon": 234, "start_lat": 231, "start_lon": -23.22, "stop_lat":231, "stop_lon": -23.22, \
    #           "campaign_id": 1, "duration": 10}, {"time": "2017-02-21 13:32:32", "lat": 231, "lon": -23.2201, \
    #           "start_lat": 231, "start_lon": -23.22, "stop_lat": 231, "stop_lon": -23.22, "campaign_id": 2, \
    #           "duration": 15}, {"time": "2017-02-21 13:32:47", "lat": 231, "lon": -23.2203, "start_lat": 231, \
    #           "start_lon": -23.22, "stop_lat": 231, "stop_lon": -23.22, "campaign_id":1, "duration": 10} ] } }'

    response = requests.request('POST', url, data=payload, headers=header)
    response_dict = json.loads(response.text)
    camp_list = response_dict['data']
    active_campaigns = []  # Start over with fresh list of campaigns
    if len(camp_list) == 0:  # There are no campaigns to show, so go with default
        cm = {}
        cm['id'] = 1
        cm['name'] = 'ADWAY GLOBAL'
        cm['latitude'] = str(state['location'][0])
        cm['longitude'] = str(state['location'][1])
        cm['distance'] = 99
        cm['duration'] = 99
        cm['advertiser'] = 'ADWAY'
        cm['image_left'] = 'https://s3.amazonaws.com/adwayusa/website/ADWAY_BW_right.jpg'
        cm['image_right'] = 'https://s3.amazonaws.com/adwayusa/website/ADWAY_BW_right.jpg'
        cm['logo_link'] = 'https://s3.amazonaws.com/adwayusa/ads/UllbRsLkao_logo.jpg'
        cm['price'] = 0
        cm['priority'] = 99

        active_campaigns.append(cm)
        return

    for i in range(len(camp_list)):
        cm = {}
        cm['id'] = camp_list[i]['id']
        cm['name'] = camp_list[i]['name']
        cm['latitude'] = camp_list[i]['lat']
        cm['longitude'] = camp_list[i]['lon']
        cm['distance'] = camp_list[i]['distance']
        cm['duration'] = camp_list[i]['duration']
        cm['advertiser'] = camp_list[i]['advertiser']
        cm['image_left'] = camp_list[i]['content_left']
        cm['image_right'] = camp_list[i]['content_right']
        cm['logo_link'] = camp_list[i]['content_logo']
        cm['price'] = camp_list[i]['pay_per_minute']
        cm['priority'] = camp_list[i]['priority']

        active_campaigns.append(cm)
    return


def main():
    global state
    global active_campaigns
    global displayed_campaigns
    initiateState()
    login('wolframdonat@gmail.com', '5mudg301', state['location'])
    initializeDevice('wolframdonat@gmail.com', state['location'])
    initiateProjector()
    getCurrentLocation()
    displayDefaultImage()
    getContent('wolframdonat@gmail.com')
    print active_campaigns
#    for i in range(len(active_campaigns)):
#        displayCampaign(active_campaigns[i])


if __name__ == '__main__':
    main()

# img = Image.open('/home/wolf/Pictures/dsd-2.png')
# img.show()
#file1 = subprocess.call(['firefox', '/home/wolf/Pictures/dsd-1.png'])
#time.sleep(5)
#file1.terminate()
#file1.kill()
