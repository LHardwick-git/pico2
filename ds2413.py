import time
from machine import Pin
import onewire

# see device types here: https://www.owfs.org/index_php_page_standard-devices.html
# Driver for DS2413 relay/switch device driver

class DS2413:
    def __init__(self, ow):
        self.ow = ow
        
    def scan(self):
        return [rom for rom in self.ow.scan() if rom[0] == 0x3a]

    def write_state(self, rom, state):
        # 0xFF = High/OFF (Open Drain), 0x00 = Low/ON
        # DS2413 expects a specific protocol:
        # Write Byte, PIO_Byte, ~PIO_Byte (twice)
        
        # Prepare byte: 0xFC + 3 bits for PIO and 5 dummy bits
        # Simplified: Use 0x5A to write
        pio_byte = 0xFC | state[0] | state[1] << 1
        
        self.ow.reset()
        self.ow.select_rom(rom)
        self.ow.writebyte(0x5A) # Write PIO
        self.ow.writebyte(pio_byte)
        self.ow.writebyte(~pio_byte) # Inverted
#        print("Return code ",hex(self.ow.readbyte()))# Read result
        
    def read_state(self, rom):
        # 0xFF = High/OFF (Open Drain), 0x00 = Low/ON
        # DS2413 expects a specific protocol:
        # Write Byte, PIO_Byte, ~PIO_Byte (twice)
        
        # Prepare byte: 0xFC + 3 bits for PIO and 5 dummy bits
        # Simplified: Use 0x5A to write
        
        self.ow.reset()
        self.ow.select_rom(rom)
        self.ow.writebyte(0xF5) # Read PIO
        result = self.ow.readbyte() # Read result
        
#        print (result & 0x01, result >> 1 &0x01, result >> 2 & 0x01, result >>3 & 0x01)
#        print("Bits ",hex(self.ow.readbyte()))
#		return is B-latch, B-Pin, A-latch, A-Pin
        return [[result >> 3 & 0x01, result >> 2 &0x01], [result >> 1 & 0x01, result >>0 & 0x01]]

# --- Usage ---

if __name__ == "__main__":
    ds_pin = machine.Pin(22, machine.Pin.IN, machine.Pin.PULL_UP)

    ow = onewire.OneWire(ds_pin)
    ds_relay = DS2413(ow)

    roms = ow.scan()
    s_roms = ds_relay.scan()
    print("All one wire devices found")
    for rom in roms:
        print(hex(rom[0]), rom.hex(), rom, end ="\r\n")

    print()

# Turn both channels ON (Low)
    if len(s_roms) == 0:
        print("No relay available to control")
    else:
        for rom in s_roms:
            print("Relay devices")
            print(hex(rom[0]), rom.hex(), rom, end ="\r\n")
            
        rom = s_roms[0] # demo with single relay       
        while True:
            ds_relay.write_state(rom, [0, 0])
            print(rom.hex(),ds_relay.read_state(rom))
            time.sleep(1)
# Turn both channels OFF (High)
            ds_relay.write_state(rom, [1, 1])
            print(rom.hex(),ds_relay.read_state(rom))
            time.sleep(1)
    
