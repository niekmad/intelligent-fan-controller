import subprocess
import time
from gpiozero import OutputDevice


from prometheus_client import Gauge, start_http_server

gTEMP = Gauge('server_temp', 'Temperature of the server')
gFAN = Gauge('server_fan', 'Status of the server fan')


ON_THRESHOLD = 55  # (degrees Celsius) Fan kicks on at this temperature.
OFF_THRESHOLD = 44  # (degress Celsius) Fan shuts off at this temperature.
SLEEP_INTERVAL = 5  # (seconds) How often we check the core temperature.
GPIO_PIN = 3  # Which GPIO pin you're using to control the fan.


def get_temp():
    """Get the core temperature.
    Run a shell script to get the core temp and parse the output.
    Raises:
        RuntimeError: if response cannot be parsed.
    Returns:
        float: The core temperature in degrees Celsius.
    """
    output = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True)
    temp_str = output.stdout.decode()

    try:
        return float(temp_str.split('=')[1].split('\'')[0])
    except (IndexError, ValueError):
        raise RuntimeError('Could not parse temperature output.')


def run():

    while True:
        try:
            temp = get_temp()
            gTEMP.set(temp)
            
            # Start the fan if the temperature has reached the limit and the fan
            # isn't already running.
            # NOTE: `fan.value` returns 1 for "on" and 0 for "off"
            if temp > ON_THRESHOLD and not fan.value:
                fan.on()
                gFAN.set(1)

            # Stop the fan if the fan is running and the temperature has dropped
            # to 10 degrees below the limit.
            elif fan.value and temp < OFF_THRESHOLD:
                fan.off()
                gFAN.set(0)
        except:
            break
        
        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    # Validate the on and off thresholds
    if OFF_THRESHOLD >= ON_THRESHOLD:
        raise RuntimeError('OFF_THRESHOLD must be less than ON_THRESHOLD')

    fan = OutputDevice(GPIO_PIN)
    fan.off()

    # Start prometheus metrics collector
    start_http_server(8020)
    # Run fan application
    run()
    