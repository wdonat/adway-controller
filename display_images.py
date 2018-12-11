# Get images in one directory
# feh in that directory

import time
import psutil
import os

def displayImage(img_dir, dur):
  # Display image
  os.system('feh --hide-pointer -x -q black -g 1366x768 ' + img_dir + ' &')
  time.sleep(dur)

  # Clear image
  for process in psutil.process_iter():
    if 'feh' in process.cmdline():
      process.terminate()
  return

def main():

  images = ['JP', 'AD', 'logo', 'AA', 'web', 'lakers']
  JP = os.path.expanduser('~/ADWAY/JP')
  AD = os.path.expanduser('~/ADWAY/AD')
  logo = os.path.expanduser('~/ADWAY/logo')
  AA = os.path.expanduser('~/ADWAY/AA')
  web = os.path.expanduser('~/ADWAY/web')
  lakers = os.path.expanduser('~/ADWAY/lakers')

  while True:
      displayImage(JP, 8)
      displayImage(AD, 10)
      displayImage(logo, 5)
      displayImage(AA, 10)
      displayImage(web, 15)
      displayImage(lakers, 8)


if __name__ == '__main__':
  main()
