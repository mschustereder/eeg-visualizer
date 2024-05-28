import matplotlib.pyplot as plt
from graph_callbacks import *

def get_sine(time_vector, frequency, amplitude):
    return amplitude * np.sin(2.0 * np.pi * frequency * time_vector)

sampling_rate = 1000 # Hz = s^(-1)
sampling_period = 1.0 / sampling_rate # s
num_of_samples = 2333  # num of samples

frequency_1 = 11
amplitude_1 = 13
frequency_2 = 140
amplitude_2 = 50
frequency_3 = 412
amplitude_3 = 30

time = np.linspace(0, sampling_period * num_of_samples, num_of_samples, endpoint=False)

signal = get_sine(time, frequency_1, amplitude_1) + get_sine(time, frequency_2, amplitude_2) + get_sine(time, frequency_3, amplitude_3)

frequencies, fft_magnitude = calculate_fft(signal, sampling_rate)

plt.figure(figsize=(12, 6))

# plot time signal
plt.subplot(2, 1, 1)
plt.plot(time, signal)
plt.title('Signal in time domain')
plt.xlabel('Time in s')
plt.ylabel('Amplitude')

# plot fft
plt.subplot(2, 1, 2)
plt.plot(frequencies, fft_magnitude)
plt.title('Signal in the frequency domain (DFT)')
plt.xlabel('Frequency in Hz')
plt.ylabel('Magnitude')

plt.tight_layout()

plt.savefig('fft_result.png')

print("Plot saved as 'fft_result.png'")
