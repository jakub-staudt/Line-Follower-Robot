import threading
import time

import RPi.GPIO as GPIO

from IRCollaboration import main as ir_array_collaboration, get_thresholds, get_sensor_pins, get_tape_color


def setup_pins() -> None:
    """
    Sets up GPIO pins and PWM channels for motor control and sensor interfacing.

    This function configures pins for motor driver components, ultrasonic sensors,
    and infrared sensors, setting their input or output states as required. It also
    initializes PWM channels for motor speed control and sets default states for
    the control pins of the motor driver.

    :raises RuntimeError: If GPIO library is not properly initialized or
                          if pins are unavailable for use.

    :global int en1: Pin for motor driver enable pin 1.
    :global int in1: Pin for motor driver input 1.
    :global int in2: Pin for motor driver input 2.
    :global int in3: Pin for motor driver input 3.
    :global int in4: Pin for motor driver input 4.
    :global int en2: Pin for motor driver enable pin 2.
    :global list IR_pins: List of pins used for IR sensors, sourced from
                          an external function.
    :global int US_ECHO: Pin used for reading echo signal in ultrasonic sensor.
    :global int US_TRIG: Pin used for sending a trigger signal in ultrasonic sensor.
    :global GPIO.PWM p1: PWM instance controlling motor associated with `en1`.
    :global GPIO.PWM p2: PWM instance controlling motor associated with `en2`.

    :return: This function does not return any value.
    """
    global en1, in1, in2, in3, in4, en2, IR_pins, US_ECHO, US_TRIG, p1, p2

    GPIO.setmode(GPIO.BCM)  # Set GPIO mode to BCM

    # Motor Driver
    en1 = 0
    in1 = 5
    in2 = 6
    in3 = 13
    in4 = 19
    en2 = 26

    # Ultrasonic Sensor
    US_ECHO = 2
    US_TRIG = 3

    # IR Sensor pins from external file
    IR_pins = get_sensor_pins()

    # Allocate Pin State (IN/OUT)
    GPIO.setup(en1, GPIO.OUT)
    GPIO.setup(in1, GPIO.OUT)
    GPIO.setup(in2, GPIO.OUT)
    GPIO.setup(in3, GPIO.OUT)
    GPIO.setup(in4, GPIO.OUT)
    GPIO.setup(en2, GPIO.OUT)
    GPIO.setup(US_TRIG, GPIO.OUT)
    GPIO.setup(US_ECHO, GPIO.IN)

    p1 = GPIO.PWM(en1, 1000) # Right wheel
    p2 = GPIO.PWM(en2, 1000) # Left Wheel

    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.LOW)

    p1.start(25)
    p2.start(25)

def check_ir_position(IRThresholds):
    """
    Calculate the orientation of the robot by detecting a tape by an array of Infrared (IR) sensors.

    The function samples readings from an array of IR sensors, determines the binary states of each sensor
    based on predefined thresholds, and calculates a weighted position value. The detection and calculation
    are influenced by a tolerance threshold and tape color.

    :param IRThresholds: Dictionary where keys represent sensor pins and values are the threshold values
        for determining the binary state of the respective IR sensor.
    :type IRThresholds: dict[int, float]
    :return: Computed position of the object or tape detected by the sensors relative to the center of
        the sensor array. Returns 0 if no valid data is detected or if the denominator is zero.
    :rtype: float
    """


    DECAY_TIMEOUT = 0.01  # timeout (10ms)
    SAMPLING_DELAY = 0.001  # between sensor readings (original = 100ms)
    ir_times = {}
    ir_states_binary = {}
    weights = [-2, -1, 0, 1, 2]  # For IR array with 5 sensors

    # FIRST STEP: Sample the readings from IR sensors
    for pin in IR_pins:
        # Initially charge the capacitors
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.00001)  # Allow voltage to build (Charge capacitor)
        GPIO.setup(pin, GPIO.IN)

        # Measure voltage decay time
        start_time = time.time()
        decay_time = 0

        # Safety mechanism to prevent infinite loop if no reading detected
        while GPIO.input(pin) == GPIO.HIGH:
            if time.time() - start_time > DECAY_TIMEOUT:
                break
            decay_time = time.time() - start_time

        # Store the decay time for specific pin
        ir_times[pin] = decay_time
        time.sleep(SAMPLING_DELAY)

    # SECOND STEP: Convert the array into a binary state array using 'pin'
    tape_color = get_tape_color()
    for pin in IR_pins:
        binary_state = 1 if ir_times[pin] < IRThresholds[pin] else 0
        ir_states_binary[pin] = binary_state if tape_color == 'w' else 1 - binary_state
    print(list(ir_states_binary.values()))

    # THIRD STEP: Calculate position
    numerator = sum(ir_states_binary[pin] * weights[index] for index, pin in enumerate(IR_pins))
    denominator = sum(ir_states_binary.values())

    position = numerator / denominator if denominator != 0 else 0  # Avoid division by zero
    print("Position:", position)

    return position

def drive_stop():
    """
        Stops the operation of all motors by setting their GPIO control pins to a low state. This function is designed to
        ensure the motors are immediately stopped.

    :return: None
    """
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.LOW)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.LOW)

def forward():
    """
    Drives a motor forward by setting appropriate GPIO pins to HIGH or LOW.

    This function utilizes the GPIO library to set certain pins to control
    the direction of a motor. The `forward` function specifically sets the
    required pins to spin the motor in a forward direction.

    :raises RuntimeError: If there is an issue with the GPIO configuration
                          or pin setup, the function may fail at runtime.
    """
    GPIO.output(in1, GPIO.LOW)
    GPIO.output(in2, GPIO.HIGH)
    GPIO.output(in3, GPIO.LOW)
    GPIO.output(in4, GPIO.HIGH)

def monitor_distance():
    """
    Measures the distance to an obstacle using an ultrasonic sensor and controls the
    robot's behavior based on the detected distance. This function triggers the ultrasonic
    sensor, calculates the time taken for the echo to return, and computes the distance
    to an obstacle. Based on the calculated distance, the robot either stops if an
    obstacle is detected within a threshold or continues moving forward if the path is clear.

    :raises RuntimeError: If the sensor cannot detect a pulse for distance measurement.

    :return: The measured distance to an obstacle in centimeters.
    :rtype: float
    """
    GPIO.output(US_TRIG, False)

    time.sleep(0.01) # Waiting for sensor to settle

    GPIO.output(US_TRIG, True)
    time.sleep(0.00001)
    GPIO.output(US_TRIG, False)

    while GPIO.input(US_ECHO) == 0:
        pulse_start = time.time()

    while GPIO.input(US_ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    print(f"Obstruction distance: {distance}cm")

    if distance < 20:
        drive_stop()
        print("Obstacle Detected, Stopping Robot")
        time.sleep(0.5)
    else:
        forward()

    return distance
    # If else the current Manouvre continues
    print(f"Obstruction in front: {distance}cm")

def monitor_distance_thread():
    """
    Runs a continuous thread to monitor distance using the `monitor_distance` function.

    This function initiates an infinite loop where the `monitor_distance` function is called
    repeatedly. It is designed to operate as part of a threading mechanism that continuously
    tracks or processes distance-related data in a background thread. The purpose of this function is to
    allow simultaneous operation of the Ultrasound distance monitoring without causing large latency for
    the main() control loop.

    :return: This function does not return any value as it runs indefinitely.
    """
    while True:
        monitor_distance()

def manoeuvre(position):
    """
    Constrain the robot's position and adjust motor speeds to achieve the desired manoeuvring behavior.
    This function ensures that the position remains between a predefined range to prevent over steering.
    Based on the position, the function calculates adjustment values for the motor speeds
    and sets the duty cycle accordingly for directional movement.

    :param position: The position value representing the desired directional motion.
                     Values range from -2 (hard left) to 2 (hard right).
                     Values closer to 0 indicate forward motion.
    :type position: float
    :return: None
    """

    # Constrain position to be within range [-2, 2] so that the robot doesn't overdrive when maneuvering
    if position < -2:
        position = -2
    elif position > 2:
        position = 2

    # THE BELOW VALUES CAN BE MODIFIED
    # IDEAL VALUES: p1 = 40, p2 = 35, adjustment_p1 = 20, adjustment_p2 = 17.5,
    # MAX VALUES: p1 = 50, p2 = 35, adjustment_p1 = 25, adjustment_p2 = 22.5
    base_speed_p1 = 40  # Define a base motor speed for p1 (different due to different max torque of wheel), p1 = 40 is a safe limit
    base_speed_p2 = 35  # Define a base motor speed for p2 (different due to different max torque of wheel), p2 = 35 is a safe limit
    adjustment_p1 = abs(position) * 20  # Adjustment value for motor p1
    adjustment_p2 = abs(position) * 17.5  # Adjustment value for motor p2

    if position <= -2:  # Hard left
        p1.ChangeDutyCycle(base_speed_p1 - adjustment_p1)
        p2.ChangeDutyCycle(base_speed_p2 + adjustment_p2)

    elif -2 < position < -0.1:  # Slight left
        p1.ChangeDutyCycle(base_speed_p1 - adjustment_p1 / 2)
        p2.ChangeDutyCycle(base_speed_p2 + adjustment_p2 / 2)

    elif -0.1 <= position <= 0.1:  # Move forward if near the center
        p1.ChangeDutyCycle(base_speed_p1)
        p2.ChangeDutyCycle(base_speed_p2)

    elif 0.1 < position < 2:  # Slight right
        p1.ChangeDutyCycle(base_speed_p1 + adjustment_p1 / 2)
        p2.ChangeDutyCycle(base_speed_p2 - adjustment_p2 / 2)

    else:  # Hard right
        p1.ChangeDutyCycle(base_speed_p1 + adjustment_p1)
        p2.ChangeDutyCycle(base_speed_p2 - adjustment_p2)

def main():
    """
    Executes the main control loop for a robot, initializing its sensors, starting its
    motor operation, and handling distance monitoring and navigation based on
    infrared (IR) sensor thresholds.

    The function orchestrates the primary operations for the robot's control, such as setting
    up GPIO pins, fetching IR sensor thresholds, handling IR sensor collaboration, starting
    distance monitoring in a separate thread, and controlling motor movement in a continuous loop.

    :raises: Any exceptions from called subroutines or hardware access.
    """

    # ROBOT SETUP

    setup_pins()

    # Logic to initialize sensor readings
    ir_array_collaboration()  # Execute the program in IRCollaboration.py

    IR_array_thresholds = get_thresholds()  # Fetch and store get_thresholds value
    print(f"Imported THRESHOLD values: {get_thresholds}, Thresholds: {IR_array_thresholds}")

    # START ROBOT OPERATION

    # Start distance monitoring thread
    distance_thread = threading.Thread(target=monitor_distance_thread, daemon=True)
    distance_thread.start()

    forward() #Start of motors

    while True:
        manoeuvre(check_ir_position(IR_array_thresholds))  # Control the direction of the robot based on calculated position
        time.sleep(0.001)  # Shorter sleep time for more frequent distance checks

if __name__ == "__main__":
    try:
        print("Running program 'Robot_main.py'...")
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Stopping robot...")
        drive_stop()
        GPIO.cleanup()

    finally:
        GPIO.cleanup()






