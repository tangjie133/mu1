

MAQUEEN_EXAMPLES = {
 "IR.py":{"description":"Read infrared value","code":'''
import necir
def cb(addr,cmd):
  print('addr=',hex(addr))
  print('cmd=',hex(cmd))
necir.init(16,cb)

while True:
  pass'''},

 "Music.py": {"description": "Play Nyan Nyan from meow planet", "code": '''import music
music.play(music.NYAN)'''},

"Ultrasound.py": {"description": "Reading ultrasound data", "code": '''
from microbit import *
import urm10
while True:
  a = urm10.read(1,2)
  print(a,'cm')
  sleep(1000)
'''},

"Line.py": {"description": "Line inspection", "code": '''
from microbit import *
import maqueen
while True:
    a = maqueen.line(1)
    print(a)
    sleep(1000)'''},

"Servo.py": {"description": "Steering gear control", "code": '''
from microbit import *
import maqueen
while True:
    maqueen.servo(1,0)
    sleep(1000)
    maqueen.servo(1,90)
    sleep(1000)
    maqueen.servo(1,180)
    sleep(1000)'''},

"motor.py": {"description": "motor control", "code": '''
from microbit import *
import maqueen
while True:
    maqueen.motor(0,255,0,0)
    sleep(1000)
    maqueen.motor(0,0,0,255)
    sleep(1000)
    maqueen.motor(1,255,1,0)
    sleep(1000)
    maqueen.motor(1,0,1,255)
    sleep(1000)'''},
}
