import serial               # pyserial to communicate w/ laser
from serial.tools import list_ports

# laser_commands = {
#     "l?" :  "get laser on/off state"
#     "lo" :  "laser off "
#     "@cob1 " :  "restart laser (including warm-up)"
#     "p" : "set output power"
#     "slc": "set drive current"
#     "cp" : "Enter constant power mode"
#     "ci" : "Enter constant current mode"
#     }


# global variables
laser_serial = serial.Serial();

#exceptions
class FailureToOpenPortException(Exception):
    def __str__(self):
        return "laser port not open"

# laser faults
faults = {
    0 : "no error",
    1 : "temperature error",
    3 : "remote interlock error",
    4 : "constant power timeout" }

# functions
def init(laser_id):
    """
    initialize the serial port through which we will communicate with the laser
    """
    global laser_serial
    baud = 112500
    try :
        # Connect to the slected port port, baudrate, timeout in milliseconds
        laser_serial = serial.Serial( list_ports.comports()[laser_id].device, baud, timeout=1)
        if not laser_serial.is_open:
            raise FailureToOpenPortException()

    except Exception as e:
        print("Exception: " + str(e))
        if laser_serial.is_open:
            laser_serial.close()
        exit()

def cmd(command):
    """
    send a string as a command to the laser via the serial port
    """
    global laser_serial
    try:
        if (not laser_serial) or (not laser_serial.is_open):
            raise FailureToOpenPortException()
        laser_serial.reset_input_buffer()
        laser_serial.write( (command + "\r\n").encode('ascii') ) # encode('ascii') converts python string to a binary ascii representation

        result = laser_serial.readline().decode('ascii')
        return result

    except Exception as e:
        print("Exception: " + str(e))
        shutdown()
        exit()

def shutdown():
    """
    shut down laser & com port
    """
    global laser_serial
    if laser_serial.is_open:
        cmd("l0") #turn laser off?
        laser_serial.close()


def start(power_W=0.120):
    """
    start the laser
    """
    cmd("@cob1")    # force restart

    fault = int(cmd("f?"))
    if fault:
        print("ERROR: Laser fault {} : {}".format(fault, faults[fault]))
        exit()

    if int(cmd("ilk?")): # get remote interlock state
        print("ERROR: interlock not closed")
        return

    set_power(power_W)

def stop():
    """
    stop the laser without turning it off (i.e. set the power output to 0 W)
    """
    set_power(0)


def set_power(power_W):
    """
    set the power setpoint for the laser to track in [W]
    """
    if power_W > 0.120 : power_W = 0.120
    elif power_W < 0.  : power_W = 0.
    if not ("OK" in cmd("cp")):
        print(answer)
        shutdown()
        exit()
    if not ("OK" in cmd("p {:.4f}".format(float(power_W)))):
        print(answer)
        shutdown()
        exit()


def get_power():
    """
    get the current output power in [W]
    """
    return float(cmd("pa?"))



# DEMO
if __name__ == "__main__" :
    import os
    import time

    try:
        devices_found = list()
        devices_found.extend( list_ports.comports() )

        if len(devices_found) < 1:
            print("ERROR: No devices found.")
            exit()

        print("Listing devices found: ")
        for i, device in enumerate(devices_found):
            print( "{} : ({}, {}, {})".format(i, device.device, device.description, device.hwid ) )

    except Exception as e:
        print("Exception: " + str(e))
        shutdown()

    print("Starting laser")
    init(0)
    cmd("@cob1") # force restart

    print("getting serial number")
    print("Serial number was: {}".format(cmd("gsn?")))

    print("getting laser status: ")
    while True:
        if int(cmd("l?")) == 1 : status = "ON"
        else :                   status = "OFF"
        print("laser is {}, \n\twith power setpoint at {} mW. ".format(status, 1e3*float(cmd("p?"))))
        print("\tcurrent output power is {} mW".format(1e3*float(cmd("pa?"))))
        fault = int(cmd("f?"))
        if fault:
            print(fault)
            break;

        time.sleep(.5)
        os.system('cls' if os.name=='nt' else 'clear')

    print("shutting down")
    shutdown()
