from __future__ import print_function
import ast
import argparse
import sys
import os
import time
import os.path
import binascii

from serial.tools.list_ports import comports as list_serial_ports
from serial import Serial

COMMAND_LINE_FLAG = False  # Indicates running from the command line.

def find_pyb():
    ports = list_serial_ports()
    # riven, add pyb serial access
    for port in ports:
        if "VID:PID=F055:9800" in port[2].upper():
            return (port[0], port.serial_number)
    return (None, None)

def get_serial():
    """
    Detect if a micro:bit is connected and return a serial object to talk to
    it.
    """
    port, serial_number = find_pyb()
    if port is None:
        raise IOError('Could not find micro:bit.')
    return Serial(port, 115200, timeout=1, parity='N')

def raw_on(serial):
    """
    Puts the device into raw mode.
    """
    # Send CTRL-B to end raw mode if required.
    serial.write(b'\x02')
    # Send CTRL-C three times between pauses to break out of loop.
    for i in range(3):
        serial.write(b'\r\x03')
        time.sleep(0.01)
    # Flush input (without relying on serial.flushInput())
    n = serial.inWaiting()
    while n > 0:
        serial.read(n)
        n = serial.inWaiting()
    # Go into raw mode with CTRL-A.
    serial.write(b'\r\x01')
    # Flush
    data = serial.read_until(b'raw REPL; CTRL-B to exit\r\n>')
    if not data.endswith(b'raw REPL; CTRL-B to exit\r\n>'):
        if COMMAND_LINE_FLAG:
            print(data)
        raise IOError('Could not enter raw REPL.')
    # no soft reset on pyb

def raw_off(serial):
    """
    Takes the device out of raw mode.
    """
    serial.write(b'\x02')  # Send CTRL-B to get out of raw mode.


def execute(commands, serial):
    """
    Sends the command to the connected micro:bit via serial and returns the
    result. If no serial connection is provided, attempts to autodetect the
    device.

    For this to work correctly, a particular sequence of commands needs to be
    sent to put the device into a good state to process the incoming command.

    Returns the stdout and stderr output from the micro:bit.
    """
    close_serial = False
    if serial is None:
        serial = get_serial()
        close_serial = True
        time.sleep(0.1)
    result = b''
    raw_on(serial)
    time.sleep(0.1)
    # Write the actual command and send CTRL-D to evaluate.
    for command in commands:
        command_bytes = command.encode('utf-8')
        for i in range(0, len(command_bytes), 32):
            serial.write(command_bytes[i:min(i + 32, len(command_bytes))])
            time.sleep(0.01)
        serial.write(b'\x04')
        response = serial.read_until(b'\x04>')       # Read until prompt.
        try:
            out, err = response[2:-2].split(b'\x04', 1)  # Split stdout, stderr
            result += out
        except Exception as e:
            err = e
    time.sleep(0.1)
    raw_off(serial)
    if close_serial:
        serial.close()
        time.sleep(0.1)
    return result, err


