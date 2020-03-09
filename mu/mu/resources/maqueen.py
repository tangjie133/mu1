import math
import ustruct
from time import sleep
from microbit import *

I2caddr = 0x10

def motor(direction1, speed1, direction2, speed2):
    buf = bytearray(5)
    buf[0] = 0x00
    buf[1] = direction1
    buf[2] = speed1
    buf[3] = direction2
    buf[4] = speed2
    i2c.write(I2caddr, buf)

def servo(index,angle):

    if(index == 1):
        buf =bytearray(2)
        buf[0]=0x14
        buf[1]=angle
        i2c.write(I2caddr, buf)
    if(index == 2):
        buf =bytearray(2)
        buf[0]=0x15
        buf[1]=angle
        i2c.write(I2caddr, buf)

def line(index):
    if(index == 1):
        a=pin13.read_digital()
        return a
    if(index == 2):
        a=pin14.read_digital()
        return a