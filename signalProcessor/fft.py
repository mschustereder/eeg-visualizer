import numpy as np

def get_next_lowest_power_of_two(num):
    return 2 ** (num - 1).bit_length()

def calculate_fft(signal):
    window_length = len(signal)
    fft_result = np.fft.fft(signal, window_length)
    fft_magnitude = np.abs(fft_result)
    fft_magnitude_only_positive = fft_magnitude[:(window_length // 2)] # positive values are in first half
    fft_magnitude_normalized = fft_magnitude_only_positive / window_length
    return fft_magnitude_normalized

def calculate_frequencies(signal_len, sampling_rate):
    sampling_period = 1 / sampling_rate
    window_length = signal_len
    return np.fft.fftfreq(window_length, sampling_period)[:window_length // 2] # frequency vector