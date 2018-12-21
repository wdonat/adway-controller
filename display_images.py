# Get images in one directory
# feh in that directory

import time
import psutil
import os
from gps import *
import threading

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

def displayImage(img_dir, dur):
    # Display image
    os.system('feh --hide-pointer -x -q black -g 1366x768 ' + img_dir + ' &')
    time.sleep(dur)

    # Clear image
    for process in psutil.process_iter():
        if 'feh' in process.cmdline():
            process.terminate()
    return


if __name__ == '__main__':
    gpsp = GpsPoller()
    JP = os.path.expanduser('~/ADWAY/JP')
    AD = os.path.expanduser('~/ADWAY/AD')
    logo = os.path.expanduser('~/ADWAY/logo')
    AA = os.path.expanduser('~/ADWAY/AA')
    web = os.path.expanduser('~/ADWAY/web')
    try:
        gpsp.start()
        while True:

            if gpsd.fix.latitude > 0:
                lat = 'N'
            else:
                lat = 'S'
            latString = str(abs(round(gpsd.fix.latitude, 2)))
            lonString = str(abs(round(gpsd.fix.longitude, 2)))
            dateString = str(gpsd.utc)
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('JP - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
            displayImage(JP, 8)

            latString = str(abs(round(gpsd.fix.latitude, 2)))
            lonString = str(abs(round(gpsd.fix.longitude, 2)))
            dateString = str(gpsd.utc)
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('AD - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
            displayImage(AD, 10)

            latString = str(abs(round(gpsd.fix.latitude, 2)))
            lonString = str(abs(round(gpsd.fix.longitude, 2)))
            dateString = str(gpsd.utc)
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('logo - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
            displayImage(logo, 5)

            latString = str(abs(round(gpsd.fix.latitude, 2)))
            lonString = str(abs(round(gpsd.fix.longitude, 2)))
            dateString = str(gpsd.utc)
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('AA - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
            displayImage(AA, 10)

            latString = str(abs(round(gpsd.fix.latitude, 2)))
            lonString = str(abs(round(gpsd.fix.longitude, 2)))
            dateString = str(gpsd.utc)
            with open('/home/pi/ADWAY/gps.txt', 'a') as f:
                f.write('web - ' + dateString + '\n')
                f.write(latString + ', ' + lonString + '\n')
            displayImage(web, 15)
            
    except(KeyboardInterrupt, SystemExit):
        gpsp.running = False
        gpsp.join()
            
