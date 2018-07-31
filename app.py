import os
import time
import urllib

import requests
from flask import Flask, redirect, render_template, request, url_for

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

CLIENT_DATA = {}


def retrieve_balance(account_id, access_token) -> str:
    auth_header = {'Authorization': f'Bearer {access_token}'}
    res = requests.get(f'https://api.truelayer.com/data/v1/accounts/{account_id}/balance', headers=auth_header)

    # blow up if cannot retrive balance for an account
    res.raise_for_status()

    balance = res.json()['results'][0]

    return {
        'currency': balance["currency"],
        'value': balance["available"],
    }


############################
# Flask app                #
############################

app = Flask(__name__)


@app.route('/show_balance', methods=['GET'])
def show_balance():
    if len(CLIENT_DATA) == 0:
        return redirect(url_for('signin'))

    access_token = CLIENT_DATA['token']['access_token']

    auth_header = {'Authorization': f'Bearer {access_token}'}

    res = requests.get('https://api.truelayer.com/data/v1/accounts', headers=auth_header)

    # blow up if cannot retrive accounts
    res.raise_for_status()

    accounts = {}
    for account in res.json()['results']:
        acc_id = account['account_id']
        acc_name = account['display_name']
        balance = retrieve_balance(acc_id, access_token)
        accounts[acc_id] = {
            'balance': balance,
            'name': acc_name,
        }

    # render accounts
    return render_template('accounts.html', accounts=accounts)


@app.route('/signin', methods=['GET'])
def sign_in():
    query = urllib.parse.urlencode({
        'response_type': 'code',
        'response_mode': 'form_post',
        'client_id': CLIENT_ID,
        'scope': 'accounts balance offline_access',
        'nonce': int(time.time()),
        'redirect_uri': REDIRECT_URI,
        'enable_mock': 'true',
    })

    auth_uri = f'https://auth.truelayer.com/?{query}'

    return f'Please sign in <a href="{auth_uri}" target="_blank">here.</a>'


@app.route('/signin_callback', methods=['POST'])
def handle_signin():
    # you should probably be using a db
    global CLIENT_DATA

    access_code = request.form['code']
    body = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': access_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    }
    res = requests.post('https://auth.truelayer.com/connect/token', data=body)

    CLIENT_DATA['token'] = res.json()

    print(f"Got token: {CLIENT_DATA['token']}")

    return redirect(url_for('show_balance'))
