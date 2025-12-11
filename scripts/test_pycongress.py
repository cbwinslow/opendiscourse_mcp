
import os
from pycongress import Congress

# Get the API key from the environment variables
api_key = "U71JFZEqNsiSranCdbrj4pZaobtoMtAnl18cIJc2"

# Initialize the Congress API client
congress = Congress(api_key)

# Fetch a single bill from the 118th Congress
try:
    bill = congress.bills.get(congress=118, bill_type='hr', bill_number=1)
    print(bill)
except Exception as e:
    print(f"An error occurred: {e}")
