#!/bin/sh
set -e
. venv/bin/activate

python3 xdfStreamer/xdfStreamer.py xdfStreamer/Hr_recording.xdf -hr -c &
python3 xdfStreamer/xdfStreamer.py xdfStreamer/abs_28.xdf -c &


wait