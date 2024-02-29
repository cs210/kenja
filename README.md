# 📚 🐛 Bookworm
For all our booklovers out there: give us a description of a book you're dying to find, and we'll give you recs!

## Set-Up

Simple set-up: create a virtual environment and install dependencies.
```bash
python3 -m venv env
source env/bin/activate
python3 -m pip install -r requirements.txt
```

## To Run

If you've installed all the dependencies above, run:

```bash
streamlit run app.py
```

## Telemetry

To query telemetry data, run the following after running Streamlit:

```bash
curl kenja.pro:8501/_stcore/metrics
```

## Coding Standards

We use [Black](https://github.com/psf/black) as our Python code formatter and [Flake8](https://flake8.pycqa.org/en/latest/) as our linter. To use both, install all of the requirements. To check Black, try:

```bash
black .
```

To check Flake8, try:
```bash
flake8 .
```

We also set up `setup.cfg` to configure Flake8 to meet Black style.

## Deployment

Notes on deployment are [here](https://github.com/cs210/2024-Unusual-1/wiki/Prototyping:-A-New-Shopping-Experience)!