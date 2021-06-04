import re
import scipy.interpolate    as interpolate


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
filename = "./mock_resources/exc785_Sample1_100pc_p2.txt"

# load the library
sys = platform.system()
WL = sizeof(c_voidp)*8
if sys == 'Windows':
    ccd = CDLL(".\\USBLC_DLL\\"+str(WL)+"Bit\\usblc"+str(WL)+".dll")
elif sys == 'Linux':
# ccd = CDLL("./USBLC_SO_Linux/"+str(WL)+"Bit/libusblc"+str(WL)+".so") # for the VM
    ccd = CDLL("./USBLC_SO_Jetson/libusblcjtn.so.1.2.0")
else :
    print("unexpected OS: " + sys)
    exit()
ccd.ls_geterrorstring.restype = c_char_p

# mock functions
def init(ccd_id):
    """
    establish connection w/ CCD and do a few basic settings
    """
    pass


def get_data():
    """
    get raw data from the CCD
    """
    f = open(filename, 'r')
    s = np.array(re.findall(r'(\d+\.\d+)', f.read()), dtype = np.float32)
    f.close();

    x, y = [], []
    for i in range(int(s.size/2)) :
        x.append(s[2*i])
        y.append(s[2*i+1])

    y = np.flip((np.array(y)*(integration_time_us))[0:-15])
    y = interpolate.interp1d(np.linspace(0, CCD_NB_PXL-1, y.size), y)(np.linspace(0, CCD_NB_PXL-1, CCD_NB_PXL))
    y = y + np.random.randint(0,500, y.size)
    y = np.maximum( y, 2*16-1).astype(int)

    time.sleep((integration_time_us+100)*1e-6)  # simulate integration vor verisimilitude
    return y


def set_integration_time(inttime_us):
    """
    set the integration time of the ccd
    """
    global integration_time_us
    integration_time_us = inttime_us

def shutdown():
    """
    shut down CCD
    """
    pass


def change_file(newfile):
    global filename
    filename = newfile

### DEMO
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    init(0)
    print("Device 0 initialized. Starting main loop")

    ax = plt.plot(np.zeros((1,CCD_NB_PXL)))

    for i in range(30) :
        data = get_data()

        if (np.max(data) > 55000) and integration_time_us > 4:
            set_integration_time(integration_time_us*.75)
        elif (np.max(data) < 15000)  and integration_time_us < 1e6:
            set_integration_time(integration_time_us/.75)

        plt.cla()
        plt.plot(data)
        plt.ylim((0, 2**16))
        plt.pause(.005)


    plt.show()

    plt.close()
