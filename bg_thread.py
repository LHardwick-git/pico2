
# Machine and phython imports
from machine import ADC, Pin, I2C
from time import sleep
import _thread
import sys
import time

# the one wire system imports
# Standard library imports
import onewire, ds18x20
# temperature sensors

# Local (in flash) One wire imports
from ds2413 import DS2413			# Relays

# The debug system Debug can be set by the master thread
debug = True

def log(*args):
    if debug:
        for item in args:
            print(item, end = "")

# Local config and tool imports
#import dev_list 				# a file created to map device names
try:
    from dev_list import dev_names
except ImportError:
    dev_names = {}

import bidict		# bi directional dictionary

dev_type = bidict.bidict() # maps devices to types
                    # dev_type[dev] = type
                    # inverse maps types to device list


# i2C initialisation

# load device specific pins and sensors from config file
from gpio_config import i2c_interface, sdapin, sclpin, ow_pin, adc_pins

# i2C initialisation
i2c = I2C(i2c_interface, scl=sclpin, sda=sdapin, freq=100000)

# i2c Imports (Thes are local imports and must be in flash files)
def i2c_module_load(id):
        if   id == '48':
            print('loading ADS1015 - analogue voltage library')
            from i2c_analogue import ADS1015	# Analogue Voltages
            ads1015 = decorate_ADS1015(ADS1015)(i2c)
            i2c_drivers['48'] = ads1015  # log object(driver) for device ID
            
        elif id == '38':
            print('loading AHT10 - temp and humidity library')
            from i2c_AHT10_20 import AHT10		# Temperature and humidity
            aht10 = decorate_aht10(AHT10)(i2c) # creating new instance calls __init__ which resets / recalibrates device
            i2c_drivers['38'] = aht10 # log object(driver) for device ID
            
        # elif id == 'xx':  : template for other drivers to be added here
        #
        # passing the 'dev' ID to the class addaptor allow the driver to be reused for multiple similar devices
        # which have been configured at differnt i2c addresses      

def decorate_aht10(cls):
    # The following allow the default AHT1x library module to be loaded
    # and overwrites/ adds methods that need to be changed for this app
    # Basically this alows the module to be impoted and class to be modified
    #
    # this is the template for all other i2c module addaptors to be added here
    
    @property
    def _humidity(self):
            return self.relative_humidity
    
    cls.humidity = _humidity
    
    def create(self, dev):
        mytypes = {"0T": "Temp", "0H": 'Humidity'}
        for parameter in mytypes:
            key = "ic"+dev+parameter+"00"+station[-8:]    
            log("initialising ", key, "\r\n")
            devices[key] = {' Name': dev_names.get(key, 'Not Set'), 'Value': '','Connected': 'True'}
            dev_type[key]= mytypes[parameter]
        self.update(dev)
        
    cls.create = create
    
    def update(self, dev):
        mytypes = {"0T": "temperature", "0H": 'humidity'}
        for parameter in mytypes:
            key = "ic"+dev+parameter+"00"+station[-8:]
            devices[key]['Value'] = round(getattr(self, mytypes[parameter]),1)
            
    cls.update = update
    
    return cls

def decorate_ADS1015(cls):
    
    def create(self, dev):
        for channel in range(4):
            key = "ic"+dev+"0"+str(channel)+"00"+station[-8:]
            log("initialising ", key, "\r\n")
            devices[key] = {' Name': dev_names.get(key, 'Not Set'), 'Value': '','Connected': 'True'}
            dev_type[key]= 'Volts'
        self.update(dev)
        
    cls.create = create
    
    def update(self, dev):

        for channel in range(4):
            value = round(10*self.raw_to_v(self.read(0,channel)),4)
            key = "ic"+ dev +"0"+str(channel)+"00"+station[-8:]
            log("updating ", key)
            devices[key]['Value'] = value
            log("updated ", channel, " ", value, "\r\n")    
    
    cls.update = update
    
    return cls

i2c_drivers= {'38': None, '48' : None} # empty drivers list to register drivers into

#
# drivers return device adresses; i2c device addresses are two bytes hex which will be included in
# the unique device id - this avoids wrap around issus with hex >100
#
# Driver (CLASS) should be m0dified to NOT talk to the device unitil it is detected
# It might not be present but it will be noticed when it is connected
# Device might be removed and reconnected, in which case init will be called again
#=================================================

# One wire intitializations
# Setup one-wire bus

ow = onewire.OneWire(ow_pin)

# known one wire devices
ow_temperature = ds18x20.DS18X20(ow)
ow_relays = DS2413(ow)
# =======================================
# End of one wire initializations
# see docs here https://github.com/robert-hh/Onewire_DS18X20/blob/master/Readme.md



# Station MAC address used as part of unique device ID string
station = "1234567890123456"

def set_station(x):
    global station
    station = x

# Thread loop flags (could be moved closer to the thread definition)
run_thread = False
running = False

# Local start up states
# The Q system queue_add is called from the master thread
queue = []

def queue_add(x):
    global queue
    queue += x

# No devices know in startup (found by bus scanning
devices = {}
# ==========================================
# End of local start up states
    
# r_lock = _thread.lock()  ??? not know waht this is for

log("bg_thread module started\r\n")   # tell the world


# Local Pico configurations
temp_sensor = ADC(4)

# one wire code
# Scan for one wire devices and initialise
ow_families = {'10': 'Temp',
               '22': 'Temp',
               '28': 'Temp',
               '3a': 'Relay'}


def init_ow_item(devices, k):  	# devices list and k is the full device ID
    d = devices[k]				# d is the device record
    d[' Name'] 		= dev_names.get(k, 'Not Set')
    d['Connected'] 	= 'True'
    dev_type[k] = ow_families.get(k[:2], 'Unknown')

    if dev_type[k] 	== 'Relay':
        d.update({'State': [[0],[0]], 'Pins': [[1],[1]]})

def ow_scan(ow, devices):
    scanned_devices = [rom.hex() for rom in ow.scan()]
    log('Found ow devices:', scanned_devices, "\r\n")
    
    for d in scanned_devices:
        if d not in devices:
            devices[d] = {}
            init_ow_item(devices, d)
            
        else:
            devices[d]['Connected'] = 'True' 
            
    for d in devices:
        if (d[:2] in ow_families.keys()) and (d not in scanned_devices):
            if devices[d]['Connected']:
                devices[d]['Connected'] = False
                log("Device ", d, " apparently disconnected\r\n")
            
def read_ow_temperatures(ow, devices): # always scan first so we know the devices are there
    devs = [k for k in devices if ow_families.get(k[:2]) == "Temp" and devices[k]['Connected']]
    if devs:
        try:
            ow_temperature.convert_temp()
        except onewire.OneWireError as e:
            log("One wire error caught when starting temperature conversion\r\n")
            return
    
    sleep(0.750)
    for dev in devs:
#        if devices[dev]['Connected']:
        try:
            temp = round(ow_temperature.read_temp(bytearray.fromhex(dev)),1)
        except Exception as e:
            log("error reading device ", dev, "\r\n")
            if str(e) == "CRC error":
                log("CRC error caught reading ", dev, "\r\n")
                devices[dev]['Value'] = ''
                devices[dev]['Connected'] = False
            else:
                log("Unknown error ", e, " reading device ",dev, "\r\n")
                
        else:
            devices[dev]['Value'] = temp
                    
#        else:
#            devices[dev]['Value'] = ''
            # Max and  Min retained in case device returns
    
def read_ow_relays(ow, devices): # always scan first so we know the devices are there
    devs = [k for k in devices if ow_families.get(k[:2]) == "Relay"]
    pass # do no more till temperatures teste

    for dev in devs:
        if devices[dev]['Connected']:
            state = ow_relays.read_state(bytearray.fromhex(dev))
            devices[dev]['State'] = [state[1][0], state[0][0]]
            devices[dev]['Pins'] = [state[1][1], state[0][1]]
        else:
            devices[dev]['State'] = ""
            devices[dev]['Pins']  = ""                 
  
# end of one wire routines

bg_count = 1

def init_CPU_temp(devices):
    id = "RPPi_CPU" + station[-8:]
    devices[id] = {'Connected': 'Native', ' Name' : dev_names.get(id, "Not Set")}
    dev_type[id] = 'Temp'
    if id+'_hide' in dev_names : dev_type[id] = dev_type[id] + "*"
    update_CPU_temp(devices)
    
def update_CPU_temp(devices):
    adc_value = temp_sensor.read_u16()    
    # Convert ADC value to voltage
    voltage = adc_value * (3.3 / 65535.0)
    temperature_celsius = round(27 - (voltage - 0.706) / 0.001721, 1)
    id = "RPPi_CPU" + station[-8:]
    devices[id]['Value'] = temperature_celsius

def r_temperatures():
    return {d: devices[d] for d in dev_type.inverse.get('Temp', {} ) }

def r_relays():
    return {d: devices[d] for d in dev_type.inverse.get('Relay', {} ) }

def r_voltages():
    return {d: devices[d] for d in dev_type.inverse.get('Volts', {} ) }

def read(type):
    return {d: devices[d] for d in dev_type.inverse.get(type, {} ) }

def delete(device):
    if devices[device]['Connected']:
        log("Request to delete ", device, " ignored, device is connected \r\n")
        return False
    else:
        del devices[device]
        del dev_type[device]
        return True

# initialise voltages
def init_RPI_volts():
    for pin in adc_pins:
        adc = ADC(Pin(pin))

        id = "RPPiIo" + str(pin) + station[-8:]
        devices[id] = {'Connected': 'Native', ' Name' : dev_names.get(id, "Not Set")}
        dev_type[id] = 'Volts'
        if id+'_hide' in dev_names : dev_type[id] = dev_type[id] + "*"
    update_RPI_volts()    
        
def update_RPI_volts():
    # Read raw 16-bit value (0-65535)   
    # Convert to voltage (0.0 - 3.3V)
    for pin in adc_pins:
        adc = ADC(Pin(pin))
        id = "RPPiIo" + str(pin) + station[-8:]
        devices[id]["Value"] = round(adc.read_u16()  * (3.3 / 65535), 3)
        
        
def minmax():
    for dev in [k for k in devices if k+"_minmax" in dev_names and devices[k]['Connected'] and 'Value' in devices[k]]:
        devices[dev]['Max'] = max(devices[dev]['Value'], devices[dev].get('Max', devices[dev]['Value']))
        devices[dev]['Min'] = min(devices[dev]['Value'], devices[dev].get('Min', devices[dev]['Value']))
    for dev in [k for k in devices if k+"_minmax" not in dev_names and 'Max' in devices[k]]:
        del devices[dev]['Max']
        del devices[dev]['Min']


def i2c_scan(bus, devices): # Scan bus; reconnect know, create new, and disconnect know if not on bus
    scanned_devices = [f'{k:x}' for k in bus.scan()] # k is a two byte hex
    for dev in scanned_devices:
        
        if dev not in [k[2:4] for k in devices if k[:4] == "ic"+str(dev)]: # if device not already known
            if str(dev) not in i2c_drivers:
                log("Unknown i2c device family connected in rescan ", dev, "\r\n")
                
            else:   # Log as connected and initialise device
                log("New device ", dev, " apparently connected \r\n")
                i2c_module_load(dev)
                i2c_drivers[dev].create(dev)
       
        reconnected = [k for k in devices if devices[k]['Connected'] == False and k[:4] == "ic"+str(dev)]
        for d in reconnected:  # some i2c devices report multiple data points so connect each point
                                    # NB this does not consider the case of re-init device when reconnected
            log(d, " Reconnected \r\n")  
            devices[d]['Connected'] = 'True'
                
        disconnected = [k for k in devices if devices[k]['Connected'] and  \
                        k[:2] == "ic" and \
                        k[2:4] not in scanned_devices]
        
        for d in disconnected :
            devices[d]['Connected'] = False
            devices[d]['Value'] = ''
            log("Device ", d, " apparently disconnected \r\n")            
                
    return scanned_devices  # NB so we only return items found on the bus,
                            # Orphan devices will persist in the devices dictionary until deleted              
            
# i2 = (i2c)
# nn = device address
# (#i/c) parameter /channel  (temp/hum : channel)
# half byte spare ?
# ??
# 4 - 7 MAC unique
#
# RP Raspberry
# PI Pico / NA Nano / nx number and model (e.g.4a)
# Io
# Pin
# 4 - 7 MAC unique
#
# w1 byte 0 is unique family number

# f strings convert byte addres to hex [x] so that every devices is 1 byte address  
           
# add internal temparature to temperatures   
#    temp_sensor = ADC(4)
#adc_value = temp_sensor.read_u16
# Convert ADC value to CPU temperature
#voltage = adc_value * (3.3 / 65535.0)
#temperature_celsius = round(27 - (voltage - 0.706) / 0.001721, 1)
#temperatures.setdefault("CPU", { 'Value': temperature_celsius, 'Connected': 'Native'})
    
def set_relays():
    for r in r_relays():
        ow_relays.write_state(bytearray.fromhex(r), [1, 1])
    read_ow_relays(ow, devices)
    
def clear_relays():
    for r in r_relays():
        ow_relays.write_state(bytearray.fromhex(r), [0, 0])
    read_ow_relays(ow, devices)
    
def delete_all():
    for dev in [k for k in devices if k[:2] in ow_families or k[:2] == "ic"]:
        del devices[dev]
        del dev_type[dev]
        
    # only delete bus based items not natice (as they must exist)
    

def core1_thread():
#led = Pin('LED', Pin.OUT)
    global run_thread
    sleep(5)
    global running
    running = True
    while not run_thread:
        pass
    log ("Thread 1 started")
    
#    init things once the main program says to run
    init_CPU_temp(devices)
    init_RPI_volts()
    
    global adc_pins, bg_count
    
    
# End of thread initialisation loop starts here
#===============================================
    while run_thread:
        
#  toggle led, delay loop, and check queue
        led.value(led.value() ^ 1)
        sleep(2)
        while queue:   # If queue not empty
            queue[0]() # execute item from Q
            queue.pop(0)

#  read native voltages
        update_RPI_volts()
# 
        i2c_devices = i2c_scan(i2c, devices) # scan i2c bus and update device connections and values
        log("I2c scan returned ", i2c_devices, "\r\n")
        for dev in i2c_devices:
                i2c_drivers[dev].update(dev)
        log("refreshed i2c devices", "\r\n")
    
#  re-read CPU temperature
        update_CPU_temp(devices)
      
        ow_scan(ow, devices)   # rescan ow bus and update device values
        read_ow_temperatures(ow, devices)
        read_ow_relays(ow, devices)
        
        minmax()
        
# increment counter
        bg_count += 1
        while queue:
            queue[0]()
            queue.pop(0)

            
    print ("Background thread halted")
    running = False


led = Pin('LED', Pin.OUT)

led.value(True)
      
second_thread = _thread.start_new_thread(core1_thread, ())

if __name__ == "__main__":
#   th = AHT10(i2c)
#    print("Temp and huminity AHT10 instance created")
#    print(th.temperature)
#    print(th.humidity)
    
    print("running main")

    run_thread = True
    try:
        while True:
#            print("voltages: ",voltages)
            print("")
            print("Devices: ")
            for dev in sorted(devices):
                print(dev,dev_type[dev],"\t : ",devices[dev],dev_type[dev])
            print("")
            sleep(5)
    except KeyboardInterrupt as e:
        run_thread = False
        while running:
            pass
        
    



                       

