import subprocess

subprocess.Popen(['start', 'cmd', '/k', 'python', "xdfStreamer/xdfStreamer.py", "xdfStreamer/Hr_recording.xdf", "-hr", "-c"], shell=True)
subprocess.Popen(['start', 'cmd', '/k', 'python', "xdfStreamer/xdfStreamer.py", "xdfStreamer/bitbrain_eeg_recording.xdf", "-c"], shell=True)

