from microdot import Microdot, Response
from microdot import send_file
from utemplate.utemplate import Template
import gc
import os
import asyncio
import sys

import WAN_connect
from uio import StringIO

sys.path.append('local') if 'local' not in sys.path else sys.path
import host
import bg_thread

# =====================================
# module level debugs

bg_thread.debug = False
debug = True
info_on = True


station = WAN_connect.station

if not WAN_connect.connected():
    try:
        WAN_connect.connect(host.host)
    except Exception as e:
        print(e," : No Network, Unable to start server, Exiting")
        sys.exit()
        
print("IP address: ", station.ifconfig()[0])

bg_thread.set_station(station.config('mac').hex())

def log(*args):
    if debug:
        for item in args:
            print(item, end = "")
        print()
        
def info(*args):
    if info_on:
        for item in args:
            print(item, end = "")
            
boot = (__file__ == "main.py")

if boot:
    bg_thread.debug = False
    debug = False
    info_on = False
else:
    print("started from command line debug enabled")

filebase = 'Views/'

app = Microdot()
Response.default_content_type = 'text/html'

#@app.route('/')
#async def hello(request):
#    return html, 200, {'Content-Type': 'text/html'}


@app.route('/favicon.ico')
async def favicon(r):
    return '', 204

@app.route('/index.tpl')
@app.route('/')
async def index(req):
    return Template('index.tpl').render(host=host.host)

@app.route('/devconfig.tpl', methods=['GET', 'POST'])
async def devconfig(req):
    if req.method == 'POST':
        write_names(req)
    return Template('devconfig.tpl').render( devices = bg_thread.devices, dev_type = bg_thread.dev_type, dev_names = bg_thread.dev_names)

# ====================================================
#        Interface routines

@app.route('div-zero')
async def cause_error(*_):
    log("causing server error")
    x = 3/0

    
@app.route('ping-temp')
def read_temps(*_):
    return bg_thread.read('Temp')

@app.route('ping-volts')
def read_voltages(*_):
    return bg_thread.read('Volts')

@app.route('delete-all')
async def delete_all(*_):
    bg_thread.queue_add([bg_thread.delete_all])
    while bg_thread.queue:
        pass
    return "Devices Cleared"

@app.route('tools/get-device')
@app.route('get-device')
def get_device(r):
    if r.args.get('id') in bg_thread.devices:
        return {r.args['id']: bg_thread.devices[r.args['id']]}
    else:
        return {}
    
@app.route('tools/get-name')
@app.route('get-name')
def get_name(r):
    result = {}
    if 'name' in r.args:
        for dev in [dev for dev in bg_thread.devices if r.args['name'].lower() in bg_thread.devices[dev][' Name'].lower()]:
            result[dev] = bg_thread.devices[dev]
    return result

@app.route('tools/get')
@app.route('get') 
def get (r):
    if 'id' in r.args:
        return get_device(r)
    elif 'name' in r.args:
        return get_name(r)
    else:
        return {}
    
@app.route('ping-state')
def read_states(*_):
    return bg_thread.read('Relay')

@app.route('set-relay')
async def set_relays(*_):
    bg_thread.queue_add([bg_thread.set_relays])
    while bg_thread.queue:
        await asyncio.sleep(0.1)
    return bg_thread.r_relays()

@app.route('clear-relay')
async def clear_relays(*_):
    bg_thread.queue_add([bg_thread.clear_relays])
    while bg_thread.queue:
        await asyncio.sleep(0.1)
    return bg_thread.r_relays()

@app.route('ping-humidity')
def read_humidity(*_):
    return bg_thread.read('Humidity')

@app.route('refresh')
async def refresh(*_):
    results = {}
#    if r: results.setdefault('Analogue', r)
    
    
#    async for item in read_voltages(" "):
#        print(item)
    r = read_voltages()
    if r:
        results.setdefault('Voltages', r)
    else:
        log(" no read voltages") 
    results.setdefault('Temperatures', read_temps())
    r = read_states(" ")
    if r:
        results.setdefault('Relays', r)
    else:
        log(" no connected relays")
        
    r = read_humidity(" , ")
    if r:
        results.setdefault('Humidity', r)
        
    return dict(data=results)

def write_names(r):

    if True:
# 		Define the structured list we're editing
        dev_list = bg_thread.devices
        modify = False
        for device in dev_list:
            if dev_list[device][' Name'] != r.form.get(device+'_Name'):
                log("modifying ",device)
                dev_list[device][' Name'] = r.form.get(device+'_Name')
                modify = True
                
            if dev_list[device]['Connected'] == 'Native':
                if (device+'_hide' in bg_thread.dev_names) != (device+'_hide' in r.form):
                    if device+'_hide' in r.form:
                        bg_thread.dev_names[device+'_hide'] = 'checked'
                        bg_thread.dev_type[device] = bg_thread.dev_type[device] + "*"
                    else:
                        del bg_thread.dev_names[device+'_hide']
                        bg_thread.dev_type[device] = bg_thread.dev_type[device].replace("*", "")
                    log("modifying in hide for native devices")
                    modify = True
                    
            else:                            
                if device+"_hide" in r.form:
                    if dev_list[device]['Connected'] != True:
                        modify = bg_thread.delete(device)
                    else:
                        log("Not deleting devices as it is connected ",device)

            if (device+'_minmax' in bg_thread.dev_names) != (device+'_minmax' in r.form):
                if device+'_minmax' in r.form:
                    bg_thread.dev_names[device+'_minmax'] = 'checked'
                else:
                    del bg_thread.dev_names[device+'_minmax'] 
                modify = True
                
        if modify:
            log("devices changed writing out changes")

            try:
                with open('local/dev_list.py', 'w') as f:
                    f.write("dev_names = {") 
                    for device in dev_list: # this is itterating over the known devices                      
                        s = ("'"+ device+"'" + " : " + "'" + dev_list[device][' Name'] + "',\r\n")  
                        log("writing to file :",s)
                        f.write(s)
                        
                        if dev_list[device]['Connected']  == 'Native' and device+"_hide" in r.form:
                            s = "'"+device+"_hide' : 'Checked',\r\n"      
                            f.write(s)
                        
                    for key in [key for key in r.form if "_minmax" in key]:
                        s = "'"+key+"'" + " : 'Checked',\r\n"                      
                        f.write(s)
                        
                    f.write("}\r\n")
                            
            except Exception as e:
                log("Exception caught in writing names ", e)

                s = StringIO()    
                sys.print_exception(e, s)
                log(s.getvalue())
                raise HTTP_Error(500, str(e), r.path, s.getvalue())

    else:
        raise HTTP_Error(405, "Method not allowed", r.path, "No post data in form response")

#               end of interface routines
# ============================================================
# error handlers

class HTTP_Error(Exception):
    def __init__(self, number, message, file = "", comment = ""):
        self.message = message
        self.number = number
        self.file = file
        self.comment = comment
    def __str__(self):
        return str(self.number)+" : "+self.message
    @property
    def string(self):
        return str(self.number)+" : "+self.message
    
    @property
    def body(self):
        return (f'''<!DOCTYPE html>
        <html>
            <head>
            <meta charset="UTF-8">
            </head>
            <body>
            <div>
<h1>Error Report {self.number}</h1>
<p>{self.message}</p>
<pre style="word-wrap: break-word; white-space: pre-wrap;">
{self.comment}
</pre>
            </div>
            </body>
            </html>''')       
        
@app.errorhandler(HTTP_Error)
def http_error(request, exception):
    return exception.body, exception.number 

@app.errorhandler(404)
def not_found(request):
    return {'error': 'resource not found'}, 404

@app.errorhandler(ZeroDivisionError)
def division_by_zero(request, exception):
    s = StringIO()    
    sys.print_exception(exception, s)
    http_error = HTTP_Error(500, str(exception), request.path, s.getvalue())
    return http_error.body, http_error.number 


#               end of error handlers
# ============================================================
# routes

@app.route('serverip')
def server_ip(req):
    gc.collect()
    return [station.ifconfig()[0], gc.mem_free(), bg_thread.bg_count, bg_thread.running]

@app.route('error-test')
def raise_error(req):
    raise HTTP_Error(500, 'the error text', req.path, 'additional comment')

@app.route('/shutdown')
@app.route('/exit')
async def shutdown(request):
    info("background running is :",bg_thread.running)
    bg_thread.run_thread = False

    while bg_thread.running:
        pass
    info('bg Service Halted')
    request.app.shutdown()
    return 'The server is shutting down...'

@app.route('/not-found')
async def fnf(request):
    return 'Not found', 404


@app.route('/<path:path>')
async def static(request, path):
    if '..' in path:
        # directory traversal is not allowed
        return 'Not found', 404
    
    full_path = filebase + path    
    try:
        with open(full_path, "r") as f:
            pass
        found = True
    except OSError:
        return ('Resource not found: '+path), 404
    
    return send_file(filebase + path)

bg_thread.run_thread = True

app.run(debug=True, port = 80, host = station.ifconfig()[0])

