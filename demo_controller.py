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

from picamera import PiCamera
from gps import *
import threading
from bluepy.btle import Scanner, DefaultDelegate

global camera_exists

try:
    camera = PiCamera()
    camera_exists = 1
except:
    camera_exists = 0

global token
global device_token
global arch

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
    global state
    state['login'] = 'OFF'
    state['location'] = (34.0368, -118.4499)
    state['last_location'] = (34.0368, -118.4499)
    state['speed'] = 0
    state['current_campaign'] = 0
    state['device_id'] = device_id
    return


def displayImage(img_dir, dur, adv, camp, loc):
    global arch
    global camera_exists

    # Display image
    os.system('feh --hide-pointer -x -q -B black -g 1280x720 ' + img_dir + ' &')
    if arch == 'x86_64':
        time.sleep(dur)
    else:
        if camera_exists == 1:
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


def main():
    return

if __name__ == '__main__':
    global arch
    arch = platform.machine()

    gpsp = GpsPoller()
    campaign_one = '/home/pi/ADWAY/campaign_one'
    camp_one_dur = 10
    camp_one_id = '1'
    campaign_two = '/home/pi/ADWAY/campaign_two'
    camp_two_dur = 10
    camp_two_id = '2'
    campaign_three = '/home/pi/ADWAY/campaign_three'
    camp_three_dur = 10
    camp_three_id = '3'
    campaign_four = '/home/pi/ADWAY/campaign_four'
    camp_four_dur = 10
    camp_four_id = '4'

    global state
    global active_campaigns
    global displayed_campaigns
    global offline_campaigns

    print 'initiating state'
    initiateState()

    print 'logging in'
    login(sysparam.user, sysparam.password, state['location'])

    print 'initializing device'
    initializeDevice(sysparam.user, state['location'])

    try:
        gpsp.start() 
        while True:
        	displayed_campaigns = []

            if gpsd.fix.latitude > 0:
                lat = 'N'
            else:
                lat = 'S'
            latString = abs(round(gpsd.fix.latitude, 4))
            lonString = round(gpsd.fix.longitude, 4)

            displayed_campaign = {}
            displayed_campaign['fix'] = True

            if latString == 0.0 or lonString == 0.0:
                latString = state['last_location'][0]
                lonString = state['last_location'][1]
                displayed_campaign['fix'] = False

            try:
            	spdString = int((round(gpsd.fix.speed, 4) * 1.60934))  # Converting MPH to KPH
            except:
            	spdString = 0

            dateString = str(gpsd.utc)
            dateString = dateString.replace('_', ' ')
            state['location'] = (latString, lonString)
            state['last_location'] = state['location']
            state['speed'] = spdString

            try:
	            scanner = Scanner().withDelegate(ScanDelegate())
    	        devices = len(scanner.scan(2.0))
    	    except:
    	    	devices = 1

    	    with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_one - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
            displayImage(campaign_one, 10, 'campaign_one', '1', (latString, lonString))

		    displayed_campaign["campaign_id"] = camp_one_id
		    displayed_campaign["lat"] = state['location'][0]
		    displayed_campaign["lon"] = state['location'][1]
		    displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		    displayed_campaign["start_lat"] = state['location'][0]
		    displayed_campaign["start_lon"] = state['location'][1]
		    displayed_campaign["stop_lat"] = state['location'][0]
		    displayed_campaign["stop_lon"] = state['location'][1]
		    displayed_campaign["duration"] = camp_one_dur
		    displayed_campaign["speed"] = state['speed']
		    displayed_campaign["RT_impressions"] = devices

		    displayed_campaigns.append(displayed_campaign)



            ###############################################################
            displayed_campaign = []
            displayed_campaign['fix'] = True

            latString = abs(round(gpsd.fix.latitude, 4))
            lonString = round(gpsd.fix.longitude, 4)
            if latString == 0.0 or lonString == 0.0:
                latString = state['last_location'][0]
                lonString = state['last_location'][1]
                displayed_campaign['fix'] = False

            try:
            	spdString = int((round(gpsd.fix.speed, 4) * 1.60934))  # Converting MPH to KPH
            except:
            	spdString = 0

            dateString = str(gpsd.utc)
            dateString = dateString.replace('_', ' ')
            state['location'] = (latString, lonString)
            state['last_location'] = state['location']
            state['speed'] = spdString

            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_two - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
            displayImage(campaign_two, 10, 'campaign_two', '2', (latString, lonString))

		    displayed_campaign["campaign_id"] = camp_two_id
		    displayed_campaign["lat"] = state['location'][0]
		    displayed_campaign["lon"] = state['location'][1]
		    displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		    displayed_campaign["start_lat"] = state['location'][0]
		    displayed_campaign["start_lon"] = state['location'][1]
		    displayed_campaign["stop_lat"] = state['location'][0]
		    displayed_campaign["stop_lon"] = state['location'][1]
		    displayed_campaign["duration"] = camp_two_dur
		    displayed_campaign["speed"] = state['speed']
		    displayed_campaign["RT_impressions"] = devices

		    displayed_campaigns.append(displayed_campaign)



            ###############################################################
            displayed_campaign = {}
            displayed_campaign['fix'] = True

            latString = abs(round(gpsd.fix.latitude, 4))
            lonString = round(gpsd.fix.longitude, 4)
            if latString == 0.0 or lonString == 0.0:
                latString = state['last_location'][0]
                lonString = state['last_location'][1]
                displayed_campaign['fix'] = False

            try:
            	spdString = int((round(gpsd.fix.speed, 4) * 1.60934))  # Converting MPH to KPH
            except:
            	spdString = 0

            dateString = str(gpsd.utc)
            dateString = dateString.replace('_', ' ')
            state['location'] = (latString, lonString)
            state['last_location'] = state['location']
            state['speed'] = spdString

            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_three - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
            displayImage(campaign_three, 10, 'campaign_three', '3', (latString, lonString))

		    displayed_campaign["campaign_id"] = camp_three_id
		    displayed_campaign["lat"] = state['location'][0]
		    displayed_campaign["lon"] = state['location'][1]
		    displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		    displayed_campaign["start_lat"] = state['location'][0]
		    displayed_campaign["start_lon"] = state['location'][1]
		    displayed_campaign["stop_lat"] = state['location'][0]
		    displayed_campaign["stop_lon"] = state['location'][1]
		    displayed_campaign["duration"] = camp_three_dur
		    displayed_campaign["speed"] = state['speed']
		    displayed_campaign["RT_impressions"] = devices

		    displayed_campaigns.append(displayed_campaign)



            ###############################################################
            displayed_campaign = {}
            displayed_campaign['fix'] = True

            latString = abs(round(gpsd.fix.latitude, 4))
            lonString = round(gpsd.fix.longitude, 4)
            if latString == 0.0 or lonString == 0.0:
                latString = state['last_location'][0]
                lonString = state['last_location'][1]
                displayed_campaign['fix'] = False

            try:
            	spdString = int((round(gpsd.fix.speed, 4) * 1.60934))  # Converting MPH to KPH
            except:
            	spdString = 0

            dateString = str(gpsd.utc)
            dateString = dateString.replace('_', ' ')
            state['location'] = (latString, lonString)
            state['last_location'] = state['location']
            state['speed'] = spdString

            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(devices) + '\n')
                f.write('campaign_four - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
            displayImage(campaign_four, 10, 'campaign_four', '4', (latString, lonString))

            displayed_campaign = {}

		    displayed_campaign["campaign_id"] = camp_four_id
		    displayed_campaign["lat"] = state['location'][0]
		    displayed_campaign["lon"] = state['location'][1]
		    displayed_campaign["time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		    displayed_campaign["start_lat"] = state['location'][0]
		    displayed_campaign["start_lon"] = state['location'][1]
		    displayed_campaign["stop_lat"] = state['location'][0]
		    displayed_campaign["stop_lon"] = state['location'][1]
		    displayed_campaign["duration"] = camp_four_dur
		    displayed_campaign["speed"] = state['speed']
		    displayed_campaign["RT_impressions"] = devices

		    displayed_campaigns.append(displayed_campaign)


###################################################################################################################
        
            if internet():
                print 'Have connection, uploading stats'

               	url = base_url + '/get/content'

			    stats = []
    			for i in range(len(displayed_campaigns)):
        			stats.append(displayed_campaigns[i])

			    sent_stats = str(stats)
			    sent_stats = sent_stats.replace("'", '"')

			    payload = '{"user": "' + sysparam.user + '", "code": "' + token + '", "API_KEY": "' + api_key + '", "data": {"lat":' + str(state['location'][0]) + ', "lon": ' + str(state['location'][1]) + ', "cur_campaign": ' + str(state['current_campaign']) + ', "device_id": "' + state['device_id'] + '", "projector_left": 325, "projector_right": 326, "stats": ' + sent_stats + '}} '

			    response = requests.request('POST', url, data=payload, headers=header)

			else:
				continue

    except(KeyboardInterrupt, SystemExit):
        gpsp.running = False
        gpsp.join()
        
