# Complete project details at https://RandomNerdTutorials.com

from machine import Pin, SoftI2C, RTC
from pico_i2c_lcd import I2cLcd
from picozero import Button
import time
import utime
#https://github.com/micropython/micropython-lib/blob/master/micropython/net/ntptime/ntptime.py
import requests
import network
import dht 
import secrets

# Define the LCD I2C address and dimensions
I2C_ADDR = 0x27
I2C_NUM_ROWS = 4
I2C_NUM_COLS = 20

# initialize DHT11 Sensor, Buttons, Buzzer and relay
setTimer = Button(21)
setTemp = Button(20)
buttonUp = Button(19)
buttonDown = Button(18)
sensor = dht.DHT11(Pin(17))
relay = Pin(16, Pin.OUT)
buzzer = Pin(15, Pin.OUT)
buzzer.low()

# initialize different values
buttonpressed = 0
timerbuttonpressed = False
temperaturebuttonpressed = False
temperatureSet = 24
timerSet = 0 # timervalue in seconds
temperatureIsSet = False 
timerIsSet = False
isBuzzer = False
once = True
relay.high() # turn heater on

# buzzer test
buzzer.low()
time.sleep(1)
buzzer.high()
time.sleep(1)
buzzer.low()
#Relay test
relay.high()
time.sleep(1)
relay.low()
# functions related to buttons

def setTimerFunc():
   global timerbuttonpressed, timerIsSet, timerSet,normalLoop, oldtime
   # first Presse the button to ask to set the timer
   # second press starts the timer
   if timerbuttonpressed:
      # button already pressed, start the timer
      timerIsSet = True
      timerbuttonpressed = False
      normalLoop = True
      oldtime = utime.time()
   else:
      timerbuttonpressed = True
      normalLoop = False
      timerSet = 0
   print("Timerbutton pressed")
def setTempFunc():
   global temperaturebuttonpressed,temperatureIsSet, temperatureSet, normalLoop
   if temperaturebuttonpressed:
      temperatureIsSet = True
      temperaturebuttonpressed = False
      normalLoop = True
   else:
      normalLoop = False
      temperaturebuttonpressed = True
      temperatureSet = 24
   print("Tempbutton pressed")
   pass
def buttonUpFunc():
   global timerbuttonpressed, timerSet, temperatureSet
   if timerbuttonpressed:
      timerSet = timerSet + 60
   if temperaturebuttonpressed:
      temperatureSet = temperatureSet+1
   print("Upbutton pressed")
def buttonDownFunc():
   global timerbuttonpressed, timerSet, temperatureSet, isBuzzer, timerIsSet
   if isBuzzer:
      isBuzzer = False
      timerIsSet = False
      return
   if timerbuttonpressed:
      timerSet = timerSet - 60
   if temperaturebuttonpressed:
      temperatureSet = temperatureSet - 1
   print("Downbutton pressed")
# define functons to call when buttons pressed
setTimer.when_pressed = setTimerFunc
setTemp.when_pressed = setTempFunc
buttonUp.when_pressed = buttonUpFunc
buttonDown.when_pressed = buttonDownFunc

# Initialize I2C and LCD objects
i2c = SoftI2C(sda=Pin(4), scl=Pin(5), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
lcd.putstr("Initialising")
time.sleep(1)
lcd.clear()
lcd.putstr("Connecting to wifi..")
# Initialize network and network time protovol

# wifi connection
wifi = network.WLAN(network.STA_IF) # station mode
wifi.active(True)
wifi.connect(secrets.ssid, secrets.pw)

# wait for connection
while not wifi.isconnected():
   lcd.move_to(0,1)
   lcd.putstr("Trying..")
   time.sleep(1)
   lcd.move_to(0,1)
   lcd.putstr("Waiting..")

print(wifi.ifconfig()[0])
# wifi connected
lcd.clear()
lcd.putstr("Connected. IP: "+str(wifi.ifconfig()[0]))

rtc = RTC()
while True:
   try:
      response = requests.get("http://worldtimeapi.org/api/timezone/Europe/Luxembourg")
      if response.status_code == 200:
         jsonresp = response.json()
         print(jsonresp)
         day_of_week = int(jsonresp["day_of_week"])
         jsonresp = jsonresp["datetime"]
         # now we have to to format the data in order to use it 
         y = int(jsonresp[:4])
         m = int(jsonresp[5:7])
         d = int(jsonresp[8:10])
         hr = int(jsonresp[11:13])
         minute = int(jsonresp[14:16])
         sec = int(jsonresp[17:19])
         z = time.mktime((y, m, d, hr, minute, sec, 0, 0))  # time in seconds since epoch
         print(z)
         rtc.datetime((y, m, d, day_of_week,hr, minute, sec, 0))
         break
      else:
         time.sleep(1)     
   except Exception as e:
      print('Failed to get API Time.')
# initialize input and output 

# main loop

oldtime = utime.time()
normalLoop = True  # normal loops, is displaying info
while True:
   if normalLoop:
      try:
         if timerIsSet and timerSet > 0:
            newtime = utime.time()
            timerSet = timerSet -(newtime-oldtime)
            if timerSet < 0:
               timerSet = 0
            oldtime = newtime
            if timerSet == 0:
               isBuzzer = True
         sensor.measure()
         temp = sensor.temperature()
         hum = sensor.humidity()
         year, month, day, hour, minute, second, weekday, yearday = utime.localtime()
         print("temp - ",temp,"tempset - ",temperatureSet)
         if  temp >= temperatureSet:
            relay.low()
            heatonoff = "OFF"
         else:
            relay.high()
            heatonoff = "ON"
         lcd.clear()
         lcd.move_to(0, 0)
         #lcd.putstr("Time: {}".format(time.strftime("%H:%M:%S %m:%d:%Y")))
         lcd.putstr(f"Time: {hour}:{minute}:{second}")
         # Starting at the second line (0, 1)
         lcd.move_to(0, 1)
         lcd.putstr("T: "+str(temp)+"C "+"- H: "+str(hum)+"% "+heatonoff)
         # Starting at the second line (0, 2)
         # Starting at the second line (0, 3)
         lcd.move_to(0, 2)
         if timerIsSet:
            yearT, monthT, dayT, hourT, minuteT, secondT, weekdayT, yeardayT  = time.localtime(timerSet)
            timerValue = str(hourT)+":"+str(minuteT)+":"+str(secondT)
         else:
            timerValue = "Not Set"
         if temperatureIsSet:
            tempValue = str(temperatureSet)
         else:
            tempValue = "Not Set"   
         lcd.putstr("Temp: "+str(tempValue))
         lcd.move_to(0, 3)
         lcd.putstr("Timer: "+str(timerValue))
         if isBuzzer:
            lcd.move_to(17, 3)
            lcd.putstr("!!")
         # now get the state of the buttons and set either temperature or timer and handle both
         # set buzzer if timer expired
         if isBuzzer:
            buzzer.high()
         else:
            buzzer.low()
         time.sleep(1)
         once = True
      except OSError as e:
         print('Failed to read sensor.')
   else:
      # exception loop
      if timerbuttonpressed: 
         if once:
            lcd.clear()
            lcd.move_to(0, 0)
            lcd.putstr("Set timer")
            lcd.move_to(0, 1)
            lcd.putstr("Green Button +1min")
            lcd.move_to(0, 2)
            lcd.putstr("Red Button -1min")
            lcd.move_to(0, 3)
            once = False
         lcd.move_to(0, 3)
         yearT, monthT, dayT, hourT, minuteT, secondT, weekdayT, yeardayT  = time.localtime(timerSet)
         lcd.putstr("Timer: "+str(hourT)+":"+str(minuteT)+":"+str(secondT))
      if temperaturebuttonpressed:
         if once:
            lcd.clear()
            lcd.move_to(0, 0)
            lcd.putstr("Set Temperature")
            lcd.move_to(0, 1)
            lcd.putstr("Green Button +1 Grad")
            lcd.move_to(0, 2)
            lcd.putstr("R   ed Button -1 Grad")
            once = False
         lcd.move_to(0, 3)
         lcd.putstr("Temperature : "+str(temperatureSet)+" Grad")

