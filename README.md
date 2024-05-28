```
pip install dash
pip install pandas
pip install dash-bootstrap-components
```

Note: Best used with Python Virtual Environment:
Steps for Windows:
Create Virtual Environment: python -m venv venv
Activate Virtual Environment: .\venv\Scripts\activate
Install Requirements: pip install -r requirements.txt

If new packages are added or updated, do so with pip in the directory of the venv and update requirements.txt:
pip freeze > requirements.txt

Do not push venv folder (is already added to .gitignore)

If you get an error where "from astropy.stats import LombScargle" fails, change this import line in \venv\lib\site-packages\hrvanalysis\extract_features.py to "from astropy.timeseries import LombScargle"