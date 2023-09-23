#hcsr04 modular sensor component

*hcsr04* is a Viam modular sensor component that provides distance readings from the HCSR04 ultrasonic sensor for Pi boards with direct GPIO access.


## API

The hcsr04 resource fulfills the Viam sensor interface

### get_readings()

The *get_readings()* command takes no arguments, and returns the detected distance in centimeters (with the key 'distance').

## Viam Component Configuration

This component should be configured as type *sensor*, model *ilboud:sensor:hcsr04*.

The following attributes may be configured as hcsr04 component config attributes.

Example:

``` json
{
  "trigger_pin": 32,
  "echo_pin": 30
}
```

### trigger_pin

*integer - required*

### echo_pin

*integer - required*

