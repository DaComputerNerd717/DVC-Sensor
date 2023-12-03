# Sensor2, main.py
# Import modules
import network
import urequests
from machine import Pin, ADC
import time
import gc

led = machine.Pin("LED", machine.Pin.OUT)
PirSensor = Pin(1, Pin.IN, Pin.PULL_DOWN)
led.off()
SensorID = 2
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
    print(PirSensor.value())
    if BootTimer >= 3600: #Reboot once an hour
        print("Hourly Reboot in progress")
        led.on()
        machine.reset()
    gc.collect()
    print("waiting")
    try:
        if PirSensor.value() == 1: # status of PIR output
            led.on()
            print("motion detected") # print the response
            print('http://'+ServerAddress+':5000/sensor'+str(SensorID)+'/YES')
            response = urequests.get('http://'+ServerAddress+':5000/sensor'+str(SensorID)+'/YES')
        else:
            led.off()
            print("no motion")
            print('http://'+ServerAddress+':5000/sensor'+str(SensorID)+'/NO')
            response = urequests.get('http://'+ServerAddress+':5000/sensor'+str(SensorID)+'/NO')
        data = response.json()
        print(data['status'])
    except Exception as E:
        ErrorCount += 1
        print("Server not responding: \n",E,ErrorCount)
        if ErrorCount > 60:
            led.on()
            machine.reset()
    time.sleep(1)
    BootTimer += 1
