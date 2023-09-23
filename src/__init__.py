"""
This file registers the model with the Python SDK.
"""
from viam.components.sensor import Sensor
from viam.resource.registry import Registry, ResourceCreatorRegistration

from .hcsr04 import HCSR04

Registry.register_resource_creator(Sensor.SUBTYPE, HCSR04.MODEL, ResourceCreatorRegistration(HCSR04.new, HCSR04.validate))
