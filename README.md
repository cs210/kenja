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
curl localhost:8501/_stcore/metrics
```

## Deployment

[TO-DO] Will be looking into deploying onto a lightweight EC2 instance, routing to a url, and running!