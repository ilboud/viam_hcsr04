from typing import ClassVar, Mapping, Sequence, Any, Dict, Optional, cast
from typing_extensions import Self

from viam.module.types import Reconfigurable
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily

from viam.components.sensor import Sensor
from viam.logging import getLogger

import time
import asyncio
import RPi.GPIO as GPIO


class HCSR04(Sensor, Reconfigurable):
    MODEL: ClassVar[Model] = Model(ModelFamily("ilboud", "sensor"), "hcsr04")
    def __init__(self, name: str):
        super().__init__(name)
        self.samples = 5  # or whatever default or configuration-defined value you want
        self.timeout = 100
        self.offset = 190000
    trigger_pin: int
    echo_pin: int
    # Speed of sound is 343m/s which we need in cm/ns for our distance measure
    SPEED_OF_SOUND_CM_NS = 343 * 100 / 1E9  # 0.0000343 cm / ns
     
    # Constructor
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        sensor = cls(config.name)
        sensor.reconfigure(config, dependencies)
        return sensor

    # Validates JSON Configuration
    @classmethod
    def validate(cls, config: ComponentConfig):
        trigger_pin = config.attributes.fields["trigger_pin"].number_value
        if trigger_pin == "":
            raise Exception("A trigger_pin must be defined")
        echo_pin = config.attributes.fields["echo_pin"].number_value
        if echo_pin == "":
            raise Exception("An echo_pin must be defined")
        return

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        self.trigger_pin = int(config.attributes.fields["trigger_pin"].number_value)
        self.echo_pin = int(config.attributes.fields["echo_pin"].number_value)
    
        # set both pins to output mode
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.trigger_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.setwarnings(False)
        return


    async def get_readings(self, extra: Optional[Dict[str, Any]] = None, **kwargs):
#    def read_distance(self, timeout=50, samples=3, offset=190000):
        """ Return a distance in cm from the ultrasound sensor.
        timeout: total time in ms to try to get distance reading
        samples: determines how many readings to average
        offset: Time in ns the measurement takes (prevents over estimates)
        The default offset here is about right for a Raspberry Pi 4.
        Returns the measured distance in centimetres as a float.

        To give more stable readings, this method will attempt to take several
        readings and return the average distance. You can set the maximum time
        you want it to take before returning a result so you have control over
        how long this method ties up your program. It takes as many readings
        up to the requested number of samples set as it can before the timeout
        total is reached. It then returns the average distance measured. Any
        readings where the single reading takes more than the timeout is
        ignored so these do not distort the average distance measured. If no
        valid readings are taken before the timeout then it returns zero.

        You can choose parameters to get faster but less accurate readings or
        take longer to get more samples to average before it returns. The
        timeout effectively limits the maximum distance the sensor can measure
        because if the sound pusle takes longer to return over the distance
        than the timeout set then this method returns zero rather than waiting.
        So to extend the distance that can be measured, use a larger timeout.
        """
        # Start timing
        start_time = time.perf_counter_ns()
        time_elapsed = 0
        count = 0  # Track now many samples taken
        total_pulse_durations = 0
        distance = -999


        # Loop until the timeout is exceeded or all samples have been taken
        while (count < self.samples) and (time_elapsed < self.timeout * 1000000):
            # Trigger
            GPIO.output(self.trigger_pin, 1)
            time.sleep(.00001)  # 10 microseconds
            GPIO.output(self.trigger_pin, 0)

            # Wait for the ECHO pin to go high
            # wait for the pulse rise
            GPIO.wait_for_edge(self.echo_pin, GPIO.RISING, timeout=self.timeout)
            pulse_start = time.perf_counter_ns()

            # And wait for it to fall
            GPIO.wait_for_edge(self.echo_pin, GPIO.FALLING, timeout=self.timeout)
            pulse_end = time.perf_counter_ns()

            # get the duration
            pulse_duration = pulse_end - pulse_start - self.offset
            if pulse_duration < 0:
                pulse_duration = 0  # Prevent negative readings when offset was too high

            # Only count reading if achieved in less than timeout total time
            if pulse_duration < self.timeout * 1000000:
                # Convert to distance and add to total
                total_pulse_durations += pulse_duration
                count += 1

            time_elapsed = time.perf_counter_ns() - start_time

        # Calculate average distance in cm if any successful reading were made
        if count > 0:
            # Calculate distance using speed of sound divided by number of samples and half
            # that as sound pulse travels from robot to obstacle and back (twice the distance)
            distance = total_pulse_durations * self.SPEED_OF_SOUND_CM_NS / (2 * count)
        return {"distance": distance}
    
async def main():
    # Create a configuration for the HCSR04 sensor
    sensor_config = ComponentConfig()
    sensor_config.name = "hcsr04"
    
    # Set trigger_pin and echo_pin attributes
    sensor_config.attributes.fields["trigger_pin"].number_value = 13    # Replace with your GPIO pin number
    sensor_config.attributes.fields["echo_pin"].number_value = 25       # Replace with your GPIO pin number


    # Create a sensor instance
    hcsr04_sensor = HCSR04.new(sensor_config, {})


    distance = await hcsr04_sensor.get_readings()
    print(f"Distance: {distance} cm")    

# Run the main coroutine
if __name__ == "__main__":
    asyncio.run(main())