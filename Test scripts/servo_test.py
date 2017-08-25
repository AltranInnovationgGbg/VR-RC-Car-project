import RPi.GPIO as gpio

gpio.setmode(gpio.BOARD) #Below 4 rows just tells the RPi what theese pins are output pinns =(pins to send signals to the H-brige with)
servoPin=16 # Servo signaling pin
gpio.setup(servoPin, gpio.OUT) # Set the pin 16 as an output/signaling pin

pwm=gpio.PWM(servoPin,50)
pwm.start(7) # straight forward
for i in range(0,20):
    desiredPosition=input("Where do you want the servo? 5-160 ")
    DC= 1./18.*(desiredPosition)+2
    print(DC)
    pwm.ChangeDutyCycle(DC)
#pwm.start(7)# straight forward
#pwm.ChangeDutyCycle(2)# max to right
#pwm.ChangeDutyCycle(12) # max left
print(DC)
pwm.stop()
gpio.cleanup()