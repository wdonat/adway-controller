#!/usr/bin/python
from subprocess import Popen

while True:
	p = Popen("python /home/pi/Code/adway-controller/demo_controller.py", shell=True)
	p.wait()
