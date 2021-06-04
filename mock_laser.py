import re
import serial               # pyserial to communicate w/ laser
from serial.tools import list_ports

#exceptions
class FailureToOpenPortException(Exception):
    def __str__(self):
        return "laser port not open"

# laser faults
faults = {
    0 : "no error",
    1 : "temperature error",
    3 : "remote interlock error",
    4 : "constant power timeout"
}


# mock functions & variables

l_status = 0
l_ilk   = 1
l_fault = 0
l_power_set = 0.12
l_power_out = 0.

cmd_resp = {
    "@cob1"     : "OK",
    "cp"        : "OK",
    "f?"        : str(l_fault),
    "gsn?"      : "00000",
    "ilk?"      : str(l_ilk),
    "l?"        : str(l_status),
    "l0"        : "OK",
    "p"         : "OK",
    "p?"        : "{:.4f}".format(l_power_set),
    "pa?"       : "{:.4f}".format(l_power_out)
}

def init(laser_id):
    global l_ilk, cmd_resp
    l_ilk = 0
    l_status = 1
    l_power_out = l_power_set

    cmd_resp["ilk?"] = str(l_ilk)
    cmd_resp["l?"]  = str(l_status)
    cmd_resp["pa?"] = str(l_power_out)

def cmd(command):
    global l_power_set, l_status, cmd_resp

    if "p " in command:
        l_power_set = float(re.findall(r"\d+\.\d+", command)[0])
        cmd_resp["p?"] = "{:.4f}".format(l_power_set)
        command = "p"
    elif "l0" in command:
        l_status = 0;
        l_power_out = 0.
        cmd_resp["l?"]  = str(l_status)
        cmd_resp["pa?"] = str(l_power_out)

    return cmd_resp[command]

def shutdown():
    cmd("l0")


# simulate key box
def turn_key():
    global l_ilk, cmd_resp
    l_ilk ^= 1
    cmd_resp["ilk?"] = str(l_ilk)

    if not l_ilk and not l_fault :
        l_status = 1
        l_power_out = l_power_set
    else :
        l_status = 0;
        l_power_out = 0.

    cmd_resp["l?"]  = str(l_status)
    cmd_resp["pa?"] = str(l_power_out)


# real functions

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


# DEMO
if __name__ == "__main__":
    import os
    import time

    print("Starting laser")
    init(0)
    cmd("@cob1") # force restart

    print("getting serial number")
    print("Serial number was: {}".format(cmd("gsn?")))

    print("getting laser status: ")
    for i in range(10):

        if i == 5: turn_key();

        if int(cmd("l?")) == 1 : status = "ON"
        else :                   status = "OFF"
        print("laser is {}, \n\twith power setpoint at {} mW. ".format(status, 1e3*float(cmd("p?"))))
        print("\tcurrent output power is {} mW".format(1e3*float(cmd("pa?"))))
        fault = int(cmd("f?"))
        if fault:
            print(fault)
            break;

        time.sleep(.1)
        os.system('cls' if os.name=='nt' else 'clear')

    print("shutting down")
    shutdown()
