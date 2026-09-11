from machine import Pin

i2c_interface = 0
sdapin = Pin(20)                      # I2C Data
sclpin = Pin(21)                      # I2C Clock
ow_pin = Pin(22, Pin.IN, Pin.PULL_UP)  # One wire 

# Configure ADC pin (GP26, GP27, or GP28) or sub set
# Configure only the pins that have voltage signals attached
#adc_pins = [26, 27, 28]
adc_pins = [26]
