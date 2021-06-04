import numpy                as np
from scipy import sparse
import scipy.signal         as signal
import scipy.ndimage        as filter

CCD_SATURATION_VAL = 2**16-1
epsil = -10000

def detect_saturation(x):
    """
    detect if the CCD is saturated
    """
    if np.max(x) >= (CCD_SATURATION_VAL + epsil):
        return True
    else:
        return False

def detect_lowsignal(x):
    """
    detect if the CCD singal is low
    """
    if np.max(x) <= (CCD_SATURATION_VAL/3):
        return True
    else:
        return False

def normalize(x, ord=np.inf):
    """ normalize the spectrum
        - ord = 1   : normalize the area under the spectrum
        - ord = 2   : normalize the energy of the spectrum
        - ord = inf (default) : normalize the peak of the spectrum
    """
    y = x/np.linalg.norm(x, ord)
    return y


def smooth(x, size, type="median"):
    """ smooth the spectrum to remove noise
        - type = "median" (default)
        - type = "gaussian"   : gaussian filter
        - type = "avg"        : moving avverage
    """
    if type=="median":
        y = signal.medfilt(x, size)
    elif type=="gaussian":
        y = filter.gaussian_filter1d(x, size)
    elif type=="avg":
        y = filter.uniform_filter1d(x, size)
    else:
        error("no such smoothing filter currently implemented")
    return y


def remove_baseline(x, pow, type="AsLS"):
    """ remove the baseline of a spectrum
        - type = "AsLS" (default) : "Asymmetric Least Squares Smoothing" by Eilers & Boelens (2005) (pow = [lambda, p])
        - type = "polysub"  : subtract minimum polynomial background (pow = degree of polynomial)
        - type = "bandpass" : apply bandpass filter of 2 gaussians (power = [sigma1 sigma2])
    """
    if type=="AsLS":
        # Eilers, P. and Boelens, H., Baseline Correction with Asymmetric Least Squares Smoothing, 2005
        # https://stackoverflow.com/questions/29156532/python-baseline-correction-library
        L = len(x)
        D = sparse.diags([1,-2,1],[0,-1,-2], shape=(L,L-2))
        w = np.ones(L)
        for i in range(20): # arbitrary iteration value. should iterate until stabilisation, but at 10 iterations it's close enough
            W = sparse.spdiags(w, 0, L, L)
            Z = W + pow[0] * D.dot(D.transpose())
            z = sparse.linalg.spsolve(Z, w*x)
            w = pow[1] * (x > z) + (1-pow[1]) * (x < z)
        y = x - z
    elif type=="polysub":
        idx = np.concatenate((np.array([0, x.size-1]), signal.find_peaks(-x)[0]))
        p = np.polyfit(x, -x[idx], np.minimum(pow, x.size-1))
        y = x + np.polyval(p, np.linspace(0, x.size-1, x.size))
    elif type=="bandpass":
        y = filter.gaussian_filter1d(x, np.min(pow)) - filter.gaussian_filter1d(x, np.max(pow))
    else:
        error("no such baseline removal filter currently implemented")
    return y


def find_correction(x, model, initial_guess, thresh=.5, deg=2):
    """ find the polynomial geometric distortion on the signal, using prior
        knowledge of the peak locations and heights for this substance.
        model=[peaks_location, peaks_height] for a known substance
        initial_guess : rough à priori estimate of the correction_parameters
        calculate correction_parameters and return for future use
    """
    # find the peaks in the data and sort them by size
    unsorted_peaks=signal.find_peaks(x, height=np.mean(x)+thresh*np.std(x), distance=20)[0]
    peaks_px = unsorted_peaks[x[unsorted_peaks].argsort()[::-1]]
    peak_wn_guess = np.polyval(initial_guess, peaks_px.astype(float))

    # find the closest and largest detected peak to each peak of the model
    corresponiding_detected_peak_idx = [];
    size_penalty = np.linspace(0, peak_wn_guess.size-1, peak_wn_guess.size)**2
    M = np.minimum(peaks_px.size, model.size)
    for m in range(M):
        closeness_penalty = np.abs(peak_wn_guess - model[m])
        optimum = np.argmin(closeness_penalty + size_penalty)
        peak_wn_guess[optimum] = np.inf                 # make cost = inf, so we don't use the same peak twice
        corresponiding_detected_peak_idx.append(optimum)

    # calculate the correction correction_parameters
    N = np.minimum(deg, M-1)
    correction_parameters = np.polyfit(peaks_px[corresponiding_detected_peak_idx], model[0:M], N);

    return correction_parameters
