import time
from statistics import mean

import RPi.GPIO as GPIO
import matplotlib.pyplot as plt

# Constants
SAMPLING_DURATION = 20
DECAY_TIMEOUT = 0.01  # 10ms timeout
SAMPLING_DELAY = 0.01  # 10ms between sensor readings
BUFFER_DELAY = 0.01  # 10ms buffer
SENSOR_PINS = [14, 15, 18, 23, 24]

# Set up GPIO
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Thresholds dictionary
THRESHOLDS = {}
tape_color = None


def get_thresholds():
    """
    Retrieve predefined thresholds for a given context.

    This function provides access to the global `THRESHOLDS` variable,
    which contains a set of calculated threshold values of the IR Array sensors.
    These values can be used for various operations such as validations, comparisons,
    or other logical determinations based on specific thresholds. The
    function does not accept any input arguments and simply returns the
    `THRESHOLDS` variable.

    :return: A dictionary or list of predefined threshold values. The
             exact structure and data will depend on the implementation
             of the `THRESHOLDS` global variable.
    """
    return THRESHOLDS

def get_tape_color():
    """
    Retrieves the color of the tape. This function is designed to return the
    value representing the color of the tape currently in use.

    :return: The color of the tape.
    :rtype: str
    """
    return tape_color

def get_sensor_pins():
    """
    Retrieve the sensor pins configuration.

    This function returns a dictionary containing the configuration of
    the sensor pins. The dictionary keys represent the sensor names,
    and the values correspond to the respective pin numbers used by
    the sensors.

    :return: A dictionary mapping sensor names to their corresponding
             pin numbers.
    :rtype: dict
    """
    return SENSOR_PINS

# Helper functions
def calculate_threshold(pin, tape_min, floor_max):
    """
    Calculates a threshold value based on the provided tape minimum and floor
    maximum values. If both values are given, their average is computed and rounded
    to five decimal places. If either value is not provided, the function returns
    None.

    :param pin: Provided parameter (unused in this function).
    :type pin: Any
    :param tape_min: The minimum value of the tape to be considered for the
        threshold computation. If None, no threshold is calculated.
    :type tape_min: float or None
    :param floor_max: The maximum value of the floor to be considered for the
        threshold computation. If None, no threshold is calculated.
    :type floor_max: float or None
    :return: The computed threshold value as the rounded average of tape_min and
        floor_max if both are provided. Returns None otherwise.
    :rtype: float or None
    """
    if tape_min is not None and floor_max is not None:
        return round((tape_min + floor_max) / 2, 5)
    return None

def sample_decay_times(state_key, sampling_start_time, decay_stats):
    """
    Sample the voltage decay times for a set of sensors over a fixed duration and
    store the collected data. The function continuously collects and records each
    sensor's decay time until the total sampling time exceeds a defined duration.
    It uses a safety mechanism to prevent infinite loops when no reading is detected
    within a timeout period.

    :param state_key: A key indicating the state of the system which will be used to
        categorize the decay statistics recorded.
    :type state_key: str
    :param sampling_start_time: The timestamp representing when the sampling process
        started.
    :type sampling_start_time: float
    :param decay_stats: A nested dictionary where the outer keys are sensor pins,
        the inner keys are state identifiers (e.g., `state_key`), and the values
        are lists of recorded decay times for the corresponding state and sensor.
    :type decay_stats: dict
    :return: None
    """
    while time.time() - sampling_start_time < SAMPLING_DURATION:
        for sensor_pin in SENSOR_PINS:
            GPIO.setup(sensor_pin, GPIO.OUT)
            GPIO.output(sensor_pin, GPIO.HIGH)
            time.sleep(0.00001)  # Allow voltage to build
            GPIO.setup(sensor_pin, GPIO.IN)

            # Measure voltage decay time
            start_time = time.time()
            decay_time = 0

            # Safety mechanism to prevent infinite loop if no reading detected
            while GPIO.input(sensor_pin) == GPIO.HIGH:
                if time.time() - start_time > DECAY_TIMEOUT:
                    break
                decay_time = time.time() - start_time

            # Store the decay time
            decay_stats[sensor_pin][state_key].append(decay_time)
            time.sleep(SAMPLING_DELAY)

        print(
            f"Decay times recorded for state '{state_key}': {[decay_stats[pin][state_key][-1] for pin in SENSOR_PINS]}")
        time.sleep(BUFFER_DELAY)

def load_thresholds_from_file(filename="IR_thresholds.txt"):
    """
    Loads thresholds for IR sensors from a specified file and returns them as a
    dictionary. The file is expected to be formatted with each line containing
    a key-value pair in the format "Pin X: Y", where X is the pin number (integer)
    and Y is the threshold value (float). Lines not conforming to this format are
    ignored.
`
    :param filename: The name of the file containing threshold values. Defaults
                     to "IR_thresholds.txt".
    :type filename: str

    :return: A dictionary mapping pin numbers (int) to their respective thresholds
             (float), or None if an error occurs while reading the file.
    :rtype: dict[int, float] | None
    """
    try:
        with open(filename, "r") as file:
            thresholds = {}
            for line in file:
                if line.strip():
                    parts = line.strip().split(":")
                    if len(parts) == 2:
                        pin = int(parts[0].split()[1])
                        threshold = float(parts[1].strip())
                        thresholds[pin] = threshold
        print(f"Thresholds loaded from {filename}")
        return thresholds
    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"Error loading thresholds from {filename}: {e}")
        return None

def save_thresholds_to_file(filename="IR_thresholds.txt"):
    """
    Saves threshold values to a file in a readable format.

    This function writes the content of the global `THRESHOLDS` dictionary
    to a specified file. Each entry in the dictionary is formatted into
    lines and written to the file, displaying the pin and its corresponding
    threshold value. If no filename is provided, the default filename
    "IR_thresholds.txt" will be used.

    :param filename: Path to the file where thresholds will be saved.
    :type filename: str, optional
    :return: None
    """
    with open(filename, "w") as file:
        for pin, threshold in THRESHOLDS.items():
            file.write(f"Pin {pin}: {threshold}\n")
        print(f"Thresholds saved to {filename}")

def main():
    """
    Main functionality to execute the user interaction flow, sensor data sampling, decay analysis, and threshold
    calculation for the line follower system.

    It provides the ability to load thresholds from a file, use or discard them, and gather decay statistics for
    light sensors placed on tape and floor surfaces. Based on these readings, thresholds are calculated and
    highlighted alongside any potential issues during the analysis, such as a safety mechanism to make sure the
    readings were conducted correctly, if not then an error will be printed with details about the error.
    The final step involves user confirmation for starting the robot.

    :raises RuntimeError: When the user manually aborts at specific critical decision points in the script.
    """
    # Attempt to load thresholds from file
    loaded_thresholds = load_thresholds_from_file()
    if loaded_thresholds:
        while True:
            user_input = input("Do you want to use the loaded thresholds? [Y/N]: ").strip().upper()

            if user_input == 'Y':
                global THRESHOLDS
                THRESHOLDS = loaded_thresholds
                print("Using loaded thresholds. Skipping sampling process.")
                return
            elif user_input == 'N':
                print("Discarding loaded thresholds. Proceeding with sampling.")
                break
            else:
                print("Invalid input. Please enter 'Y' or 'N'!")

    # User input for tape color
    while True:
        tape_color = input("Is the line follower tape black or white [B/W]? ").strip().lower()
        if tape_color in ['b', 'w']:
            break
        print("Invalid input. Please enter 'B' for black or 'W' for white.")

    # Initialize decay statistics and sampling phases
    input("Place the tape underneath the sensor and press Enter to start sampling...")
    decay_stats = {pin: {"tape": [], "floor": []} for pin in SENSOR_PINS}

    # Sampling for tape state
    print("Sampling for tape state...")
    sampling_start_time = time.time()
    sample_decay_times("tape", sampling_start_time, decay_stats)

    input("Now remove the tape and place the sensors on the floor. Press Enter to start sampling...")
    sampling_start_time = time.time()
    print("Sampling for floor state...")
    sample_decay_times("floor", sampling_start_time, decay_stats)

    # Analyze decay times and calculate thresholds
    for pin in SENSOR_PINS:
        tape_min = min(decay_stats[pin]["tape"], default=None)
        floor_max = max(decay_stats[pin]["floor"], default=None)
        threshold = calculate_threshold(pin, tape_min, floor_max)
        THRESHOLDS[pin] = threshold if threshold is not None else "N/A"

        # Print stats
        for state in ["tape", "floor"]:
            print(
                f"Pin {pin} ({state}) - Min: {round(min(decay_stats[pin][state]), 5) if decay_stats[pin][state] else 'N/A'}, "
                f"Max: {round(max(decay_stats[pin][state]), 5) if decay_stats[pin][state] else 'N/A'}, "
                f"Mean: {round(mean(decay_stats[pin][state]), 5) if decay_stats[pin][state] else 'N/A'}")
        print(f"Pin {pin} - Suggested Threshold: {THRESHOLDS[pin]}")

        # Plot and save graph
        plt.figure()
        plt.plot(decay_stats[pin]["tape"], label="Tape", color='blue', alpha=0.7, marker='o', linestyle='-')
        plt.plot(decay_stats[pin]["floor"], label="Floor", color='red', alpha=0.7, marker='x', linestyle='--')
        if threshold:
            plt.axhline(y=threshold, color='green', linestyle='--', label="Suggested Threshold")
        plt.title(f"Decay Time Line Graph for Pin {pin}")
        plt.xlabel("Readings Index")
        plt.ylabel("Decay Time (s)")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"pin_{pin}_decay_time_comparison_line_graph.png")
        plt.close()

        # Calculate intersections with the threshold (Readings error detection).
        if threshold is not None:
            if tape_color == 'w':
                tape_intersections = sum(1 for value in decay_stats[pin]["tape"] if value > threshold)
                floor_intersections = sum(1 for value in decay_stats[pin]["floor"] if value < threshold)
            elif tape_color == 'b':
                tape_intersections = sum(1 for value in decay_stats[pin]["tape"] if value < threshold)
                floor_intersections = sum(1 for value in decay_stats[pin]["floor"] if value > threshold)

            print(f"tape_color: {tape_color}")

            if tape_intersections > 10 or floor_intersections > 10:
                print(f"Warning: Pin {pin} has {tape_intersections} threshold crossings for 'tape' and "
                      f"{floor_intersections} for 'floor' decay times.")

                while True:
                    user_input = input("Threshold crossings are high. Do you want to proceed? [Y/N]: ").strip().lower()
                    if user_input in ['y', 'n']:
                        break
                    print("Invalid input. Please enter 'Y' to proceed or 'N' to abort.")

                if user_input == 'n':
                    print("Program execution aborted by user.")
                    GPIO.cleanup()
                    exit()
                elif user_input == 'y':
                    print("Program execution continues with the current settings.")


    # Save thresholds to file after calculations
    save_thresholds_to_file()

    # Print a messagea to inform the user and ask if they want the robot to start running
    while True:
        user_input = input("Configuration complete. Do you want the robot to start running? [Y/N]: ").strip().lower()
        if user_input == 'y':
            print("The robot is now starting...")
            break
        elif user_input == 'n':
            print("Terminating the program as per user request.")
            GPIO.cleanup()
            exit()
        else:
            print("Invalid input. Please enter 'Y' to start the robot or 'N' to terminate the program.")


if __name__ == "__main__":
    try:
        print("Running subprogram 'IRCollaboration.py' process...")
        main()
    except KeyboardInterrupt:
        print("Subprogram 'IRCollaboration.py' interrupted by user.")
    finally:
        GPIO.cleanup()
