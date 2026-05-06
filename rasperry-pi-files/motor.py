from gpiozero import Servo
from time import sleep
from gpiozero import Device
from gpiozero.pins.native import NativeFactory
import RPi.GPIO

#Device.pin_factory = NativeFactory()

# Connect the servo signal wire to GPIO 17
# Use a 5V external power source for the servo red/black wires
servo = Servo(18)

def dip():
    try:
        print("Moving Forward...")
        servo.min()    # Moves to minimum position (0 degrees)
        sleep(3)       # Holds for 3 seconds

        print("Retracting...")
        servo.max()    # Moves to maximum position (180 degrees)
        sleep(3)       # Holds for 3 seconds

    except KeyboardInterrupt:
        # Allows you to stop the script safely with Ctrl+C
        print("Program stopped.")
        
        
def servo_down():
    servo.min()
    
def servo_up():
    servo.value = 1
    sleep(3)
    
    servo.value = 0;
        
if __name__ == "__main__":
    dip()
