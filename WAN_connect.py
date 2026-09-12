import network
import time
import sys
from machine import Pin
import binascii
sys.path.append("local")
from WiFi_nets import WiFi_nets

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

debug = True

led = Pin('LED', Pin.OUT)

station = network.WLAN(network.STA_IF)

class WANError(Exception):
    def __init__(self, number, message):
        self.msg = message
        self.number = number
    def __str__(self):
        return str(self.number)+" : "+self.msg
    
    @property
    def string(self):
        return str(self.number)+" : "+self.msg


def connected():
    return station.isconnected()

# drop previouse WAN connection and establish new one

def connect(host, debug = False):

    if connected():
        return True
      
    station.active(True)
    station.config(pm = 0xa1114)

    available_nets = station.scan()
    if debug:
       print("Scanning for Wi-Fi networks...")
       for ssid, bssid, channel, rssi, security, hidden in wlan.scan():
            # Convert bytes data to clean strings
            name = ssid.decode('utf-8') if ssid else "<Hidden Network>"
            mac = binascii.hexlify(bssid, ':').decode('utf-8')    
            print(f"SSID: {name:20} | MAC: {mac} | Ch: {channel:2} | RSSI: {rssi} dBm")    

    network.hostname(host)

    known_net = False
    for try_net in available_nets:
        net = try_net[0].decode("utf-8")
        if debug: print("Checking net ", net)
        if net in WiFi_nets:
            if debug: print("Connecting to net ",net)
            known_net = net
            station.connect(net, WiFi_nets[net])
            print("waiting for wan connection")
            n = 15
            while not station.isconnected():
                print(n)
                led.value(led.value() ^ 1)
                time.sleep(0.25)
                n -= 1
                if n == 0:
                    break
            if station.isconnected():
                return True
        
    if not known_net:
        raise WANError(45, "No known SSID found")
        
    return False
    
    
def re_connect(host, debug = False):
    station.disconnect()
    station.active(False)   
    return connect(host, debug)

if __name__ == '__main__':
    
    debug = True

    print("Station connection state ", connected())
    print("host: ", network.hostname())
    

    try:
        print("Conection status ", re_connect("host",debug))
    except WANError as e:
        sys.print_exception(e)
        print("1:",e.msg)
        print("2:",e.string)
        print("3:",e.errno)
           
    
    print("host: ", network.hostname())
    print("Connected: ", station.isconnected())
    print("ssid: ", station.config('ssid'))
    print("IP address: ", station.ifconfig()[0])

    
