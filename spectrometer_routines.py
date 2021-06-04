# imports
import time
import numpy                as np

import mock_laser as laser
import mock_ccd as ccd
from signal_treatment import *


# declare constants
LASER_PORT       =    1     #TODO: real value
CCD_PORT         =    1     #TODO: real value
STABILIZE_DELAY  =    1     # [s]   #TODO: real value
MIN_INT_TIME     =    1     # [us]
MAX_INT_TIME     =   30e6   # [us]
DEFAULT_INT_TIME =   1e4    # [us]  #TODO: real value
MIN_POWER        =   2e-3   # [us]
MAX_POWER        = 120e-3   # [us]
DEFAULT_POWER    =   5e-2   # [W]   #TODO: real value
NB_AVGS          =   5      #TODO: real value

init_calibration_params = np.array([-1e-4, .6, 60])  # TODO: experimental
calibration_ref_peaks   = np.array([465, 129, 1872]) # TODO: experimental

# global variables
integration_time        = DEFAULT_INT_TIME;
power                   = DEFAULT_POWER;
calibration_parameters  = np.array([0, 1, 0]);
dark_noise              = np.array([]);


def init():
    """
    initialize all devices
    """
    # start laser
    laser.init(LASER_PORT)              # establish connection w/ laser
    laser.stop()                        # make sure laser is off

    # start CCD, load init settings
    ccd.init(CCD_PORT)                  # establish connection w/ CCD


def calibrate():
    """
    calibrate the spectrometer on a sample of known composition
    """
    global integration_time
    global calibration_parameters
    global dark_noise

    # start laser and give it time to thermally stabilize
    laser.start(power)              # start laser
    time.sleep(STABILIZE_DELAY)     # wait for it to warm up

    # find optimal integration time on calibration sample
    ccd.set_integration_time(integration_time)
    data_raw = ccd.get_data()
    while detect_lowsignal(data_raw) and (integration_time < MAX_INT_TIME):
        integration_time = integration_time * 1.25;
        ccd.set_integration_time(integration_time)
        data_raw = ccd.get_data()
    while detect_saturation(data_raw) and (integration_time > MIN_INT_TIME):
        integration_time = integration_time / 1.25;
        ccd.set_integration_time(integration_time)
        data_raw = ccd.get_data()

    # get dark noise for this integration time
    laser.stop()
    time.sleep(STABILIZE_DELAY)
    ccd.change_file("./../spectra/dark_noise.txt")                              #TODO: remove this
    data_dn     = np.array([ccd.get_data() for i in range(NB_AVGS)])
    dark_noise  = np.mean(data_dn, 0)

    # calibration
    # 1) get spectrum of calibration sample
    laser.set_power(power)
    time.sleep(STABILIZE_DELAY)
    ccd.change_file("./../spectra/MySamples1/exc785_Sample1_100pc_p2.txt")      #TODO: remove this
    data_cs     = np.array([ccd.get_data() for i in range(NB_AVGS)])
    data_c      = np.mean(data_cs, 0) - dark_noise

    # 2) cleanup: smooth & remove baseline
    data_smooth = smooth(data_c, 7, "median")
    data_clean  = remove_baseline(data_smooth, [10**5, .05], "AsLS")

    # 3) calculate geometric correction
    calibration_parameters = find_correction(data_clean, calibration_ref_peaks, init_calibration_params, thresh=.5, deg=2)

    return data_raw, data_clean, dark_noise, calibration_parameters


def acquire_sample_spectrum():
    """
    acquire sample spectra from the CCD
    """
    global power
    global dark_noise

    # start laser and give it time to thermally stabilize
    laser.start(power)              # make sure laser is on
    time.sleep(STABILIZE_DELAY)

    # find optimal laser power for sample
    data_raw = ccd.get_data()
    while detect_lowsignal(data_raw) and (power < MAX_POWER):
        power = power * 1.25;
        laser.set_power(power)
        time.sleep(STABILIZE_DELAY)
        data_raw = ccd.get_data()
    while detect_saturation(data_raw) and (power > MIN_POWER):
        power = power / 1.25;
        laser.set_power(power)
        time.sleep(STABILIZE_DELAY)
        data_raw = ccd.get_data()

    # get spectrum of sample
    data_ss     = np.array([ccd.get_data() for i in range(NB_AVGS)])
    data_s      = np.mean(data_ss, 0) - dark_noise

    # cleanup: smooth & remove baseline
    data_smooth1 = smooth(data_s,       7, "median")
    data_smooth2 = smooth(data_smooth1, 5, "gaussian")
    data_clean   = remove_baseline(data_smooth2, [10**5, .05], "AsLS")

    return data_raw, data_clean


def shutdown():
    """
    shut down laser and CCD
    """
    laser.shutdown()
    ccd.shutdown()



# DEMO
if __name__ == "__main__":
    import re
    import scipy.interpolate    as interpolate
    import matplotlib.pyplot as plt


    init()  # start up devices

    for i in range(1): #number of samples
        ccd.change_file("./mock_resources/exc785_Sample1_100pc_p2.txt")
        raw_c, clean_c, dark_noise, calibration_parameters = calibrate()

        filenames = ["exc785_Sample1_100pc_p3.txt", "exc785_Sample1_100pc_p1.txt"]
        raw_d, clean_d = [], []
        for filename in filenames : #number of subsamples
            ccd.change_file("./mock_resources/" + filename)
            out_r, out_d = acquire_sample_spectrum()
            raw_d.append(out_r)
            clean_d.append(out_d)

        laser.stop()


    filenames.append("calibration sample")

    # get real calibration values for comparison
    f = open("./../spectra/MySamples1/exc785_Sample1_100pc_p2.txt", 'r')
    s = np.array(re.findall(r'(\d+\.\d+)', f.read()), dtype = np.float32)
    f.close();

    real = []
    for i in range(int(s.size/2)) :
        real.append(s[2*i])
    real = np.flip(np.array(real)[0:-15])

    fig, (ax1, ax2) = plt.subplots(2,1, constrained_layout=True)

    [ax1.plot(rd) for rd in raw_d]
    ax1.plot(raw_c)
    ax1.set_xlabel("pixels [px]")
    ax1.legend(filenames)

    [ax2.plot(np.polyval(calibration_parameters, np.linspace(0, cd.size-1, cd.size)), cd) for cd in clean_d]
    ax2.plot(np.polyval(calibration_parameters, np.linspace(0, clean_c.size-1, clean_c.size)), clean_c)
    ax2.set_xlabel("shift [cm^-1]")
    ax2.legend(filenames)

    plt.figure()
    plt.plot(np.linspace(0, clean_c.size-1, clean_c.size), np.polyval(calibration_parameters, np.linspace(0, clean_c.size-1, clean_c.size)))
    plt.plot(np.linspace(0, clean_c.size-1, clean_c.size), interpolate.interp1d(np.linspace(0, clean_c.size-1, real.size), real)(np.linspace(0, clean_c.size-1, clean_c.size)))
    plt.xlabel("pixels [px]")
    plt.ylabel("shift [cm^-1]")

    plt.show()
