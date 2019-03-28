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
import math
import signal
from subprocess import Popen

logging.basicConfig(filename='events.log',format='%(asctime)s %(message)s', level=logging.DEBUG)

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

def handler(s, f):
    logging.info("Couldn't connect - Signal handler called with signal %s", s) 
    raise IOError("Couldn't connect")

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
    with open ('/home/pi/Code/adway-controller/last_location.txt', 'r') as f:
        loc = f.readline()
        loc = loc.split()

    state['location'] = (loc[0], loc[1])
    state['last_location'] = (loc[0], loc[1])
    state['speed'] = 0
    state['current_campaign'] = 0
    state['device_id'] = device_id
    state['device_init'] = 'OFF'
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


def login(user, password, f):
    """
    Logs user into system and sets global session token
    :param user: string
    :param password: string
    :param f: Boolean - do we have a fix or not?
    :return:
    """
    global state
    url = base_url + '/user/login'

    if state['location'][0] == 0.0 or state['location'][1] == 0.0 or math.isnan(state['location'][0]) or math.isnan(state['location'][1]):
        with open('/home/pi/Code/adway-controller/last_location.txt', 'r') as g:
            loc = g.readline()
            loc = loc.split()
            state['location'] = (loc[0], loc[1])

    payload = '{"user": "' + user + '", "API_KEY": "' + api_key + '", "data": {"secret": "' + password + \
              '", "lat": ' + str(state['location'][0]) + ', "lon": ' + str(state['location'][1]) + ', "fix": ' + str(f).lower() + '}}'
    logging.info(payload)

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(5)
    response = requests.request("POST", url, data=payload, headers=header)
    signal.alarm(0)

    response_dict = json.loads(response.text)
    logging.info(str(response_dict))

    if len(response.content) < 450 or 'error' in response_dict:
        login(user, password, f)
    else:
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


def initializeDevice(user, f):
    """
    Creates device and initializes global device token
    :param user: string
    :param f: Boolean - do we have a fix or not?
    :return:
    """
    global token
    global device_token
    url = base_url + '/init/device'

    if state['location'][0] == 0.0 or state['location'][1] == 0.0 or math.isnan(state['location'][0]) or math.isnan(state['location'][1]):
        with open('/home/pi/Code/adway-controller/last_location.txt', 'r') as g:
            loc = g.readline()
            loc = loc.split()
            state['location'] = (loc[0], loc[1])

    payload = '{"API_KEY": "' + api_key + '", "data": {"device_id": "' + device_id + '", "lat": ' + str(state['location'][0]) + ', "lon": ' + str(state['location'][1]) + ', "fix": ' + str(f).lower() + '}}'
    logging.info(payload)

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(5)
    response = requests.request('POST', url, data=payload, headers=header)
    signal.alarm(0)

    response_dict = json.loads(response.text)
    logging.info(str(response_dict))

    if len(response.content) < 90 or 'error' in response_dict:
        initializeDevice(user, f)
    else:
        x = json.loads(response.text)
        token = x['data'][0]['token']
        state['device_init'] = 'ON'
        return


if __name__ == '__main__':

    state = {}
    logging.info('\n')
    logging.info('starting program')
    gpsp = GpsPoller()
    campaign_one = '/home/pi/ADWAY/AA'
    camp_one_dur = 8
    camp_one_id = 312
    campaign_two = '/home/pi/ADWAY/web'
    camp_two_dur = 8
    camp_two_id = 312
    campaign_three = '/home/pi/ADWAY/DA'
    camp_three_dur = 8
    camp_three_id = 312
    campaign_four = '/home/pi/ADWAY/JP'
    camp_four_dur = 16
    camp_four_id = 312
    count = 0

    p = Popen('python /home/pi/Code/adway-controller/freeze_check.py', shell=True)

    initiateState()

    logging.info('checking for internet')
    if internet():
        logging.info('got internet')
    else:
        logging.info('no internet, continuing...')
        
    try:
        gpsp.start()

        # Display default image while waiting for a fix
        logging.info('Displaying default image, waiting for fix')
        os.system('feh --hide-pointer -x -q -B black -g 1280x720 /home/pi/ADWAY/web &')

        # Wait for a fix
        while len(gpsd.satellites) < 3:
            time.sleep(0.5)

        # Got fix, clear default image
        logging.info('Got initial fix, continuing with program')
        for process in psutil.process_iter():
            if 'feh' in process.cmdline():
                process.terminate()

        # Get current location for logging in and initializing
        try:
            init_lat = round(gpsd.fix.latitude, 4)
            init_lon = round(gpsd.fix.longitude, 4)
            fix = True
        except:
            with open('/home/pi/Code/adway-controller/last_location.txt', 'r') as f:
                loc = f.readline()
                loc = loc.split()
            init_lat = loc[0]
            init_lon = loc[1]
            fix = False

        state['location'] = (init_lat, init_lon)
        if internet():
            if state['login'] == 'OFF':
                logging.info('got internet, logging in')
                while state['login'] == 'OFF':
                    login(sysparam.user, sysparam.password, fix)
                    time.sleep(0.5)

            logging.info('got internet, initializing device')
            while state['device_init'] == 'OFF':
                initializeDevice(sysparam.user, fix)
                time.sleep(0.5)
        logging.info('token = %s', token)

        while True:
            logging.info('starting loop')
            displayed_campaigns = []

            logging.info('reading from GPS')
            try:
                latString = round( gpsd.fix.latitude, 4)
                lonString = round(gpsd.fix.longitude, 4)
                logging.info('GPS read successful')

            except:
                latString = state['last_location'][0]
                lonString = state['last_location'][1]
                logging.info('GPS read unsuccessful')

            logging.info(latString)
            logging.info(lonString)
            state['last_location'] = (latString, lonString)

            ###############################################################
            # Campaign One

            displayed_campaign = {}

            try:
                start_lat = round(gpsd.fix.latitude, 4)
                start_lon = round(gpsd.fix.longitude, 4)
                displayed_campaign['fix'] = True
            except:
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            if start_lat == 0.0 or start_lat == 0.0 or math.isnan(start_lat) or math.isnan(start_lon):
                logging.info('No fix')
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            logging.info('Converting speed')
            try:
                spdString = int((round(gpsd.fix.speed, 4) * 1.60934))  # Converting MPH to KPH
            except:
                spdString = 0

            if start_lat == 0.0 or start_lon == 0.0:
                dateString = '01-01-2019'
            else:
                dateString = str(gpsd.utc)
                dateString = dateString.replace('_', ' ')

            state['location'] = (start_lat, start_lon)
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
                f.write(str(start_lat) + ', ' + str(start_lon) + '\n')
                f.write(str(spdString) + 'kph\n')

            logging.info('trying to display image')
            try:
                displayImage(campaign_one, 8, 'campaign_one', '1', (start_lat, start_lon))

                try:
                    stop_lat = round(gpsd.fix.latitude, 4)
                    stop_lon = round(gpsd.fix.longitude, 4)
                except:
                    stop_lat = start_lat
                    stop_lon = start_lon

                state['last_location'] = (stop_lat, stop_lon)
                displayed_campaign["campaign_id"] = camp_one_id
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = start_lat
                displayed_campaign["start_lon"] = start_lon
                displayed_campaign["stop_lat"] = stop_lat
                displayed_campaign["stop_lon"] = stop_lon
                displayed_campaign["duration"] = 10
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices

                displayed_campaigns.append(displayed_campaign)
                logging.info('Finished campaign one')
            except:
                logging.info('image loading failed, continuing')
                


            ###############################################################
            # Campaign Two

            logging.info('starting campaign two')
            displayed_campaign = {}

            try:
                start_lat = round(gpsd.fix.latitude, 4)
                start_lon = round(gpsd.fix.longitude, 4)
                displayed_campaign['fix'] = True
            except:
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            if start_lat == 0.0 or start_lat == 0.0 or math.isnan(start_lat) or math.isnan(start_lon):
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            logging.info('Converting speed')
            try:
                spdString = int((round(gpsd.fix.speed, 4) * 1.60934))
            except:
                spdString = 0

            if start_lat == 0.0 or start_lon == 0.0:
                dateString = '01-01-2019'
            else:
                dateString = str(gpsd.utc)
                dateString = dateString.replace('_', ' ')

            state['location'] = (start_lat, start_lon)
            state['last_location'] = state['location']
            state['speed'] = spdString

            logging.info('writing to gps log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_two - ' + dateString + '\n')
                f.write(str(start_lat) + ', ' + str(start_lon) + '\n')
                f.write(str(spdString) + 'kph\n')

            logging.info('trying to display image two')
            try:
                displayImage(campaign_two, 8, 'campaign_two', '2', (start_lat, start_lon))

                try:
                    stop_lat = round(gpsd.fix.latitude, 4)
                    stop_lon = round(gpsd.fix.longitude, 4)

                except:
                    stop_lat = start_lat
                    stop_lon = start_lon

                state['last_location'] = (stop_lat, stop_lon)    
                displayed_campaign["campaign_id"] = camp_two_id
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = start_lat
                displayed_campaign["start_lon"] = start_lon
                displayed_campaign["stop_lat"] = stop_lat
                displayed_campaign["stop_lon"] = stop_lon
                displayed_campaign["duration"] = 8
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices
                
                displayed_campaigns.append(displayed_campaign)

                logging.info('finishing campaign two')
            except:
                logging.info('image loading failed, continuing')
                

            ###############################################################
            # Campaign Three

            logging.info('starting campaign three')
            displayed_campaign = {}

            try:
                start_lat = round(gpsd.fix.latitude, 4)
                start_lon = round(gpsd.fix.longitude, 4)
                displayed_campaign['fix'] = True
            except:
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            if start_lat == 0.0 or start_lat == 0.0 or math.isnan(start_lat) or math.isnan(start_lon):
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            logging.info('Converting speed')
            try:
                spdString = int((round(gpsd.fix.speed, 4) * 1.60934))
            except:
                spdString = 0

            if start_lat == 0.0 or start_lon == 0.0:
                dateString = '01-01-2019'
            else:
                dateString = str(gpsd.utc)
                dateString = dateString.replace('_', ' ')

            state['location'] = (start_lat, start_lon)
            state['last_location'] = state['location']
            state['speed'] = spdString

            logging.info('writing to gps log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_three - ' + dateString + '\n')
                f.write(str(start_lat) + ', ' + str(start_lon) + '\n')
                f.write(str(spdString) + 'kph\n')

            logging.info('trying to display image three')
            try:
                displayImage(campaign_three, 8, 'campaign_three', '3', (start_lat, start_lon))

                try:
                    stop_lat = round(gpsd.fix.latitude, 4)
                    stop_lon = round(gpsd.fix.longitude, 4)
                except:
                    stop_lat = start_lat
                    stop_lon = start_lon

                state['last_location'] = (stop_lat, stop_lon)    
                displayed_campaign["campaign_id"] = camp_three_id
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = start_lat
                displayed_campaign["start_lon"] = start_lon
                displayed_campaign["stop_lat"] = stop_lat
                displayed_campaign["stop_lon"] = stop_lon
                displayed_campaign["duration"] = 5
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices

                displayed_campaigns.append(displayed_campaign)
                logging.info('finishing campaign three')
            except:
                logging.info('image loading failed, continuing')
                


            ###############################################################
            # Campaign Four

            logging.info('starting campaign four')
            displayed_campaign = {}

            try:
                start_lat = round(gpsd.fix.latitude, 4)
                start_lon = round(gpsd.fix.longitude, 4)
                displayed_campaign['fix'] = True
            except:
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            if start_lat == 0.0 or start_lat == 0.0 or math.isnan(start_lat) or math.isnan(start_lon):
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            logging.info('Converting speed')
            try:
                spdString = int((round(gpsd.fix.speed, 4) * 1.60934))
            except:
                spdString = 0

            if start_lat == 0.0 or start_lon == 0.0:
                dateString = '01-01-2019'
            else:
                dateString = str(gpsd.utc)
                dateString = dateString.replace('_', ' ')

            state['location'] = (start_lat, start_lon)
            state['last_location'] = state['location']
            state['speed'] = spdString

            logging.info('writing to gps log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_four - ' + dateString + '\n')
                f.write(str(start_lat) + ', ' + str(start_lon) + '\n')
                f.write(str(spdString) + 'kph\n')

            logging.info('trying to display image four')
            try:
                displayImage(campaign_two, 8, 'campaign_two', '2', (start_lat, start_lon))

                try:
                    stop_lat = round(gpsd.fix.latitude, 4)
                    stop_lon = round(gpsd.fix.longitude, 4)
                except:
                    stop_lat = start_lat
                    stop_lon = start_lon

                state['last_location'] = (start_lat, start_lon)    
                displayed_campaign["campaign_id"] = camp_four_id
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = start_lat
                displayed_campaign["start_lon"] = start_lon
                displayed_campaign["stop_lat"] = stop_lat
                displayed_campaign["stop_lon"] = stop_lon
                displayed_campaign["duration"] = 8
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices

                displayed_campaigns.append(displayed_campaign)
                
                logging.info('finishing campaign four')
            except:
                logging.info('image loading failed, continuing')
                

            ###############################################################
            # Campaign Five

            logging.info('starting campaign five')
            displayed_campaign = {}

            try:
                start_lat = round(gpsd.fix.latitude, 4)
                start_lon = round(gpxd.fix.longitude, 4)
                displayed_campaign['fix'] = True
            except:
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            if start_lat == 0.0 or start_lat == 0.0 or math.isnan(start_lat) or math.isnan(start_lon):
                start_lat = state['last_location'][0]
                start_lon = state['last_location'][1]
                displayed_campaign['fix'] = False

            logging.info('Converting speed')
            try:
                spdString = int((round(gpsd.fix.speed, 4) * 1.60934))
            except:
                spdString = 0

            if start_lat == 0.0 or start_lon == 0.0:
                dateString = '01-01-2019'
            else:
                dateString = str(gpsd.utc)
                dateString = dateString.replace('_', ' ')

            state['location'] = (start_lat, start_lon)
            state['last_location'] = state['location']
            state['speed'] = spdString

            logging.info('writing to gps log')
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_three - ' + dateString + '\n')
                f.write(str(start_lat) + ', ' + str(start_lon) + '\n')
                f.write(str(spdString) + 'kph\n')

            logging.info('trying to display image five')
            try:
                displayImage(campaign_four, 16, 'campaign_four', '4', (start_lat, start_lon))

                try:
                    stop_lat = round(gpsd.fix.latitude, 4)
                    stop_lon = round(gpsd.fix.longitude, 4)
                except:
                    stop_lat = start_lat
                    stop_lon = start_lon

                state['last_location'] = (start_lat, start_lon)    
                displayed_campaign["campaign_id"] = camp_four_id
                displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                displayed_campaign["start_lat"] = start_lat
                displayed_campaign["start_lon"] = start_lon
                displayed_campaign["stop_lat"] = stop_lat
                displayed_campaign["stop_lon"] = stop_lon
                displayed_campaign["duration"] = 16
                displayed_campaign["speed"] = state['speed']
                displayed_campaign["RT_impressions"] = devices

                displayed_campaigns.append(displayed_campaign)
                logging.info('finishing campaign five')
            except:
                logging.info('image loading failed, continuing')
                


###################################################################################################################
        
            if internet():
                try:
                    this_lat = round(gpsd.fix.latitude, 4)
                    this_lon = round(gpsd.fix.longitude, 4)
                    this_date = str(gpsd.utc)
                    this_fix = True
                except:
                    this_lat = state['last_location'][0]
                    this_lon = state['last_location'][1]
                    this_fix = False

                if math.isnan(this_lat) or math.isnan(this_lon):
                    this_lat = state['last_location'][0]
                    this_lon = state['last_location'][1]
                    this_fix = False

                state['location'] = (this_lat, this_lon)

                # Write to last_location.txt
                with open('/home/pi/Code/adway-controller/last_location.txt', 'w') as f:
                    f.write(str(this_lat) + ' ' + str(this_lon))

                # Make sure you're logged in and have a token
                if state['login'] == 'OFF':
                    login(sysparam.user, sysparam.password, this_fix)
                    initializeDevice(sysparam.user, this_fix)

                logging.info('Have connection, uploading stats')
                url = base_url + '/get/content'

                stats = []
                for i in range(len(displayed_campaigns)):
                    stats.append(displayed_campaigns[i])

                sent_stats = json.dumps(stats)

                payload = '{"code": "' + token + '", "API_KEY": "' + api_key + '", "data": {"utc": "' + this_date + '", "fix": ' + str(this_fix).lower() + ', "lat": ' + str(this_lat) + ', "lon": ' + str(this_lon) + ', "cur_campaign": ' + str(state['current_campaign']) + ', "device_id": "' + state['device_id'] + '", "stats": ' + sent_stats + '}} '
                #print json.dumps(payload)
                logging.info(payload)

                response = requests.request('POST', url, data=payload, headers=header)
                #response = requests.request('POST', url, data=json.dumps(payload), headers=header)
                response_dict = json.loads(response.text)
                logging.info(str(response_dict))

                count += 1

            else:
                logging.info('No internet, continuing')
                

    except(KeyboardInterrupt, SystemExit):
        gpsp.running = False
        gpsp.join()
        
