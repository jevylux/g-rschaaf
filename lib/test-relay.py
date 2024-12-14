from machine import Pin
import time

relay = Pin(16, Pin.OUT)


while True:
    relay.high()
    time.sleep(2)
    relay.low()
    time.sleep(2)
    