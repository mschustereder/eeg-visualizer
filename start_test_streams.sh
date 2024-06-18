#!/bin/sh
set -e
. venv/bin/activate

python3 xdfStreamer/xdfStreamer.py xdfStreamer/Hr_recording.xdf -hr -c &
python3 xdfStreamer/xdfStreamer.py xdfStreamer/bitbrain_eeg_recording_13.06.24.xdf -c &


wait