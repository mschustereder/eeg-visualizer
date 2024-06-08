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