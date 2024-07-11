## Environment Setup (Shortcut):
Requirements: 
* git 
* Python Interpreter (Version > 3.9)

Copy paste the following code block into a terminal/shell in your desired folder where you want the project to run. Note that there is a possibilty that you have to change the ```python``` keyword to ```python3``` or ```python.exe```- this depends on your installation of python and the configuration in the system environment variables.
### Windows:
```
git clone https://github.com/mschustereder/eeg-visualizer.git;
cd eeg-visualizer;
python -m venv venv;
.\venv\Scripts\activate;
pip install -r requirements.txt;
```
### Linux:
```
git clone https://github.com/mschustereder/eeg-visualizer.git;
cd eeg-visualizer;
python -m venv venv;
source venv/bin/activate;
pip install -r requirements.txt;
```

## Testing the application (Shortcut)
### Windows:
Run:
```
python stream.py;
python main.py
```

### Linux:
Run:
```
./start_test_streams.sh;
python main.py
```

### Issues
If you get an error where "from astropy.stats import LombScargle" fails, change this import line in \venv\lib\site-packages\hrvanalysis\extract_features.py to "from astropy.timeseries import LombScargle"

### For developers
- Do not push venv folder (is already added to .gitignore)
- If new packages are added or updated, do so with pip in the directory of the venv and update requirements.txt: ```pip freeze > requirements.txt```

## Steps to use the Application:

We have to differentiate between Offline and Online usage. In the Offline Environment we stream XDF files of the recorded data, whereas in Online usage the EEG and the heart rate monitor stream in Real-time.

### Offline Usage

In the xdfStreamer folder you can find 3 XDF files, which can be used to test the application. "bitbrain_eeg_recording.xdf" is a Bitbrain 16-channel (250Hz) EEG ecording of a resting human being. To compare this meaningful data to a useless recording there is also a "Noise_eeg_recording.xdf" which was recorded on the same Bitbrain EEG simply laying on the table. The third XDF file is called "Hr_recording.xdf" and holds heart related data recorded with a chest strap of a resting human being.

1. Start the streams - Options:
    * Call ```./start_test_streams.sh```(Linux) or ```python stream.py```(Windows) in the root directory: this will start streaming "bitbrain_eeg_recording.xdf" and "Hr_recording.xdf". The filenames can be changed to custom files by changing the path in the respective run scripts.
    * Start the streams manually by calling ```python xdfStreamer/xdfStreamer.py <file_directory> -c``` for the EEG stream and ``` python xdfStreamer/xdfStreamer.py <file_directory> -hr -c``` for the heart stream. The ```-c``` (continous) option repeats the streams once they end, and can be neglected if not wanted. 

2. Start the application:
    * Execute the main.py by calling ```python main.py``` or using the IDE to run the python script. 

3. Selcet the correct streams:
    * After a short waiting period a prompt appears where one can select the correct stream for EEG, HR and RR. If they do not appear immediately click "Search again".

4. Use the UI to change the parameters.

### Online Usage

1. Start the EEG stream:
    * Based on the EEG application find a way to stream the data via LSL. We used a Bitbrain EEG - with this device the steps to follow are:
        * Start the Bitbrain Viewer Software
        * Connect the EEG via Bluetooth with your PC or laptop
        * Click "connect" and select your EEG from the list
        * Tick the "Enable LSL server" checkbox
        * Click "Start"

2. Start the HR/RR stream:
    * In the folder xdfStreamer one can find the "ble_streamer.py" script which connects to a Bluetooth Low Energy device - in this case the chest straps - and streams the data via LSL. To make it work, put in the correct name and address of the device starting from line 216 and execute the script by either calling ```python xdfStreamer/ble_streamer.py``` or using the IDE to run the script. 

3. Start the application:
    * Execute the main.py by calling ```python main.py``` or using the IDE to run the python script. 

4. Select the correct streams:
    * After a short waiting period a prompt appears where one can select the correct stream for EEG, HR and RR. If they do not appear immediately click "Search again".

5. Use the UI to change the parameters.


## Infos regarding the channel_configuration.json file

This file should represent the relationship between the order of the sent data and the corresponding channel. So it translates which channel is first in the transmitted data array, which is second and so on. The numbers, or the key values itself are not really important, what matters is the order of the channels being correct.

The montage can be changed in globals.py with the USED_MNE_MONTAGE constant.

There is also the possibilty to try to read the channels info from the lsl stream which can be done by setting the global variable GET_LAYOUT_FROM_JSON to False. Note that for this to work, the channel names need to be configured beforehand.

