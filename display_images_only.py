# Get images in one directory
# feh in that directory
import time
import psutil
import os

def displayImage(img_dir, dur):

    # Display image
    os.system('feh --hide-pointer -x -q -B black -g 1280x720 ' + img_dir + ' &')
    time.sleep(dur)

    # Clear image
    for process in psutil.process_iter():
        if 'feh' in process.cmdline():
            process.terminate()
    return


if __name__ == '__main__':

    JP = '/home/wolf/ADWAY/JP'
    AD = '/home/wolf/ADWAY/AD'
    logo = '/home/wolf/ADWAY/logo'
    AA = '/home/wolf/ADWAY/AA'
    web = '/home/wolf/ADWAY/web'

    while True:

        displayImage(JP, 10)
        displayImage(AD, 8)
        displayImage(web, 8)
        displayImage(AA, 8)
        displayImage(web, 15)
            
