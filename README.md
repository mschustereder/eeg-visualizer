## Best used with Python Virtual Environment:
### Steps for Windows:
- Create Virtual Environment: ```python -m venv venv```
- Activate Virtual Environment: ```.\venv\Scripts\activate```
- Install Requirements: ```pip install -r requirements.txt```

- If new packages are added or updated, do so with pip in the directory of the venv and update requirements.txt: ```pip freeze > requirements.txt```

### Steps for Linux:
- Create Virtual Environment: ```python -m venv venv```
- Activate Virtual Environment: ```source venv/bin/activate```
- Install Requirements: ```pip install -r requirements.txt```

- If new packages are added or updated, do so with pip in the directory of the venv and update requirements.txt: ```pip freeze > requirements.txt```

### Other remarks
- Do not push venv folder (is already added to .gitignore)

- If you get an error where "from astropy.stats import LombScargle" fails, change this import line in \venv\lib\site-packages\hrvanalysis\extract_features.py to "from astropy.timeseries import LombScargle"

## Programming the UI

### pyside6-designer

We are using the ```pyside6-designer```-tool. The following commands are important:

- Start the designer: ```pyside6-designer```
- Open a specific .ui-file in the designer: ```pyside6-designer <ui-file-name>.ui```
- Convert specific .ui-file to a python file: ```pyside6-uic <ui-file-name>.ui -o <wanted-python-file-name>.py```
- In our case: Convert .ui-file to the python file: ```pyside6-uic visualizer/visualizer.ui -o visualizer/visualizer.py```

## Infos regarding the channel_configuration.json file

This file should represent the relationship between the order of the sent data and the corresponding channel. So it translates which channel is first in the transmitted data array, which is second and so on. The numbers, or the key values itself are not really important, what matters is the order of the channels being correct.

The montage can be changed in globals.py with the USED_MNE_MONTAGE constant.

There is also the possibilty to try to read the channels info from the lsl stream which can be done by setting the global variable GET_LAYOUT_FROM_JSON to False. Note that for this to work, the channel names need to be configured beforehand.