# #######################################################################
# This example is for controlling the GoPiGo robot from a mouse scroll                          
# http://www.dexterindustries.com/GoPiGo/                                                                
# #######################################################################

import RPi.GPIO as GPIO
import pygame
import time
from pygame.locals import *
import socket

# -------------------Accelerometer-----------------------
host = ''
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind((host, port))
# -----------------END Accelerometer---------------------

# -------------------- GPIO INITIATION ------------------------
GPIO.setmode(GPIO.BOARD)
# Below 4 rows just tells the RPi what theese pins are output pinns =(pins to send signals to the H-brige with)
GPIO.setup(7, GPIO.OUT)  # EN1 controls left hand side wheels (H-bridge connector J1 pin1)
GPIO.setup(11, GPIO.OUT)  # EN2 controles right hand side wheelsa (H-bridge connector J1 pin7)
GPIO.setup(13, GPIO.OUT)  # DIR1 LH True=Forward & False=Backward
GPIO.setup(15, GPIO.OUT)  # DIR2 RH True=Forward & False=Backward

GPIO.setup(12, GPIO.OUT)  # Sets the pin 12 as an output/signaling pin for the Servo
GPIO.setwarnings(False)
GPIO.output(7, False)
GPIO.output(11, False)


# ------------------ END GPIO INITIATION -----------------------

# -------------------Start Car Class-------------------------------
class Car(object):

    def __init__(self):
        self.drivingDirection = "stop"
        self.cameraDirection = 7.5

    def get_driving_direction(self):
        return self.drivingDirection

    def set_driving_direction(self, driving_direction):
        self.drivingDirection = driving_direction

    def get_camera_direction(self):
        return self.cameraDirection

    def set_camera_direction(self, camera_direction):
        self.cameraDirection = camera_direction

    def servo_turn_left(self):
        if self.cameraDirection >= 5.5 + servoStepLength:
            self.cameraDirection -= servoStepLength
        else:
            print('Maximum Left turn acheived')

    def servo_turn_right(self):
        if self.cameraDirection <= 9.5 - servoStepLength:
            self.cameraDirection += servoStepLength
        else:
            print('Maximum Right turn acheived')


# -------------------End Car Class------------------------------

# ------------- Servo on startup -------------------------------
servoPin = 12  # Servo signaling pin
pwm = GPIO.PWM(servoPin, 50)
pwm.start(7.5)  # Makes the servo point straight forward
time.sleep(0.5)  # The time for the servo to straighten forward
# ----------- END Servo on startup ------------------------------

# ------Variables--------

t = 0.05  # run time
servoStepLength = 0.5  # Set Step length for Servo
stop = False
forward = False  # Constant to set the direction the wheels spin
backward = True  # Constant to set the direction the wheels spin

# ---END Variables-------

# -------Define class with GPIO instructions for driving---------


def drive_forward():
    GPIO.output(7, False)  # EN1 Enable RH wheels to spin
    GPIO.output(11, False)  # EN2 Enable LH wheels to spin
    GPIO.output(13, forward)  # Enable RH wheels to spin forward
    GPIO.output(15, forward)  # Enable LH wheels to spin forward
    GPIO.output(7, True)  # EN1 Enable RH wheels to spin
    GPIO.output(11, True)  # EN2 Enable LH wheels to spin


def drive_backward():
    GPIO.output(7, False)  # EN1 Enable RH wheels to spin
    GPIO.output(11, False)  # EN2 Enable LH wheels to spin
    GPIO.output(13, backward)  # Enable RH wheels to spin backwards
    GPIO.output(15, backward)  # Enable LH wheels to spin backwards
    GPIO.output(7, True)  # EN1 Enable RH wheels to spin
    GPIO.output(11, True)  # EN2 Enable LH wheels to spin


def drive_left_pivot():
    GPIO.output(7, False)  # EN1 Enables RH wheels to spin
    GPIO.output(11, False)  # EN2 Disable LH wheels to spin
    GPIO.output(13, backward)  # Enabels RH wheels to spin forward
    GPIO.output(15, forward)  # Enabels LH wheels to spin backwards
    GPIO.output(7, True)  # EN1 Enables RH wheels to spin
    GPIO.output(11, True)  # EN2 Disable LH wheels to spin


def drive_right_pivot():
    GPIO.output(7, False)  # EN1 Disable RH wheels to spin
    GPIO.output(11, False)  # EN2 Enables LH wheels to spin
    GPIO.output(13, forward)  # Enabels RH wheels to spin backwards
    GPIO.output(15, backward)  # Enabels LH wheels to spin forward
    GPIO.output(7, True)  # EN1 Disable RH wheels to spin
    GPIO.output(11, True)  # EN2 Enables LH wheels to spin


# --- Stop motors --- #
def stop_all():
    GPIO.output(7, 0)
    GPIO.output(11, 0)
    GPIO.output(13, 0)
    GPIO.output(15, 0)


# --END Stop motors--##
# ---END-Define class with GPIO instructions for driving---------

# ----------Define quit game class -----------------
def stop_program():
    """shuts down all running components of program"""
    '''
    try:
        joyStick.quit()
    except:
        pass
        '''
    stop_all()
    pwm.stop()
    GPIO.cleanup()
    print ("Shutting down!")


# --------END Define quit game class ----------------

# --------Initialize pyGame -------------------
pygame.init()
pygame.joystick.init()
'''
try:
    joyStick = pygame.joystick.Joystick(0)
    joyStick.init()
except:
    pass
    '''
screen = pygame.display.set_mode((240, 240))
pygame.display.set_caption('VR CAR')
# ------ END Initialize pyGame ----------------

# ----keyboard codes for pygame
# ----http://thepythongamebook.com/en:glossary:p:pygame:keycodes

# --------------------- Driving direction list ----------------------
drivingDirectionList = {'forward': drive_forward, 'backward': drive_backward,
                        'left': drive_left_pivot, 'right': drive_right_pivot, 'stop': stop_all}


# --------------------- keyboard steering -------------------------
def main():
    the_car = Car()
    runs = True

    while runs:
        time.sleep(.02)
        if stop:
            break
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == 32:  # key <SPACE> Stop motors / Break
                    stop_all()
                if event.key == K_w:  # key <W> Move forward
                    the_car.set_driving_direction('forward')
                    print(the_car.get_driving_direction())
                if event.key == K_s:  # key <S> Move backward
                    the_car.set_driving_direction('backward')
                    print(the_car.get_driving_direction())
                if event.key == K_a:  # key <A> Move left
                    the_car.set_driving_direction('left')
                    print(the_car.get_driving_direction())
                if event.key == K_d:  # key <D> Move right
                    the_car.set_driving_direction('right')
                    print(the_car.get_driving_direction())

                if event.key == K_q:  # key <Q> Turn servo left
                    the_car.set_camera_direction(5.5)
                if event.key == K_r:  # key <R> Turn servo right
                    the_car.set_camera_direction(9.5)
                if event.key == K_e:  # key <E> Turn servo straight forward
                    the_car.set_camera_direction(7.5)

                if event.key == K_c:
                    the_car.servo_turn_left()
                    print('Camera Direction DC = ', the_car.get_camera_direction())
                if event.key == K_v:
                    the_car.servo_turn_right()
                    print('Camera Direction DC = ', the_car.get_camera_direction())

                if event.key == K_ESCAPE:  # key <Esc> QUIT
                    global stop
                    stop = True
            elif event.type == pygame.KEYUP:
                the_car.set_driving_direction('stop')
                print(the_car.get_driving_direction())

            elif event.type == pygame.QUIT:
                global stop
                stop = True

            drivingDirectionList[the_car.get_driving_direction()]()
            pwm.ChangeDutyCycle(the_car.get_camera_direction())
            time.sleep(0.05)

# -------------------- END keyboard steering -----------------------

if __name__ == "__main__":
    main()
    stop_program()
