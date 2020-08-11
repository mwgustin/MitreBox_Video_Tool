import RPi.GPIO as GPIO
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from os import listdir
from os.path import isfile, join
import os
import signal
import subprocess


vidPath = '/home/pi/videos'
onlyfiles = [f for f in listdir(vidPath) if isfile(join(vidPath, f))]


IP = ""

class MenuItem(object):
    def __init__(self, text, action):
        self.text = text
        self.action = action

class Menu(object):
    selectedIndex = 0
    padding = 5

    def __init__(self, options, display):
        self.options = options
        self.disp = display
        
        self.disp.begin()
        self.disp.clear()
        self.disp.display()
        self.image = Image.new('1', (disp.width, disp.height))

        self.draw = ImageDraw.Draw(self.image)
        self.draw.rectangle((self.padding,self.padding,disp.width, disp.height), outline=0, fill=0)
        self.font = ImageFont.load_default()

    def dispEmpty(self):
        self.draw.rectangle((0,0,disp.width, disp.height), outline=0, fill=0)

    def nav(self, direction):
        if(direction == "Right" and self.selectedIndex < (len(self.options)-1)):
            self.selectedIndex += 1
            self.display()

        elif(direction == "Left" and self.selectedIndex > 0 ):
            self.selectedIndex -= 1
            self.display()

    def display(self):
        self.disp.clear()
        self.dispEmpty()
        self.draw.text((self.padding,self.padding), self.options[self.selectedIndex].text, font=self.font, fill=255)
        self.disp.image(self.image)
        self.disp.display()

    def select(self):
        #feedback
        self.draw.text((self.padding,self.padding + 30), "executing....", font=self.font, fill = 255)
        self.disp.image(self.image)
        self.disp.display()
        
        #execute
        self.options[self.selectedIndex].action()



class Player():

    def __init__(self, path):
        self.path = path
        self.process = None

    def loop(self):
        path = self.path
        self.process = subprocess.Popen(['omxplayer', '-b', '--no-osd', '--loop', path], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    def play(self):
        path = self.path
        self.process = subprocess.Popen(['omxplayer', '-b', '--no-osd', path], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    def status(self):
        if self.process.poll() is not None:
            return 'done'
        else:
            return 'playing'

    def stop(self):
        self.process.stdin.write(b'q')
        self.process.stdin.flush()

    def kill(self):
        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def toggle(self):
        self.process.stdin.write(b'p')
        self.process.stdin.flush()


# Input pins:
L_pin = 27 
R_pin = 23 
C_pin = 4 
U_pin = 17 
D_pin = 22 

A_pin = 6
B_pin = 5 


GPIO.setmode(GPIO.BCM) 

GPIO.setup(A_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(B_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(L_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(R_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(U_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(D_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(C_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up



#pin config
RST = None
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0


disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

player = Player('')
loopProcess = None

def play():
    global player
    killLoop()
    killPlay()
    selectedFile = vidPath + "/" + vidMenu.options[vidMenu.selectedIndex].text
    print "playing: " + selectedFile
    player.path = selectedFile
    player.loop()

def killPlay():
    if (player.process != None):
        player.stop()
        # player.kill()
        player.process.kill()
        player.process = None

def showVidMenu():
    global activeMenu
    activeMenu = vidMenu
    activeMenu.display()

def showDeviceInfo():
    global activeMenu
    activeMenu = deviceInfoMenu
    activeMenu.display()

def killOMXPlayer():
    try:
        omxID = subprocess.check_output("pidof omxplayer.bin", shell=True)
        omxArray = omxID.strip().split()
        subprocess.Popen(buildKillCMD(omxArray))
    except subprocess.CalledProcessError as err:
        print err

def buildKillCMD(args):
    cmd = ['kill']
    for i in args:
        cmd.append(i)
    return cmd


def killLoop():
    global loopProcess
    if(loopProcess):
        loopProcess.kill()
    killOMXPlayer()

def loopVid():
    killPlay()
    global loopProcess
    killLoop()
    loopProcess = subprocess.Popen(['bash', '/home/pi/startvideo.sh'], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

def nullFunc():
    pass

def getIP():
    global IP
    cmd = "hostname -I | cut -d\' \' -f1"
    IP = subprocess.check_output(cmd, shell = True)
    deviceInfoMenu.options[0] = MenuItem("IP: " + str(IP), nullFunc)

def getHDMIInfo():
    global disp
    try:
        cmd = "tvservice -s"
        hdmiInfo = subprocess.check_output(cmd, shell = True)
        cmd = "tvservice -audio"
        audioInfo = subprocess.check_output(cmd, shell = True)
        cmd = "tvservice -name"
        dispName = subprocess.check_output(cmd, shell=True)

        hdmiInfoScroll(hdmiInfo,audioInfo,dispName)

        
    except subprocess.CalledProcessError as err:
        print err

def hdmiInfoScroll(hdmi, audio, name):
    global breakScroll
    maxLen = len(hdmi)
    if(len(audio) > maxLen):
        maxLen = len(audio)
    if(len(name) > maxLen):
        maxLen = len(name)
    
    for i in range(maxLen-20):
        activeMenu.disp.clear()
        activeMenu.dispEmpty()
        activeMenu.draw.text((activeMenu.padding, activeMenu.padding), hdmi[i:i+20], font=activeMenu.font, fill=255)
        activeMenu.draw.text((activeMenu.padding, activeMenu.padding+10), audio[i:i+20], font=activeMenu.font, fill=255)
        activeMenu.draw.text((activeMenu.padding, activeMenu.padding+20), name[i:i+20], font=activeMenu.font, fill=255)
        activeMenu.disp.image(activeMenu.image)
        activeMenu.disp.display()
        time.sleep(.05)
    
    activeMenu.disp.clear()
    activeMenu.dispEmpty()
    activeMenu.draw.text((activeMenu.padding, activeMenu.padding), hdmi, font=activeMenu.font, fill=255)
    activeMenu.draw.text((activeMenu.padding, activeMenu.padding+10), audio, font=activeMenu.font, fill=255)
    activeMenu.draw.text((activeMenu.padding, activeMenu.padding+20), name, font=activeMenu.font, fill=255)
    activeMenu.disp.image(activeMenu.image)
    activeMenu.disp.display()



# ------- menus--------
#main menu
mainMenuOptions = [ 
    MenuItem("Loop all", loopVid), 
    MenuItem("Play Specific File", showVidMenu),  
    MenuItem("HDMI Info", getHDMIInfo), 
    MenuItem("Device Info", showDeviceInfo)]
mainMenu = Menu(mainMenuOptions, disp)
mainMenu.display()
activeMenu = mainMenu

#vid menu
vidMenuOptions = []
for vid in onlyfiles:
    vidMenuOptions.append(MenuItem(vid, play))
vidMenu = Menu(vidMenuOptions, disp)

#device info menu
devInfoMenuItem = MenuItem("IP: " + str(IP), nullFunc)
deviceInfoMenu = Menu([devInfoMenuItem], disp)


def nav(channel):
    global mainMenu
    global activeMenu
    if(channel == C_pin or channel == A_pin):
        activeMenu.select()
    if(channel == B_pin): #revert to standard menu
        activeMenu = mainMenu
        activeMenu.display()
    if(channel == L_pin):
        activeMenu.nav("Left")
    if(channel == R_pin):
        activeMenu.nav("Right")



GPIO.add_event_detect(L_pin, GPIO.RISING, callback=nav)
GPIO.add_event_detect(R_pin, GPIO.RISING, callback=nav)
GPIO.add_event_detect(C_pin, GPIO.RISING, callback=nav)
GPIO.add_event_detect(A_pin, GPIO.RISING, callback=nav)
GPIO.add_event_detect(B_pin, GPIO.RISING, callback=nav)

mainMenu.display()
loopVid()

while True:
    getIP()
    time.sleep(5)
