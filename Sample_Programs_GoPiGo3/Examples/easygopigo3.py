#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
from builtins import input

import sys
import tty
import select

import gopigo3

try:
    sys.path.insert(0, '/home/pi/Dexter/GoPiGo/Software/Python/line_follower')
    import line_sensor
    import scratch_line
    is_line_follower_accessible = True
except:
    try:
        sys.path.insert(0, '/home/pi/GoPiGo/Software/Python/line_follower')
        import line_sensor
        import scratch_line
        is_line_follower_accessible = True
    except:
        is_line_follower_accessible = False

old_settings = ''
fd = ''
##########################

read_is_open = True

def debug(in_str):
    if True:
        print(in_str)

def _wait_for_read():
    while read_is_open is False:
        time.sleep(0.01)

def _is_read_open():
    return read_is_open

def _grab_read():
    global read_is_open
    # print("grab")
    read_is_open = False

def _release_read():
    global read_is_open
    # print("release")
    read_is_open = True


class EasyGoPiGo3(gopigo3.GoPiGo3):
    def __init__(self):
        super(EasyGoPiGo3, self).__init__()
        self.sensor_1 = None
        self.sensor_2 = None
        self.set_speed(300)
        self.left_eye_color = (0,255,255)
        self.right_eye_color = (0,255,255)

    def volt(self):
        _wait_for_read()
        _grab_read()
        voltage = self.get_voltage_battery()
        _release_read()
        return voltage

    def set_speed(self,in_speed):
        try:
            self.speed = int(in_speed)
        except:
            self.speed = 300

    def get_speed(self):
        return int(self.speed)

    def stop(self):
        self.set_motor_dps(self.MOTOR_LEFT + self.MOTOR_RIGHT, 0)

    def forward(self):
        self.set_motor_dps(self.MOTOR_LEFT + self.MOTOR_RIGHT,
                             self.get_speed())
    def backward(self):
        self.set_motor_dps(self.MOTOR_LEFT + self.MOTOR_RIGHT,
                             self.get_speed()* -1)

    def left(self):
        self.set_motor_dps(self.MOTOR_LEFT, self.get_speed())
        self.set_motor_dps(self.MOTOR_RIGHT, 0)

    def right(self):
        self.set_motor_dps(self.MOTOR_LEFT, 0)
        self.set_motor_dps(self.MOTOR_RIGHT, self.get_speed())


    def set_light_sensor(self,port):
        sensor = LightSensor(self,port)
        if port == "AD1":
            self.sensor_1 = sensor
        elif port == "AD2":
            self.sensor_2 = sensor
        return sensor

    def blinker_on(self,id):
        if id == 1 or id == "left":
            self.set_led(self.LED_LEFT_BLINKER,255)
        if id == 0 or id == "right":
            self.set_led(self.LED_RIGHT_BLINKER,255)

    def blinker_off(self,id):
        if id == 1:
            self.set_led(self.LED_LEFT_BLINKER,0)
        if id == 0:
            self.set_led(self.LED_RIGHT_BLINKER,0)

    def led_on(self,id):
        self.blinker_on(id)


    def led_off(self,id):
        blinker_off(id)


    def set_left_eye_color(self,color):
        if isinstance(color,tuple) and len(color)==3:
            self.left_eye_color = color
        else:
            raise TypeError

    def set_right_eye_color(self,color):
        if isinstance(color,tuple) and len(color)==3:
            self.right_eye_color = color
        else:
            raise TypeError

    def set_eye_color(self,color):
        self.set_left_eye_color(color)
        self.set_right_eye_color(color)

    def open_left_eye(self):
        self.set_led(self.LED_LEFT_EYE,
                     self.left_eye_color[0],
                     self.left_eye_color[1],
                     self.left_eye_color[2],
                     )

    def open_right_eye(self):
        self.set_led(self.LED_RIGHT_EYE,
                     self.left_eye_color[0],
                     self.left_eye_color[1],
                     self.left_eye_color[2],
                     )

    def open_eyes(self):
        self.open_left_eye()
        self.open_right_eye()

    def close_left_eye(self):
        self.set_led(self.LED_LEFT_EYE, 0,0,0)

    def close_right_eye(self):
        self.set_led(self.LED_RIGHT_EYE, 0,0,0)

    def close_eyes(self):
        self.close_left_eye()
        self.close_right_eye()



    def turn_degrees(self,degrees):
        # get the starting position of each motor
        StartPositionLeft = self.get_motor_encoder(self.MOTOR_LEFT)
        StartPositionRight = self.get_motor_encoder(self.MOTOR_RIGHT)

        # the distance in mm that each wheel needs to travel
        WheelTravelDistance = ((self.WHEEL_BASE_CIRCUMFERENCE * degrees) / 360)

        # the number of degrees each wheel needs to turn
        WheelTurnDegrees = ((WheelTravelDistance / self.WHEEL_CIRCUMFERENCE) * 360)

        # Limit the speed
        self.set_motor_limits(self.MOTOR_LEFT + self.MOTOR_RIGHT, dps = self.get_speed())

        # Set each motor target
        self.set_motor_position(self.MOTOR_LEFT, (StartPositionLeft + WheelTurnDegrees))
        self.set_motor_position(self.MOTOR_RIGHT, (StartPositionRight - WheelTurnDegrees))


my_gpg = EasyGoPiGo3()
# these functions are here because we need direct access to these
# for the Drive functionality in Sam
def volt():
    return my_gpg.volt()

def stop():
    return my_gpg.stop()

def forward():
    my_gpg.forward()

def backward():
    my_gpg.backward()

def left():
    my_gpg.left()

def right():
    my_gpg.right()


#############################################################
# LIGHT SENSOR ONLY BELOW HAS BEEN PORTED TO GPG3
#############################################################

#############################################################
# the following is in a try/except structure because it depends
# on the date of gopigo.py
#############################################################
try:
    # TBD: these shouldn't be hardcoded
    PORTS = {"AD1": 0x03, "AD2": 0x0C,
             "SERIAL": -1, "I2C": -2}
except:
    PORTS = {"A1": 15, "D11": 10, "SERIAL": -1, "I2C": -2}


ANALOG = 1
DIGITAL = 0
SERIAL = -1
I2C = -2

##########################


class Sensor(object):
    '''
    Base class for all sensors
    Class Attributes:
        port : string - user-readable port identification
        portID : integer - actual port id
        pinmode : "INPUT" or "OUTPUT"
        pin : 1 for ANALOG, 0 for DIGITAL
        descriptor = string to describe the sensor for printing purposes
    Class methods:
        setPort / getPort
        setPinMode / getPinMode
        isAnalog
        isDigital
    '''
    def __init__(self, port, pinmode, gpg):
        '''
        port = one of PORTS keys
        pinmode = "INPUT", "OUTPUT", "SERIAL" (which gets ignored)
        '''
        debug("Sensor init")
        debug(pinmode)
        self.setPort(port)
        self.setPinMode(pinmode)
        self.gpg = gpg
        if pinmode == "INPUT":
            self.gpg.set_grove_type(self.portID,self.gpg.GROVE_TYPE.CUSTOM)
            self.gpg.set_grove_mode(self.portID,self.gpg.GROVE_INPUT_ANALOG)
        #or pinmode == "OUTPUT":
        #     gopigo.pinMode(self.getPortID(), self.getPinMode())

    def __str__(self):
        return ("{} on port {} \npinmode {}\nportID {}".format(self.descriptor,
                     self.getPort(), self.getPinMode(), self.portID))

    def setPin(self,pin):
        if self.port == "AD1":
            if pin == 1:
                self.pin = self.gpg.GROVE_1_1
            else:
                self.pin = self.gpg.GROVE_1_2
        else:
            if pin == 2:
                self.pin = self.gpg.GROVE_2_1
            else:
                self.pin = self.gpg.GROVE_2_2

    def getPin(self):
        return self.pin

    def setPort(self, port):
        self.port = port
        self.portID = PORTS[self.port]

    def getPort(self):
        return (self.port)

    def getPortID(self):
        return (self.portID)

    def setPinMode(self, pinmode):
        self.pinmode = pinmode

    def getPinMode(self):
        return (self.pinmode)

    def isAnalog(self):
        return (self.pin == ANALOG)

    def isDigital(self):
        return (self.pin == DIGITAL)

    def set_descriptor(self, descriptor):
        self.descriptor = descriptor
##########################


class DigitalSensor(Sensor):
    '''
    Implements read and write methods
    '''
    def __init__(self, port, pinmode):
        debug("DigitalSensor init")
        self.pin = DIGITAL
        Sensor.__init__(self, port, pinmode)

    def read(self):
        '''
        tries to get a value up to 10 times.
        As soon as a valid value is read, it returns either 0 or 1
        returns -1 after 10 unsuccessful tries
        '''
        okay = False
        error_count = 0

        _wait_for_read()

        if _is_read_open():
            _grab_read()
            while not okay and error_count < 10:
                try:
                    rtn = int(gopigo.digitalRead(self.getPortID()))
                    okay = True
                except:
                    error_count += 1
            _release_read()
            if error_count > 10:
                return -1
            else:
                return rtn

    def write(self, power):
        self.value = power
        return gopigo.digitalWrite(self.getPortID(), power)
##########################


class AnalogSensor(Sensor):
    '''
    implements read and write methods
    '''
    def __init__(self, gpg, port, pinmode):
        debug("AnalogSensor init")
        self.value = 0
        self.pin = ANALOG
        Sensor.__init__(self, gpg, port, pinmode)

    def read(self):
        _wait_for_read()

        if _is_read_open():
            _grab_read()
            self.value = self.gpg.get_grove_analog(self.getPin())
        _release_read()
        return self.value

    def write(self, power):
        self.value = power
        return gopigo.analogWrite(self.getPortID(), power)
##########################


class LightSensor(AnalogSensor):
    """
    Creates a light sensor from which we can read.
    Light sensor is by default on pin A1(A-one)
    self.pin takes a value of 0 when on analog pin (default value)
        takes a value of 1 when on digital pin
    """
    def __init__(self, gpg,port="A1"):
        debug("LightSensor init")
        AnalogSensor.__init__(self, gpg, port,"INPUT")
        self.setPin(2)
        self.set_descriptor("Light sensor")
##########################


class SoundSensor(AnalogSensor):
    """
    Creates a sound sensor
    """
    def __init__(self, port="A1"):
        debug("Sound Sensor on port "+port)
        AnalogSensor.__init__(self, port, "INPUT")
        self.set_descriptor("Sound sensor")

##########################


class UltraSonicSensor(AnalogSensor):

    def __init__(self, port="A1"):
        debug("Ultrasonic Sensor on port "+port)
        AnalogSensor.__init__(self, port, "INPUT")
        self.safe_distance = 500
        self.set_descriptor("Ultrasonic sensor")

    def is_too_close(self):
        _wait_for_read()

        if _is_read_open():
            _grab_read()
            if gopigo.us_dist(PORTS[self.port]) < self.get_safe_distance():
                _release_read()
                return True
        _release_read()
        return False

    def set_safe_distance(self, dist):
        self.safe_distance = int(dist)

    def get_safe_distance(self):
        return self.safe_distance

    def read(self):
        '''
        Limit the ultrasonic sensor to a distance of 5m.
        Take 3 readings, discard any that's higher than 5m
        If we discard 5 times, then assume there's nothing in front
            and return 501
        '''
        return_reading = 0
        readings =[]
        skip = 0
        while len(readings) < 3:
            _wait_for_read()

            _grab_read()
            value = gopigo.corrected_us_dist(PORTS[self.port])
            _release_read()
            if value < 501 and value > 0:
                readings.append(value)
            else:
                skip +=1
                if skip > 5:
                    break

        if skip > 5:
            return(501)

        for reading in readings:
            return_reading += reading

        return_reading = int(return_reading // len(readings))

        return (return_reading)
##########################


class Buzzer(AnalogSensor):
    '''
    The Buzzer class is a digital Sensor with power modulation (PWM).
    Default port is D11
    Note that it inherits from AnalogSensor in order to support PWM
    It has three methods:
    sound(power)
    soundoff() -> which is the same as sound(0)
    soundon() -> which is the same as sound(254), max value
    '''
    def __init__(self, port="D11"):
        AnalogSensor.__init__(self, port, "OUTPUT")
        self.set_descriptor("Buzzer")
        self.power = 254

    def sound(self, power):
        '''
        sound takes a power argument (from 0 to 254)
        the power argument will accept either a string or a numeric value
        if power can't be cast to an int, then turn buzzer off
        '''
        try:
            power = int(power)
        except:
            power = 0

        if power < 0:
            power = 0
        self.power = power
        AnalogSensor.write(self, power)

    def sound_off(self):
        '''
        Makes buzzer silent
        '''
        self.power = 0
        AnalogSensor.write(self, 0)

    def sound_on(self):
        '''
        Maximum buzzer sound
        '''
        self.power = 254
        AnalogSensor.write(self, 254)
##########################


class Led(AnalogSensor):
    def __init__(self, port="D11"):
        AnalogSensor.__init__(self, port, "OUTPUT")
        self.set_descriptor("LED")

    def light_on(self, power):
        AnalogSensor.write(self, power)
        self.value = power

    def light_off(self):
        AnalogSensor.write(self, 0)

    def is_on(self):
        return (self.value > 0)

    def is_off(self):
        return (self.value == 0)
##########################


class MotionSensor(DigitalSensor):
    def __init__(self, port="D11"):
        DigitalSensor.__init__(self, port, "INPUT")
        self.set_descriptor("Motion Sensor")
##########################


class ButtonSensor(DigitalSensor):

    def __init__(self, port="D11"):
        DigitalSensor.__init__(self, port, "INPUT")
        self.set_descriptor("Button sensor")
##########################


class Remote(Sensor):

    def __init__(self, port="SERIAL"):
        global IR_RECEIVER_ENABLED
        # IR Receiver
        try:
            import ir_receiver
            import ir_receiver_check
            IR_RECEIVER_ENABLED = True
        except:
            IR_RECEIVER_ENABLED = False

        if ir_receiver_check.check_ir() == 0:
            print("*** Error with the Remote Controller")
            print("Please enable the IR Receiver in the Advanced Comms tool")
            IR_RECEIVER_ENABLED = False
        else:
            Sensor.__init__(self, port, "SERIAL")
            self.set_descriptor("Remote Control")

    def is_enabled(self):
        return IR_RECEIVER_ENABLED

    def get_remote_code(self):
        '''
        Returns the keycode from the remote control
        No preprocessing
        You have to check that length > 0
            before handling the code value
        if the IR Receiver is not enabled, this will return -1
        '''
        if IR_RECEIVER_ENABLED:
            return ir_receiver.nextcode()
        else:
            print("Error with the Remote Controller")
            print("Please enable the IR Receiver in the Advanced Comms tool")
            return -1
##########################


class LineFollower(Sensor):
    '''
    The line follower detects the presence of a black line or its
      absence.
    You can use this in one of three ways.
    1. You can use read_position() to get a simple position status:
        center, left or right.
        these indicate the position of the black line.
        So if it says left, the GoPiGo has to turn right
    2. You can use read() to get a list of the five sensors.
        each position in the list will either be a 0 or a 1
        It is up to you to determine where the black line is.
    3. You can use read_raw_sensors() to get raw values from all sensors
        You will have to handle the calibration yourself
    '''

    def __init__(self, port="I2C", gpg=None):
        try:
            Sensor.__init__(self, port, "INPUT", gpg)
            self.set_descriptor("Line Follower")
        except Exception as e:
            print (e)
            raise ValueError("Line Follower Library not found")

    def read_raw_sensors(self):
        '''
        Returns raw values from all sensors
        From 0 to 1023
        May return a list of -1 when there's a read error
        '''
        _wait_for_read()

        _grab_read()
        five_vals = line_sensor.read_sensor()
        _release_read()

        if five_vals != -1:
            return five_vals
        else:
            return [-1, -1, -1, -1, -1]

    def get_white_calibration(self):
        return line_sensor.get_white_line()

    def get_black_calibration(self):
        return line_sensor.get_black_line()

    def read(self):
        '''
        Returns a list of 5 values between 0 and 1
        Depends on the line sensor being calibrated first
            through the Line Sensor Calibration tool
        May return all -1 on a read error
        '''
        _wait_for_read()

        if _is_read_open():
            _grab_read()
            five_vals = scratch_line.absolute_line_pos()
            _release_read()

        return five_vals

    def read_position(self):
        '''
        Returns a string telling where the black line is, compared to
            the GoPiGo
        Returns: "Left", "Right", "Center", "Black", "White"
        May return "Unknown"
        This method is not intelligent enough to handle intersections.
        '''
        five_vals = [-1,-1,-1,-1,-1]

        _wait_for_read()
        if _is_read_open():
            _grab_read()
            five_vals = self.read()
            _release_read()

        if five_vals == [0, 0, 1, 0, 0] or five_vals == [0, 1, 1, 1, 0]:
            return "Center"
        if five_vals == [1, 1, 1, 1, 1]:
            return "Black"
        if five_vals == [0, 0, 0, 0, 0]:
            return "White"
        if five_vals == [0, 1, 1, 0, 0] or \
           five_vals == [0, 1, 0, 0, 0] or \
           five_vals == [1, 0, 0, 0, 0] or \
           five_vals == [1, 1, 0, 0, 0] or \
           five_vals == [1, 1, 1, 0, 0] or \
           five_vals == [1, 1, 1, 1, 0]:
            return "Left"
        if five_vals == [0, 0, 0, 1, 0] or \
           five_vals == [0, 0, 1, 1, 0] or \
           five_vals == [0, 0, 0, 0, 1] or \
           five_vals == [0, 0, 0, 1, 1] or \
           five_vals == [0, 0, 1, 1, 1] or \
           five_vals == [0, 1, 1, 1, 1]:
            return "Right"
        return "Unknown"


if __name__ == '__main__':
    import time
    b = Buzzer()
    print (b)
    print ("Sounding buzzer")
    b.sound_on()
    time.sleep(1)
    print ("buzzer off")
    b.sound_off()
