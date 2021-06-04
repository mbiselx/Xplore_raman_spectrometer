## BEFORE RUNNING:
# on Windows, the CCD camera requires the installation of a driver. It's pretty straightforward.
# on Linux, the CCD camera requires the use of libusb-1.0
#	to use this library, you need either root access ("sudo python ccd.py"), or follow instructions in the manual:
# 	> 'etc/udev/rules.d'
#	> create a file '99-usblc.rules'
#	> add 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="19d1", ATTRS{idProduct}=="000e", GROUP="root", MODE="0666"'
#	> unplug and replug device. (and possibly run 'sudo udevadm control --reload-rules' ?)
#

import time
import platform
import numpy as np
from ctypes import *


# constant declarations
UC_TIMEOUT_DELAY = 10     # [100 ms]
CCD_NB_PXL       = 3648
MODE_ONE_SHOT    = 0      # camera modes


# global variables, because all good programs have global variables
integration_time_us = 100; # integration time in us


# load the library
sys = platform.system()
WL = sizeof(c_voidp)*8
if sys == 'Windows':
    ccd = CDLL(".\\USBLC_DLL\\"+str(WL)+"Bit\\usblc"+str(WL)+".dll")
elif sys == 'Linux':
# ccd = CDLL("./USBLC_SO_Linux/"+str(WL)+"Bit/libusblc"+str(WL)+".so") # for the VM
    ccd = CDLL("./USBLC_SO_Jetson/libusblcjtn.so.1.2.0")
else :
    print("unexpected system: " + sys)
    exit()
ccd.ls_geterrorstring.restype = c_char_p



# functions
def log_error(err) :
    print("A CCD Error {} Occurred : ".format(err) + ccd.ls_geterrorstring(err).decode('utf-8'))               # TODO: how should errors properly be logged ?
    ccd.ls_closedevice()
    exit()


def init(ccd_id):
    """
    establish connection w/ CCD and do a few basic settings
    """
    if (ccd.ls_currentdeviceindex() > -1) :	ccd.ls_closedevice()

    err = ccd.ls_setpacketlength(2*CCD_NB_PXL)            # this needs to be done, because datasheet
    if err : log_error(err)

    err = ccd.ls_opendevicebyindex(ccd_id)
    if err : log_error(err)

    err = ccd.ls_setmode(MODE_ONE_SHOT, UC_TIMEOUT_DELAY) # software triggered acquisition
    if err : log_error(err)
    err = ccd.ls_setstate(0, UC_TIMEOUT_DELAY)            # acquisition currently off
    if err : log_error(err)
    err = ccd.ls_setadcpga1(0)                            # set electronic gain to minimum
    if err : log_error(err)
    err = ccd.ls_setinttime(100, UC_TIMEOUT_DELAY);       # set exposure time
    if err : log_error(err)

def get_data():
    """
    get raw data from the CCD
    """
    err = ccd.ls_setstate(1, UC_TIMEOUT_DELAY)             # trigger acquisition
    if err : log_error(err)

    data_type = c_ushort
    buffer = (data_type*CCD_NB_PXL)()
    bytes_read = c_uint(0)

    if sys == 'Windows':	# read data (Windows)
        err = ccd.ls_waitforpipe(c_uint(100+int(integration_time_us/1000)))       # wait for acquisition completion
        if err : log_error(err)

        err = ccd.ls_getpipe(buffer, c_uint(sizeof(data_type)*len(buffer)), pointer(bytes_read))
        bytes_read = bytes_read.value
        if err : log_error(err)

    elif sys == 'Linux':	# read data (Linux)
        ccd.ls_waitforpipe(c_uint(100+int(integration_time_us/1000)))       	  # wait for acquisition completion

        bytes_read = ccd.ls_getpipe(buffer, c_uint(sizeof(data_type)*len(buffer)))

    if not (bytes_read == sizeof(data_type)*CCD_NB_PXL):
        print("ERROR: wrong number of bytes read: expected"+str(sizeof(data_type)*CCD_NB_PXL)+", got "+str(bytes_read))
        ccd.ls_closedevice()
        exit()

    return np.ctypeslib.as_array(buffer)


def set_integration_time(inttime_us):
    """
    set the integration time of the ccd
    """
    global integration_time_us
    integration_time_us = inttime_us
    err = ccd.ls_setinttime(int(integration_time_us), UC_TIMEOUT_DELAY); # set integration time
    if err: log_error(err)


def shutdown():
    """
    shut down CCD
    """
    ccd.ls_closedevice()




### DEMO
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    nb_dev = ccd.ls_enumdevices()
    print(str(nb_dev)+" devices connected")
    if nb_dev < 1 : exit()

    init(0)
    print("Device 0 initialized. Starting main loop")

    ax = plt.plot(np.zeros((1,CCD_NB_PXL)))

    while True:
    	data = get_data()

    	if (np.max(data) > 55000) and integration_time_us > 4:
    	    set_integration_time(0.75*integration_time_us)
    	elif (np.max(data) < 15000)  and integration_time_us < 1e6:
    	    set_integration_time(1.25*integration_time_us)

    	plt.cla()
    	plt.plot(data)
    	plt.ylim((0, 2**16))
    	plt.pause(.005)

    plt.show()
