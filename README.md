# 🛍️ 🔍 Kenja
Kenja is building AI search for e-commerce.

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

Assuming all requirements are installed, first, run the backend API:
```bash
cd backend
uvicorn api:app --reload
```

Then, run the frontend:
```bash
cd frontend
npm run start
```

## Coding Standards

### Backend

We use [Black](https://github.com/psf/black) as our Python code formatter and [Flake8](https://flake8.pycqa.org/en/latest/) as our linter. To use both, install all of the requirements. To check Black, try:

```bash
black .
```

To check Flake8, try:
```bash
flake8 .
```

We also set up `setup.cfg` to configure Flake8 to meet Black style.

## Frontend

We use [ESLint](https://eslint.org/) for linting and use the default VSCode formatter for formatting. 

## Deployment

Notes on deployment are [here](https://github.com/cs210/2024-Unusual-1/wiki/Prototyping:-A-New-Shopping-Experience)!