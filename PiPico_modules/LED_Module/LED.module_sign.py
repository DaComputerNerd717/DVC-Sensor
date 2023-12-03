#sign.py, LED module
# Import modules
import network
import urequests
from machine import Pin, ADC
import time
import gc
led = machine.Pin("LED", machine.Pin.OUT)
strobe = Pin(1, Pin.OUT, Pin.PULL_DOWN)
led.off()
SensorID = 3
ServerAddress = "10.42.0.1"
# Connect to WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("deer", "SaveTheDeer")
time.sleep(3)
print(wlan.ifconfig())
BootTimer = 0
ErrorCount = 0
while True:
    print(wlan.ifconfig())
    print(BootTimer)
    if BootTimer >= 3600: #Reboot once an hour
        print("Hourly Reboot in progress")
        led.on()
        machine.reset()
    gc.collect()
    try:
        response = urequests.get('http://'+ServerAddress+':5000/sensor3')
        data = response.json()
        print(data['status'])
        if data['status'] == "on":
            led.on()
        if data['status'] == "off":
            led.off()
    except Exception as E:
        ErrorCount += 1
        print("Server not responding: \n",E,ErrorCount)
        if ErrorCount > 30:
            led.on()
            machine.reset()

        pass
    time.sleep(1)
    BootTimer += 1
