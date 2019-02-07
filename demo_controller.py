import time
import datetime
import psutil
import json
import sysparam
import os
import signal
import requests
import socket
import platform
import logging
import sys

logging.basicConfig(filename='events.log',level=logging.DEBUG)

from picamera import PiCamera
from gps import *
import threading
from bluepy.btle import Scanner, DefaultDelegate

camera_exists = 0
state = {}
active_campaigns = []
offline_campaigns = []
count = 0

arch = platform.machine()

try:
    camera = PiCamera()
    camera_exists = 1
except:
    camera_exists = 0

token = ''
device_token = ''

api_key = sysparam.api_key
base_url = sysparam.base_url
device_id = sysparam.device_id
header = {'Content-Type': 'application/json', 'cache-control': 'no-cache'}


class GpsPoller(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global gpsd
        gpsd = gps(mode=WATCH_ENABLE)
        self.current_value = None
        self.running = True

    def run(self):
        global gpsd
        while gpsp.running:
            gpsd.next()

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)


displayed_campaigns = []  # List of displayed campaigns & stats to send to server

def internet(host='8.8.8.8', port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        return False


def initiateState():
    logging.info('initiating state')
    global state
    state['login'] = 'OFF'
    state['location'] = (34.5849, -118.1568)
    state['last_location'] = (34.5849, -118.1568)
    state['speed'] = 0
    state['current_campaign'] = 0
    state['device_id'] = device_id
    return


def displayImage(img_dir, dur, adv, camp, loc):
    global arch
    global camera_exists
    global count

    # Display image
    logging.info('Displaying image %s', img_dir)

    try:
        os.system('feh --hide-pointer -x -q -B black -g 1280x720 ' + img_dir + ' &')
    except:
        logging.info('Image display failed')
        return
        
    # If testing on non-PI
    if arch == 'x86_64':
        time.sleep(dur)
    else:
        # Take picture every 10th round of images
        if camera_exists == 1 and count % 10 == 0:
            logging.info('Taking picture')
            time.sleep(dur/2)
            takePhoto(adv, camp, loc)
            time.sleep(dur/2)
        else:
            time.sleep(dur)

    # Clear image
    for process in psutil.process_iter():
        if 'feh' in process.cmdline():
            process.terminate()
    return


def takePhoto(advertiser, campaign, location):

    camera.resolution = (640, 480)

    # See if correct directory exists; if not, create it:
    if not os.path.exists(sysparam.image_dir + '/' + advertiser):
        os.makedirs(sysparam.image_dir + '/' + advertiser)
    camera.capture(sysparam.image_dir + '/' + advertiser + '/' + str(campaign) + '_' + str(location[0]) + '_' +
                   str(location[1]) + datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + '.jpg')
    return


def login(user, password, location):
    """
    Logs user into system and sets global session token
    :param user: string
    :param password: string
    :param location: tuple: (lat, lon) as floats
    :return:
    """
    global state
    logging.info('logging in')
    url = base_url + '/user/login'
    payload = '{"user": "' + user + '", "API_KEY": "' + api_key + '", "data": {"secret": "' + password + \
              '", "lat": ' + str(state['location'][0]) + ', "lon": ' + str(state['location'][1]) + '}}'
    response = requests.request("POST", url, data=payload, headers=header)
    state['login'] = 'ON'

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
    logging.info('initializing device')
    url = base_url + '/init/device'
    payload = '{"API_KEY": "' + api_key + '", "data": {"device_id": "' + device_id + '", "lat": 34.5849, "lon": -118.1568}}'
    response = requests.request('POST', url, data=payload, headers=header)
    x = json.loads(response.text)
    token = x['data'][0]['token']

    return


def main():
    return

if __name__ == '__main__':
    state = {}
    logging.info('starting program')
    gpsp = GpsPoller()
    campaign_one = '/home/pi/ADWAY/JP'
    camp_one_dur = 10
    camp_one_id = '1'
    campaign_two = '/home/pi/ADWAY/AD'
    camp_two_dur = 10
    camp_two_id = '2'
    campaign_three = '/home/pi/ADWAY/web'
    camp_three_dur = 10
    camp_three_id = '3'
    campaign_four = '/home/pi/ADWAY/AA'
    camp_four_dur = 10
    camp_four_id = '4'
    count = 0

    initiateState()

    logging.info('checking for internet')
    if internet():
        logging.info('got internet')
        login(sysparam.user, sysparam.password, state['location'])
        initializeDevice(sysparam.user, state['location'])
    else:
        logging.info('no internet, continuing...')
        
    try:
        gpsp.start() 
        while True:
            logging.info('starting loop')
            displayed_campaigns = []

            logging.info('reading from GPS')
            try:
                read_lat = round( gpsd.fix.latitude, 4)
                read_lon = round(gpsd.fix.longitude, 4)
                latString = read_lat
                lonString = read_lon
                logging.info('GPS read successful')

            except:
                latString = state['last_location'][0]
                lonString = state['last_location'][1]
                logging.info('GPS read unsuccessful')

            logging.info(latString)
            logging.info(lonString)

            ###############################################################

            displayed_campaign = {}
            displayed_campaign['fix'] = True

            if latString == 0.0 or lonString == 0.0:
                logging.info('No fix')
                latString = state['last_location'][0]
                lonString = state['last_location'][1]
                displayed_campaign['fix'] = False

            logging.info('Converting speed')
            try:
                spdString = int((round(gpsd.fix.speed, 4) * 1.60934))  # Converting MPH to KPH
            except:
                spdString = 0

            if latString == 0.0 or lonString == 0.0:
                dateString = '01-01-2019'
            else:
                dateString = str(gpsd.utc)
                dateString = dateString.replace('_', ' ')

            state['location'] = (latString, lonString)
            state['last_location'] = state['location']
            state['speed'] = spdString

            logging.info('Scanning for BT devices')
            try:
                scanner = Scanner().withDelegate(ScanDelegate())
                devices = len(scanner.scan(2.0))
                logging.info('Got %s devices', str(devices))
            except:
                logging.info('BT scan failed')
                devices = 1

            logging.info('writing to GPS log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_one - ' + dateString + '\n')
                f.write(str(latString) + ', ' + str(lonString) + '\n')
                f.write(str(spdString) + 'kph\n')
            logging.info('trying to display image')
            try:
                displayImage(campaign_one, 10, 'campaign_one', '1', (latString, lonString))

                displayed_campaign["campaign_id"] = camp_one_id
                displayed_campaign["lat"] = state['location'][0]
                displayed_campaign["lon"] = state['location'][1]
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = state['location'][0]
                displayed_campaign["start_lon"] = state['location'][1]
                displayed_campaign["stop_lat"] = state['location'][0]
                displayed_campaign["stop_lon"] = state['location'][1]
                displayed_campaign["duration"] = 10
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices

                displayed_campaigns.append(displayed_campaign)
                logging.info('Finished campaign one')
            except:
                logging.info('image loading failed, continuing')
                continue


            ###############################################################
            logging.info('starting campaign two')
            displayed_campaign = {}
            displayed_campaign['fix'] = True

            if latString == 0.0 or lonString == 0.0:
                displayed_campaign['fix'] = False

            logging.info('writing to gps log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_two - ' + dateString + '\n')
                f.write(str(latString) + ', ' + str(lonString) + '\n')
                f.write(str(spdString) + 'kph\n')

            logging.info('trying to display image two')
            try:
                displayImage(campaign_two, 8, 'campaign_two', '2', (latString, lonString))
                displayed_campaign["campaign_id"] = camp_two_id
                displayed_campaign["lat"] = state['location'][0]
                displayed_campaign["lon"] = state['location'][1]
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = state['location'][0]
                displayed_campaign["start_lon"] = state['location'][1]
                displayed_campaign["stop_lat"] = state['location'][0]
                displayed_campaign["stop_lon"] = state['location'][1]
                displayed_campaign["duration"] = 8
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices
                
                displayed_campaigns.append(displayed_campaign)

                logging.info('finishing campaign two')
            except:
                logging.info('image loading failed, continuing')
                continue

            ###############################################################
            logging.info('starting campaign three')
            displayed_campaign = {}
            displayed_campaign['fix'] = True

            if latString == 0.0 or lonString == 0.0:
                displayed_campaign['fix'] = False

            logging.info('writing to gps log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_three - ' + dateString + '\n')
                f.write(str(latString) + ', ' + str(lonString) + '\n')
                f.write(str(spdString) + 'kph\n')

            logging.info('trying to display image three')
            try:
                displayImage(campaign_three, 5, 'campaign_three', '3', (latString, lonString))
                displayed_campaign["campaign_id"] = camp_three_id
                displayed_campaign["lat"] = state['location'][0]
                displayed_campaign["lon"] = state['location'][1]
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = state['location'][0]
                displayed_campaign["start_lon"] = state['location'][1]
                displayed_campaign["stop_lat"] = state['location'][0]
                displayed_campaign["stop_lon"] = state['location'][1]
                displayed_campaign["duration"] = 5
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices

                displayed_campaigns.append(displayed_campaign)
                logging.info('finishing campaign three')
            except:
                logging.info('image loading failed, continuing')
                continue


            ###############################################################
            logging.info('starting campaign four')
            displayed_campaign = {}
            displayed_campaign['fix'] = True

            if latString == 0.0 or lonString == 0.0:
                displayed_campaign['fix'] = False

            logging.info('writing to gps log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_four - ' + dateString + '\n')
                f.write(str(latString) + ', ' + str(lonString) + '\n')
                f.write(str(spdString) + 'kph\n')

            logging.info('trying to display image four')
            try:
                displayImage(campaign_four, 8, 'campaign_four', '4', (latString, lonString))
                displayed_campaign["campaign_id"] = camp_four_id
                displayed_campaign["lat"] = state['location'][0]
                displayed_campaign["lon"] = state['location'][1]
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = state['location'][0]
                displayed_campaign["start_lon"] = state['location'][1]
                displayed_campaign["stop_lat"] = state['location'][0]
                displayed_campaign["stop_lon"] = state['location'][1]
                displayed_campaign["duration"] = 8
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices

                displayed_campaigns.append(displayed_campaign)
                
                logging.info('finishing campaign four')
            except:
                logging.info('image loading failed, continuing')
                continue

            ###############################################################
            logging.info('starting campaign five')
            displayed_campaign = {}
            displayed_campaign['fix'] = True

            if latString == 0.0 or lonString == 0.0:
                displayed_campaign['fix'] = False

            logging.info('writing to gps log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_three - ' + dateString + '\n')
                f.write(str(latString) + ', ' + str(lonString) + '\n')
                f.write(str(spdString) + 'kph\n')
            logging.info('trying to display image five')
            try:
                displayImage(campaign_three, 5, 'campaign_three', '3', (latString, lonString))
                displayed_campaign["campaign_id"] = camp_three_id
                displayed_campaign["lat"] = state['location'][0]
                displayed_campaign["lon"] = state['location'][1]
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = state['location'][0]
                displayed_campaign["start_lon"] = state['location'][1]
                displayed_campaign["stop_lat"] = state['location'][0]
                displayed_campaign["stop_lon"] = state['location'][1]
                displayed_campaign["duration"] = 5
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices

                displayed_campaigns.append(displayed_campaign)
                logging.info('finishing campaign five')
            except:
                logging.info('image loading failed, continuing')
                continue


###################################################################################################################
        
            if internet():

                # First make sure you're logged in and have a token
                if state['login'] == 'OFF':
                    login(sysparam.user, sysparam.password, state['location'])
                    initializeDevice(sysparam.user, state['location'])

                logging.info('Have connection, uploading stats')
                url = base_url + '/get/content'

                stats = []
                for i in range(len(displayed_campaigns)):
                    stats.append(displayed_campaigns[i])
                sent_stats = json.dumps(stats)

                payload = '{"user": "' + sysparam.user + '", "code": "' + token + '", "API_KEY": "' + api_key + '", "data": {"lat":' + str(state['location'][0]) + ', "lon": ' + str(state['location'][1]) + ', "cur_campaign": ' + str(state['current_campaign']) + ', "device_id": "' + state['device_id'] + '", "projector_left": 325, "projector_right": 326, "stats": ' + sent_stats + '}} '
                #print json.dumps(payload)

                response = requests.request('POST', url, data=payload, headers=header)
                #response = requests.request('POST', url, data=json.dumps(payload), headers=header)
                logging.info(str(response))

                count += 1

            else:
                logging.info('No internet, continuing')
                continue

    except(KeyboardInterrupt, SystemExit):
        gpsp.running = False
        gpsp.join()
        
