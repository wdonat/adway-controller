import psutil
import time

fail_count = 0

while True:
    # Check running processes for feh
    for process in psutil.process_iter():
        if 'feh' in process.cmdline():
            fail_count = 0
            continue
        else:
            fail_count += 1

    if fail_count == 3:  # feh hasn't been running for 30 seconds
        for process in psutil.process_iter():
            if 'demo_controller' in process.cmdline():
                process.terminate()
            if 'freeze_check' in process.cmdline():
                process.terminate()  # kill this program
                
    # Wait 10 seconds and then check again    
    time.sleep(10)
        
