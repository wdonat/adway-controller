import time
import datetime
import psutil
import json
import sysparam
import os
import signal
import requests
import socket
from bluetooth import *
from picamera import PiCamera
from gps import *
import threading

api_key = sysparam.api_key
base_url = sysparam.base_url
device_id = sysparam.device_id
header = {'Content-Type': 'application/json', 'cache-control': 'no-cache'}
state = {}

class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd
        gpsd = gps(mode=WATCH_ENABLE)
        self.current_value = None
        self.running = True

    def run(self):
        global gpsd
        gpsd.next()

global token
global device_token


active_campaigns = []  # List of campaigns to show
offline_campaigns = []  # mirrors last list of active camps for connectivity drops

# Herein lies the problem: if a Bluetooth device is not in 'discoverable' mode,
# it will not show up on scans!!!
def getBluetooth():
    nearby_devices = discover_devices(lookup_names = True)
    print 'found %d devices' % len(nearby_devices)
    return len(nearby_devices)

def internet(host='8.8.8.8', port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        return False

def fillInCampaigns():
    global active_campaigns
    cm['id'] = 1
    cm['name'] = 'ADWAY GLOBAL'
    cm['latitude'] = str(state['location'][0])
    cm['longitude'] = str(state['location'][1])
    cm['distance'] = 99
    cm['duration'] = 99
    cm['advertiser'] = 'ADWAY'
    cm['left_dir'] = sysparam.image_dir + 'ADWAY/left/'
    cm['right_dir'] = sysparam.image_dir + 'ADWAY/right/'
    cm['image_left'] = 'https://s3.amazonaws.com/adwayusa/website/ADWAY_BW_right.jpg'
    cm['image_right'] = 'https://s3.amazonaws.com/adwayusa/website/ADWAY_BW_right.jpg'
    cm['logo_link'] = 'https://s3.amazonaws.com/adwayusa/ads/UllbRsLkao_logo.jpg'
    cm['price'] = 0
    cm['priority'] = 99
    active_campaigns.append(cm)

    cm['id'] = 2
    cm['name'] = 'TEST CAMPAIGN'
    cm['latitude'] = str(state['location'][0])
    cm['longitude'] = str(state['location'][1])
    cm['distance'] = 50
    cm['duration'] = 50
    cm['advertiser'] = 'SAURON'
    cm['left_dir'] = sysparam.image_dir + 'SAURON/left/'
    cm['right_dir'] = sysparam.image_dir + 'SAURON/right/'
    cm['image_left'] = 'https://hdwallpapers2013.com/wp-content/uploads/2013/03/The-Avengers-Logo-Wallpaper.jpg'
    cm['image_right'] = 'https://hdwallpapers2013.com/wp-content/uploads/2013/03/The-Avengers-Logo-Wallpaper.jpg'
    cm['logo_link'] = 'https://s3.amazonaws.com/adwayusa/ads/UllbRsLkao_logo.jpg'
    cm['price'] = 2
    cm['priority'] = 99
    active_campaigns.append(cm)

displayed_campaigns = []  # List of displayed campaigns & stats to send to server
# Use models.DisplayedModel as a template


def initiateState():
    global state
    state['login'] = 'OFF'
    state['projector_status'] = 'OFF'
    state['location'] = (34.103, -118.326)
    state['current_campaign'] = 0
    if sysparam.orientation == 'LEFT':
        state['orientation'] = 'LEFT'
    else:
        state['orientation'] = 'RIGHT'
    state['device_id'] = device_id
    return


def displayImage(img_dir, dur):
    # Display image
    os.system('feh --hide-pointer -x -q black -g 1366x768 ' + img_dir + ' &')
    time.sleep(dur)
    # Clear image
    for process in psutil.process_iter():
        if 'feh' in process.cmdline():
            process.terminate()
    return


def getCurrentLocation():
    """
    Read from GPS unit, update state with current location
    :return:
    """
    global state
    global gpsd

    # hard-coded for demo
    lat = '34.103'
    lon = '-118.326'
    lat = str(gpsd.fix.latitude * 100)
    lon = str(gpsd.fix.longitude * 100)

    location = (lat, lon)
    state['location'] = location
    print state['location']
    return


def initiateProjector():
    global state
    state['projector_status'] = 'ON'
    print 'Projector on'
    return


This function only works on the Raspberry Pi
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

    displayed_campaign["campaign_id"] = campaign['id']
    displayed_campaign["lat"] = state['location'][0]
    displayed_campaign["lon"] = state['location'][1]
    displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    displayed_campaign["start_lat"] = state['location'][0]
    displayed_campaign["start_lon"] = state['location'][1]
    print 'campaign: ', campaign['id'], 'name: ', campaign['name'], 'duration: ', duration 
    if state['orientation'] == 'LEFT':
        displayImage(campaign['left_dir'], duration)
    else:
        displayImage(campaign['right_dir'], duration)
    # takePhoto(campaign['advertiser'], campaign['id'], state['location'])
    getCurrentLocation()
    displayed_campaign["stop_lat"] = state['location'][0]
    displayed_campaign["stop_lon"] = state['location'][1]
    displayed_campaign["duration"] = duration
    displayed_campaign["speed"] = 45
    displayed_campaign["RT_impressions"] = 5

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
    payload = '{"API_KEY": "' + api_key + '", "data": {"device_id": "' + device_id + '", "lat": 34.103, "lon": -118.326}}'
    response = requests.request('POST', url, data=payload, headers=header)
    print response
    print 'device initialized'
    return


def getContent(user, latitude, longitude):
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
    global offline_campaigns
    global displayed_campaigns
    global state
    global device_id
    
    url = base_url + '/get/content'

    payload = '{"user": "' + user +\
    '", "code": "' + token +\
    '", "API_KEY": "' + api_key +\
    '", "data": {"lat":' + latitude +\
    ', "lon": ' + longitude +\
    ', "cur_campaign": ' + str(state['current_campaign']) +\
    ', "device_id": "' + state['device_id'] +\
    '", "projector_left": 325, "projector_right": 326, "stats": []}} '
    #print payload
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
    print response_dict
    camp_list = response_dict['data']
    active_campaigns = []  # Start over with fresh list of campaigns
    offline_campaigns = []  # Ditto
    if len(camp_list) == 0:  # There are no campaigns to show, so go with default
        cm = {}
        cm['id'] = 1
        cm['name'] = 'ADWAY GLOBAL'
        cm['latitude'] = str(state['location'][0])
        cm['longitude'] = str(state['location'][1])
        cm['distance'] = 99
        cm['duration'] = 99
        cm['advertiser'] = 'ADWAY'
        cm['left_dir'] = sysparam.image_dir + 'ADWAY/left/'
        cm['right_dir'] = sysparam.image_dir + 'ADWAY/right/'
        cm['image_left'] = 'https://s3.amazonaws.com/adwayusa/website/ADWAY_BW_right.jpg'
        cm['image_right'] = 'https://s3.amazonaws.com/adwayusa/website/ADWAY_BW_right.jpg'
        cm['logo_link'] = 'https://s3.amazonaws.com/adwayusa/ads/UllbRsLkao_logo.jpg'
        cm['price'] = 0
        cm['priority'] = 99

        active_campaigns.append(cm)
        return
    
    # Or there are campaigns to show
    for i in range(len(camp_list)):
        cm = {}
        cm['id'] = camp_list[i]['id']
        cm['name'] = camp_list[i]['name'].replace(' ', '')
        cm['latitude'] = camp_list[i]['lat']
        cm['longitude'] = camp_list[i]['lon']
        cm['distance'] = camp_list[i]['distance']
        cm['duration'] = camp_list[i]['duration']
        cm['advertiser'] = camp_list[i]['advertiser']
        cm['image_left_loc'] = camp_list[i]['content_left']
        cm['image_right_loc'] = camp_list[i]['content_right']
        cm['logo_link'] = camp_list[i]['content_logo']
        cm['price'] = camp_list[i]['pay_per_minute']
        cm['priority'] = camp_list[i]['priority']

        # Download images and save to appropriate dirs
        # Make dirs if necessary
        if not os.path.exists(sysparam.image_dir + cm['advertiser'] + '/' + cm['name']):
            os.makedirs(sysparam.image_dir + cm['advertiser'] + '/' + cm['name'])
            # ~/Adway/images/ADWAY/Caliente
        if not os.path.exists(sysparam.image_dir + '/' + cm['advertiser'] + '/' + cm['name'] + '/left/'):
            os.makedirs(sysparam.image_dir + '/' + cm['advertiser'] + '/' + cm['name'] + '/left/')
            # ~/Adway/images/ADWAY/Caliente/left
        left_dir = sysparam.image_dir + cm['advertiser'] + '/' + cm['name'] + '/left/'
        if not os.path.exists(sysparam.image_dir + cm['advertiser'] + '/' + cm['name'] + '/right/'):
            os.makedirs(sysparam.image_dir + cm['advertiser'] + '/' + cm['name'] + '/right/')
        right_dir = sysparam.image_dir + cm['advertiser'] + '/' + cm['name'] + '/right/'

        # Download images if they don't exist already
        il_name = cm['image_left_loc'].split('/')[-1] 
        ir_name = cm['image_right_loc'].split('/')[-1]
        if not os.path.isfile(left_dir + il_name): 
            os.system('wget -P ' + left_dir + ' ' + cm['image_left_loc'])
        if not os.path.isfile(right_dir + ir_name):
            os.system('wget -P ' + right_dir + ' ' + cm['image_right_loc'])
        
        cm['image_left'] = left_dir + il_name
        cm['image_right'] = right_dir + ir_name
        cm['left_dir'] = left_dir
        cm['right_dir'] = right_dir
        
        active_campaigns.append(cm)

    for camp in active_campaigns:
        offline_campaigns.append(camp)
    # with open ('campaigns.txt', 'w') as f:
    #     f.write(str(active_campaigns))

    return

def main():
    return

if __name__ == '__main__':
    gpsp = GpsPoller()
    global state
    global active_campaigns
    global displayed_campaigns
    global offline_campaigns

    print 'initiating state'
    initiateState()

    print 'logging in'
    login('wolframdonat@gmail.com', '5mudg301', state['location'])

    print 'initializing device'
    initializeDevice('wolframdonat@gmail.com', state['location'])


    try:
        gpsp.start() 


        

        getCurrentLocation()
        print 'current location is: lat: ', str(state['location'][0]), ' lon: ', str(state['location'][1])

        while True:
            # Check if we have an active internet connection
            if internet():
                print 'Have connection, getting fresh campaigns'

                # Get location
                latString = str(abs(round(gpsd.fix.latitude, 2)))
                lonString = str(abs(round(gpsd.fix.longitude, 2)))
                dateString = str(gpsd.utc)

                getContent('wolframdonat@gmail.com', latString, lonString)

                for i in range(len(active_campaigns)):
                    displayCampaign(active_campaigns[i])
            else:
                for i in range(len(offline_campaigns)):

                    displayCampaign(offline_campaigns[i])

    except(KeyboardInterrupt, SystemExit):
        gpsp.running = False
        gpsp.join()
        

            

