class bidict(dict):
    def __init__(self, *args, **kwargs):
        super(bidict, self).__init__(*args, **kwargs)
        self.inverse = {}
        for key, value in self.items():
            self.inverse.setdefault(value, []).append(key) 

    def __setitem__(self, key, value):
        if key in self:
            self.inverse[self[key]].remove(key) 
        super(bidict, self).__setitem__(key, value)
        self.inverse.setdefault(value, []).append(key)        

    def __delitem__(self, key):
        self.inverse.setdefault(self[key], []).remove(key)
        if self[key] in self.inverse and not self.inverse[self[key]]: 
            del self.inverse[self[key]]
        super(bidict, self).__delitem__(key)

# test cases
if __name__ == '__main__':
    defs = {
        "123456": 'living',
        "098765": 'hall',
        }

    devices = bidict(defs)

    print("Devices : ", devices)
    print("Inverse : ", devices.inverse)

    devices["345678"] = 'kitchen'
    devices["666666"] = 'bedroom'
    devices["777777"] = 'kitchen'
    
    
    print()
    print("Devices new : ", devices)
    print("Inverse new : ", devices.inverse)

    devices.inverse['bedroom'] = "000000"

    print()
    print("Devices new2 : ", devices)
    print("Inverse new2 : ", devices.inverse)

    print(devices.inverse["kitchen"])
