# Requests
import requests

x = requests.get('https://www.cellartracker.com/notes.asp?iWine=3')

print(x.text)