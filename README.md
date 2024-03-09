# 📚 🐛 Bookworm
For all our booklovers out there: give us a description of a book you're dying to find, and we'll give you recs!

## Set-Up

### Frontend
To set up our frontend, enter the `frontend` directory and then install dependencies:
```bash
npm install
```

### Backend
To set up our backend, create a virtual environment and install dependencies.
```bash
python3 -m venv env
source env/bin/activate
python3 -m pip install -r requirements.txt
```

## To Run

First, run the backend API:
```bash
cd backend
uvicorn api:app --reload
```

Then, run the frontend:
```bash
cd frontend
npm run start
```

## Deployment

For deployment, run the backend API on our EC2 instance. To deploy the frontend, run:
```bash
cd frontend
sudo sh deploy.sh
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