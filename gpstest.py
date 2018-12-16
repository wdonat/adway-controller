from gps import *
import threading
import time


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

if __name__ == '__main__':
    gpsp = GpsPoller()
    try:
        gpsp.start()

        while True:

            dateString = str(gpsd.utc)
            if gpsd.fix.latitude > 0:
                lat = "N"
            else:
                lat = "S"
                
            latString = str(abs(round(gpsd.fix.latitude, 2)))
            lonString = str(abs(round(gpsd.fix.longitude, 2)))
            spdString = str(abs(round(gpsd.fix.speed, 2)))
                
            print 'latitude; ', latString
            print 'latitude: ', str(gpsd.fix.latitude * 100)
            print 'longitude: ', lonString
            print 'longitude: ', str(gpsd.fix.longitude * 100)

            time.sleep(1)
    except(KeyboardInterrupt, SystemExit):
        gpsp.running = False
        gpsp.join()
        
        
