"""This Python script provides examples on using the E*TRADE API endpoints"""
from __future__ import print_function
from rauth import OAuth1Service
from datetime import datetime
import webbrowser
import json
import configparser
import sys
import requests
import time
import signal
import csv

# loading configuration file
config = configparser.ConfigParser()
config.read('config.ini')

def oauth():
    """Allows user authorization for the sample application with OAuth 1"""
    etrade = OAuth1Service(
        name="etrade",
        consumer_key=config["DEFAULT"]["CONSUMER_KEY"],
        consumer_secret=config["DEFAULT"]["CONSUMER_SECRET"],
        request_token_url="https://api.etrade.com/oauth/request_token",
        access_token_url="https://api.etrade.com/oauth/access_token",
        authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
        base_url="https://api.etrade.com")

    base_url = config["DEFAULT"]["PROD_BASE_URL"]

    # Step 1: Get OAuth 1 request token and secret
    request_token, request_token_secret = etrade.get_request_token(
        params={"oauth_callback": "oob", "format": "json"})

    # Step 2: Go through the authentication flow. Login to E*TRADE.
    # After you login, the page will provide a text code to enter.
    authorize_url = etrade.authorize_url.format(etrade.consumer_key, request_token)
    webbrowser.open(authorize_url)
    text_code = input("Please accept agreement and enter text code from browser: ")

    # Step 3: Exchange the authorized request token for an authenticated OAuth 1 session
    session = etrade.get_auth_session(request_token,
                                  request_token_secret,
                                  params={"oauth_verifier": text_code})

    collect_data(session, base_url)


def collect_data(session, base_url):

    def catch_sig_int(signum, frame):
        print("Ending data collection...")
        data_file.close()
        exception_file.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, catch_sig_int)

    symbols = generate_NYSE_symbols()

    start = symbols.index("BGCP") + 1
    number = len(symbols)

    data_file = open("observations.txt", "a")
    exception_file = open("exceptions.txt", "w")

    data_writer = csv.writer(data_file, delimiter=",")
    exception_writer = csv.writer(exception_file, delimiter=",")

    print("Collecting data...")

    for index in range(start, number):

        url = base_url + "/v1/market/quote/" + symbols[index] + ".json"

        try:
            response = session.get(url)
            data = response.json()
            data_writer.writerow([
			    data["QuoteResponse"]["QuoteData"][0]["Product"]["symbol"], 
			    data["QuoteResponse"]["QuoteData"][0]["All"]["yield"]
		    ])
            data_file.flush()
        except Exception as e:
            pass
            #exception_writer.writerow([str(e)])
            #exception_file.flush()

    data_file.close()
    exception_file.close()

def generate_NYSE_symbols():
    
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    symbols = []
    
    for v in alphabet:
        # Generate all one-letter symbols
        symbols.append("" + v)
        for w in alphabet:
            # Generate all two-letter symbols
            symbols.append("" + v + w)
            for x in alphabet:
                # Generate all three-letter symbols
                symbols.append("" + v + w + x)
                for y in alphabet:
                    # Generate all four-letter symbols
                    symbols.append("" + v + w + x + y)
                    for z in alphabet:
                        # Generate all five-letter symbols
                        symbols.append("" + v + w + x + y + z)

    return symbols

if __name__ == "__main__":
    oauth()
