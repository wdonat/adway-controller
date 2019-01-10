# Get images in one directory
# feh in that directory

import time
import psutil
import os
from gps import *
import threading
import platform
from bluepy.btle import Scanner, DefaultDelegate

global arch

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

def displayImage(img_dir, dur, adv, camp, loc):
    global arch
    # Display image
    os.system('feh --hide-pointer -x -q -B black -g 1280x720 ' + img_dir + ' &')
    if arch == 'x86_64':
        time.sleep(dur)
    else:
        time.sleep(dur/2)
        takePhoto(adv, camp, loc)
        time.sleep(dur/2)

    # Clear image
    for process in psutil.process_iter():
        if 'feh' in process.cmdline():
            process.terminate()
    return

def takePhoto(advertiser, campaign, location):
    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.start_preview()  # perhaps not necessary?
    # See if correct directory exists; if not, create it:
    if not os.path.exists(sysparam.image_dir + '/' + advertiser):
        os.makedirs(sysparam.image_dir + '/' + advertiser)
    camera.capture(sysparam.image_dir + '/' + advertiser + '/' + str(campaign) + '_' + str(location[0]) + '_' +
                   str(location[1]) + datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S') + '.jpg')
    return


if __name__ == '__main__':
    global arch

    gpsp = GpsPoller()
    JP = '/home/pi/ADWAY/JP'
    AD = '/home/pi/ADWAY/AD'
    logo = '/home/pi/ADWAY/logo'
    AA = '/home/pi/ADWAY/AA'
    web = '/home/pi/ADWAY/web'
    arch = platform.machine()

    try:
        gpsp.start()
        while True:

            if gpsd.fix.latitude > 0:
                lat = 'N'
            else:
                lat = 'S'
            latString = str(abs(round(gpsd.fix.latitude, 4)))
            lonString = str(round(gpsd.fix.longitude, 4))
            spdString = str(round(gpsd.fix.speed, 4) * 1.60934)  # Converting MPH to KPH
            dateString = str(gpsd.utc)

            scanner = Scanner().withDelegate(ScanDelegate())
            devices = scanner.scan(2.0)
  
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('Devices - ' + str(len(devices)) + '\n')
                f.write('JP - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
            displayImage(JP, 8, 'JP', '1', (latString, lonString))

            latString = str(abs(round(gpsd.fix.latitude, 4)))
            lonString = str(round(gpsd.fix.longitude, 4))
            dateString = str(gpsd.utc)
            spdString = str(round(gpsd.fix.speed, 4) * 1.60934)  # Converting MPH to KPH
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('AD - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
            displayImage(AD, 10, 'AD', '1', (latString, lonString))

            latString = str(abs(round(gpsd.fix.latitude, 4)))
            lonString = str(round(gpsd.fix.longitude, 4))
            dateString = str(gpsd.utc)
            spdString = str(round(gpsd.fix.speed, 4) * 1.60934)  # Converting MPH to KPH
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('logo - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
            displayImage(logo, 5, 'logo', '1', (latString, lonString))

            latString = str(abs(round(gpsd.fix.latitude, 4)))
            lonString = str(round(gpsd.fix.longitude, 4))
            dateString = str(gpsd.utc)
            spdString = str(round(gpsd.fix.speed, 4) * 1.60934)  # Converting MPH to KPH
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('AA - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
            displayImage(AA, 10, 'AA', '1', (latString, lonString))

            latString = str(abs(round(gpsd.fix.latitude, 4)))
            lonString = str(round(gpsd.fix.longitude, 4))
            dateString = str(gpsd.utc)
            spdString = str(round(gpsd.fix.speed, 4) * 1.60934)  # Converting MPH to KPH
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('web - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
                f.write(spdString + 'kph\n')
                f.write('\n')
            displayImage(web, 15, 'web', '1', (latString, lonString))
            
    except(KeyboardInterrupt, SystemExit):
        gpsp.running = False
        gpsp.join()
            
