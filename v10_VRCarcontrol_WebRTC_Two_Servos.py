import pigpio
import pygame
import time
from pygame.locals import *
import re
import socket
import os
import json
from subprocess import call

# ------------------ GPIO INITIATION ------------------------
""" This section declares and initialize the gpio pins """
pi = pigpio.pi()  # Setup pigpio connection to the raspberry pi
ENABLE_L_PIN = 4  # GPIO pin number for enabling left side wheels
ENABLE_R_PIN = 17  # GPIO pin number for enabling right side wheels
DIR_L_PIN = 27  # GPIO pin number for direction of left side wheels
DIR_R_PIN = 22  # GPIO pin number for direction of right side wheels
SERVO_PIN_Z_AXIS = 19  # GPIO pin number for Servo pin rotating around the z-axis
SERVO_PIN_ELEVATION = 18  # GPIO pin number for Servo pin changing the elevation angle

pi.set_mode(ENABLE_L_PIN, pigpio.OUTPUT)  # EN1 controls left hand side wheels (H-bridge connector J1 pin1)
pi.set_mode(ENABLE_R_PIN, pigpio.OUTPUT)  # EN2 controls right hand side wheels (H-bridge connector J1 pin7)
pi.set_mode(DIR_L_PIN, pigpio.OUTPUT)  # DIR1 LH True=Backward & False=Forward
pi.set_mode(DIR_R_PIN, pigpio.OUTPUT)  # DIR2 RH True=Backward & False=Forward
pi.set_mode(SERVO_PIN_Z_AXIS, pigpio.OUTPUT)  # Sets the physical pin 12 as an output/signaling pin for the Servo
pi.set_mode(SERVO_PIN_ELEVATION, pigpio.OUTPUT)  # Sets the physical pin 35 as an output/signaling pin for the Servo

pi.write(ENABLE_L_PIN, False)  # Set left side wheels to stop spinning.
pi.write(ENABLE_R_PIN, False)  # Set right side wheels to stop spinning.
# ---------------- END GPIO INITIATION -----------------------
# -------------------- Variables -----------------------------
"""This section initialize constants used through out the program"""
# t = 0.05  # run time
# servoStepLength = 0.5  # Set Step length for Servo
forward = False  # Constant to set the direction the wheels spin
backward = True  # Constant to set the direction the wheels spin
MAX_PW_ELEVATION = 2100  # set the maximum pulse width of the pulse width modulation
                         # for the Servo controlling elevation angle. Larger pulse width points the cameras downward
                         # for maximum possible rotation without cameras = 2200
MIN_PW_ELEVATION = 900  # set the minimum pulse width of the pulse width modulation
                        # for the Servo controlling elevation angle. Lower pulse width points the cameras upwards
START_PW_ELEVATION = 900  # initialization value for the z-axis servo
FORWARD_PW_ELEVATION = 1900  # pulse width to make the cameras face forward
DEG2PW_FACTOR_ELEVATION = 1000.0/90.0  # Factor to change from degrees into pulse width.
MAX_PW_Z = 1850  # set the maximum pulse width of the pulse width modulation
                 # for the Servo controlling rotation around Z-axis
                 # for maximum possible rotation without cameras = 2250
MIN_PW_Z = 1050  # set the minimum pulse width of the pulse width modulation
                # for the Servo controlling rotation around Z-axis
                # for maximum possible rotation without cameras = 750
START_PW_Z = 1500  # initialization value for the z-axis servo
FORWARD_PW_Z = 1500  # pulse width to make the cameras face forward
DEG2PW_FACTOR_Z = 750/90.0  # Factor to change from degrees into pulse width.
keycode_forward = [103]  # set key code for driving forward
keycode_backward = [108]  # set key code for driving backward
keycode_left = [105]  # set key code for turning left
keycode_right = [106]  # set key code for turning right
keycode_calibrate_forward = [28]  # set key code for calibrating forward servo direction
quit_command = 'quit'  # Command sent through webRTC server to turn off program.
stop_command = 'stop'  # Command sent through webRTC server to sever connection to cellphone
# ------------------- END Variables --------------------------
# ------------------- Start Car Class ------------------------
"""The Car class is used to keep track of the car settings. 
   The car is initialized as standing still with camera direction forward"""


class Car(object):
    def __init__(self):
        """The car is initialized as standing still with camera direction forward"""
        self.drivingDirection = "stop"
        self.cameraDirection_Z = START_PW_Z
        self.cameraDirection_Elevation = START_PW_ELEVATION
        self.cameraForward = 180.0
        self.alpha_degrees = 90
        self.gamma_degrees = 90
        self.gx = 0
        self.gy = 0
        self.upside_down = False

    def get_driving_direction(self):
        """Returns the driving direction (String)"""
        return self.drivingDirection

    def set_driving_direction(self, driving_direction):
        """Set the driving direction (String): possible values: forward, backward, left, right and stop."""
        self.drivingDirection = driving_direction

    def get_camera_direction_z(self):
        """Returns the pulse width of the PWM signal that controls the servo rotating around the z-axis."""
        return self.cameraDirection_Z

    def get_camera_direction_elevation(self):
        """Returns the pulse width of the PWM signal that controls the servo controlling the elevation angle."""
        return self.cameraDirection_Elevation

    def set_camera_direction_z(self, camera_direction_z):
        """Set the pulse width of the PWM signal that controls the servo rotating around the z-axis (float).
           Checks if the pulse width is within the allowed pulse width length and otherwise sets it to the upper or
           lower limit. If within the allowed pulse width it rounds the number to the closest tens, since the RPI can
           only handle this resolution"""
        if camera_direction_z < MIN_PW_Z:
            self.cameraDirection_Z = MIN_PW_Z
        elif camera_direction_z > MAX_PW_Z:
            self.cameraDirection_Z = MAX_PW_Z
        else:
            self.cameraDirection_Z = round(camera_direction_z, -1)

    def set_camera_direction_elevation(self, camera_direction_elevation):
        """Set the pulse width of the PWM signal that controls the servo rotating around the z-axis. 
           Checks if the pulse width is within the allowed pulse width length and otherwise sets it to the upper or
           lower limit. If within the allowed pulse width it rounds the number to the closest tens, since the RPI can
           only handle this resolution"""
        if camera_direction_elevation < MIN_PW_ELEVATION:
            self.cameraDirection_Elevation = MIN_PW_ELEVATION
        elif camera_direction_elevation > MAX_PW_ELEVATION:
            self.cameraDirection_Elevation = MAX_PW_ELEVATION
        else:
            self.cameraDirection_Elevation = round(camera_direction_elevation, 0)

    def set_camera_forward(self):
        """Recalibrates which angle is considered forward around the z axis (float)."""
        self.cameraForward = self.alpha_degrees

    def get_camera_forward(self):
        """Returns which angle is considered forward (float)"""
        return self.cameraForward

    def calculate_new_pulse_widths(self):
        """Calculates and sets the pulse width of the servos. All angles changes with 180 degrees when the phone passes
        from being pointed upward to downward and vice versa. First check if the phone is pointed up or down and change
        the degrees accordingly."""
        if self.gamma_degrees < 0:
            self.alpha_degrees -= 180
            self.gamma_degrees += 180
            if self.alpha_degrees < 0:
                self.alpha_degrees += 360
        self.check_upside_down()
        if self.upside_down:
            self.gamma_degrees = 180 - self.gamma_degrees
        alpha_forward_diff1 = self.alpha_degrees - self.cameraForward
        gamma_diff = 90 - self.gamma_degrees
        if alpha_forward_diff1 < 0:
            alpha_forward_diff2 = 360.0 + self.alpha_degrees - self.cameraForward
        else:
            alpha_forward_diff2 = -360.0 + self.alpha_degrees - self.cameraForward

        if abs(alpha_forward_diff1) <= abs(alpha_forward_diff2):
            alpha_forward_diff = alpha_forward_diff1
        else:
            alpha_forward_diff = alpha_forward_diff2

        self.set_camera_direction_z(FORWARD_PW_Z-alpha_forward_diff*DEG2PW_FACTOR_Z)
        self.set_camera_direction_elevation(FORWARD_PW_ELEVATION-gamma_diff*DEG2PW_FACTOR_ELEVATION)

    def extract_json_data(self, json_data):
        """Extracts the relevant orientation data sent from phone and save them to class variables"""
        self.alpha_degrees = float(json_data.get('do').get('alpha'))
        self.gamma_degrees = float(json_data.get('do').get('gamma'))
        self.gx = float(json_data.get('dm').get('gx'))
        self.gy = float(json_data.get('dm').get('gy'))

    def check_upside_down(self):
        """ Check if the phone has turned 180 degrees around the phone's y-axis. upside down will change if the up down
        tilt of the phone is between +/- 30 degrees"""
        if self.gx > 7 or self.gy > 7:
            self.upside_down = True
        elif self.gx < -7 or self.gy < -7:
            self.upside_down = False

# ------------------- End Car Class------------------------------
# ----------------- Servo initialization/stop ----------------------------
"""The Servo is started, and later only the duty cycle is changed to
direct the cameras in different directions"""


def initialize_servo():
    """ Initialize the Servos and make them point to starting position"""
    pi.set_servo_pulsewidth(SERVO_PIN_Z_AXIS, START_PW_Z)  # Makes the servo point straight forward
    pi.set_servo_pulsewidth(SERVO_PIN_ELEVATION, START_PW_ELEVATION)  # Makes the servo point straight up
    time.sleep(0.5)  # The time for the servo to straighten forward


def stop_servos():
    """ Make the servo point to starting position and then turn the PWM signal off"""
    pi.set_servo_pulsewidth(SERVO_PIN_Z_AXIS, START_PW_Z)  # Points the servo to starting position
    pi.set_servo_pulsewidth(SERVO_PIN_ELEVATION, START_PW_ELEVATION)  # points the servo to starting position
    time.sleep(1)  # wait one second for the servo to reach starting position
    pi.set_servo_pulsewidth(SERVO_PIN_Z_AXIS, 0)  # Stop servo
    pi.set_servo_pulsewidth(SERVO_PIN_ELEVATION, 0)  # Stop servo
# ---------------- END Servo on startup -------------------------
# -------Define class with GPIO instructions for driving---------
"""Functions to drive the Car. Because how the h-bridge is designed, the motors need to be
disabled before changing the driving directions of the motors."""


def drive_forward():
    """ Turn off all motors, set all motors to turn forward, start all motors"""
    pi.write(ENABLE_L_PIN, False)  # Stop LH wheels
    pi.write(ENABLE_R_PIN, False)  # Stop RH wheels
    pi.write(DIR_L_PIN, forward)  # Set LH wheels to spin forward
    pi.write(DIR_R_PIN, forward)  # Set RH wheels to spin forward
    pi.write(ENABLE_L_PIN, True)  # Start spinning LH wheels
    pi.write(ENABLE_R_PIN, True)  # Start spinning RH wheels


def drive_backward():
    """ Turn off all motors, set all motors to turn backward, start all motors"""
    pi.write(ENABLE_L_PIN, False)  # Stop LH wheels
    pi.write(ENABLE_R_PIN, False)  # Stop RH wheels
    pi.write(DIR_L_PIN, backward)  # Set LH wheels to spin backward
    pi.write(DIR_R_PIN, backward)  # Set RH wheels to spin backward
    pi.write(ENABLE_L_PIN, True)  # Start spinning LH wheels
    pi.write(ENABLE_R_PIN, True)  # Start spinning RH wheels


def drive_left_pivot():
    """ Turn off all motors, set LH motors to turn backward and RH motors to turn forward, start all motors"""
    pi.write(ENABLE_L_PIN, False)  # Stop LH wheels
    pi.write(ENABLE_R_PIN, False)  # Stop RH wheels
    pi.write(DIR_L_PIN, backward)  # Set LH wheels to spin backward
    pi.write(DIR_R_PIN, forward)  # Set RH wheels to spin forward
    pi.write(ENABLE_L_PIN, True)  # Start spinning LH wheels
    pi.write(ENABLE_R_PIN, True)  # Start spinning RH wheels


def drive_right_pivot():
    """ Turn off all motors, set LH motors to turn forward and RH motors to turn backward, start all motors"""
    pi.write(ENABLE_L_PIN, False)  # Stop LH wheels
    pi.write(ENABLE_R_PIN, False)  # Stop RH wheels
    pi.write(DIR_L_PIN, forward)  # Set LH wheels to spin forward
    pi.write(DIR_R_PIN, backward)  # Set RH wheels to spin backward
    pi.write(ENABLE_L_PIN, True)  # Start spinning LH wheels
    pi.write(ENABLE_R_PIN, True)  # Start spinning RH wheels


def stop_motors():
    """Stop all motors, turn all motor GPIO pins to low."""
    pi.write(ENABLE_L_PIN, False)  # Stop LH wheels
    pi.write(ENABLE_R_PIN, False)  # Stop RH wheels
    pi.write(DIR_L_PIN, False)  # Set LH wheels to spin backward
    pi.write(DIR_R_PIN, False)  # Set RH wheels to spin backward


# -------END-Define class with GPIO instructions for driving---------
# --------------------- Driving direction list ----------------------
"""The driving list is later used as a look up table to call the driving functions."""

driving_direction_list = {'forward': drive_forward, 'backward': drive_backward,
                          'left': drive_left_pivot, 'right': drive_right_pivot, 'stop': stop_motors}

# --------------------- End Driving Direction List ------------------
# -----------------------Define quit game class ------------------


def stop_program():
    """shuts down all running components of program"""
    stop_motors()
    stop_servos()
    pi.stop()
    print ("Shutting down!")


# ---------------------END Define quit game class ----------------

# ------------------ Communication with phone ----------------
""" Setup of the communication service through the webrtc server."""


def setup_connection():
    """Setup socket connection and returns socket to listen to."""
    socket_path = '/tmp/uv4l.socket'
    try:
        os.unlink(socket_path)
    except OSError:
        if os.path.exists(socket_path):
            raise
    s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    s.bind(socket_path)
    s.listen(0)
    return s
# ----------------- end communication with phone -----------------

# ---------------- Main ------------------------


def main():
    """
    Main loop controlling the program flow.
    By sending Quit/Stop it is possible to quit the program or stop the connection to the phone.
    After stopping, it is possible to connect another phone to the car.
    """
    the_car = Car()  # Create the Car object
    iteration_control = 0  # used to control how many iterations the car should enable the motors
    turn_off_program = False  # Used to send quit command
    while True:
        if turn_off_program:  # Exit main loop if quit command received
            break
        s = setup_connection()  # Setup connection
        print 'awaiting connection...'
        connection, client_address = s.accept()  # Establish connection to client
        print 'Connection established'
        initialize_servo()  # initialize the servo
        stop = False  # used to stop the control loop and a new connection is possible.
        while True:
            if stop:  # if stop command has been received, enter stop sequence.
                stop_servos()
                stop_motors()
                print 'stop sequence initiated'
                connection.send('Connection aborted, will reconnect in 15s if call not hanged up.')
                connection.close()
                time.sleep(15)
                s.close()
                break
            data_in_string = connection.recv(256)  # Retrieved the received string.
            try:
                data_in_json = json.loads(data_in_string)  # change string into json object
                if data_in_json.get('do'):  # if the json-object contains 'do'
                    the_car.extract_json_data(data_in_json)
                    the_car.calculate_new_pulse_widths()
                elif data_in_json.get('keycodes'):  # if the json-object contains 'keycodes'
                    if data_in_json.get('keycodes') == keycode_forward:  # check if relevant keycode has been sent
                        the_car.set_driving_direction('forward')
                        iteration_control = 5
                    elif data_in_json.get('keycodes') == keycode_backward:
                        the_car.set_driving_direction('backward')
                        iteration_control = 5
                    elif data_in_json.get('keycodes') == keycode_left:
                        the_car.set_driving_direction('left')
                        iteration_control = 2
                    elif data_in_json.get('keycodes') == keycode_right:
                        the_car.set_driving_direction('right')
                        iteration_control = 2
                    elif data_in_json.get('keycodes') == keycode_calibrate_forward:
                        the_car.set_camera_forward()
                if iteration_control <= 0:  # Check if car motors has been going for the specified number of iterations
                    the_car.set_driving_direction('stop')  # stop motors if it has.
                    iteration_control = 0

                driving_direction_list[the_car.get_driving_direction()]()  # Call motor function from list
                pi.set_servo_pulsewidth(SERVO_PIN_Z_AXIS, round(the_car.get_camera_direction_z(), -1))  # Set servos
                pi.set_servo_pulsewidth(SERVO_PIN_ELEVATION, round(the_car.get_camera_direction_elevation(), 0))
                iteration_control -= 1
            except ValueError:  # Check if something other than json-object has been sent.
                if data_in_string == quit_command:  # Check if quit command has been sent
                    stop = True
                    turn_off_program = True
                elif data_in_string == stop_command:  # Check if stop command has been sent
                    stop = True
# ------------------------End Main---------------------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print e
    stop_program()
    # call("sudo nohup shutdown -h now", shell=True)  # Turns off RPi when program ends.