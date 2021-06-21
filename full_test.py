import tda 
from tda.auth import easy_client
from tda.client import Client
from tda.streaming import StreamClient
from tda.orders.equities import equity_buy_market
from tda.orders.equities import equity_sell_market
import atexit
import pytz
import datetime
from datetime import timedelta
import asyncio
from contextlib import suppress
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import ta
import numpy as np
import pandas as pd
import math
import logging
import locale
import threading
import time
import sys
import os 

class Bar:
    open = 0
    low = 0
    high = 0
    close = 0
    volume = 0
    date = datetime.datetime.now()
    def __init__(self):
        self.open = 0
        self.low = 0
        self.high = 0
        self.close = 0
        self.volume = 0
        self.date = datetime.datetime.now()

class Bot():
    barsize = 1
    currentBar = Bar()
    bars = []
    client = ''
    account_id = 0
    accountSize = 10000
    inPosition = True
    # indicators
    rsi = []
    # Params
    rsiPeriod = 14
    stream_client = ''
    status = None
    initialbartime = datetime.datetime.now().astimezone(pytz.timezone("America/New_York"))
    # Connect to TD Ameritrade
    def __init__(self):
        try:
            # Global vars
            API_KEY = 'FXPRVOIX4V3AADD3M6HJD9NY7WAOUGB5@AMER.OAUTHAP'
            REDIRECT_URL = 'https://localhost'
            TOKEN_PATH = 'token.pickie'
            # Create a new client
            self.client = tda.auth.easy_client(API_KEY,
            REDIRECT_URL,
            TOKEN_PATH,
            self.make_webdriver)
            # To place traders we must specify the account ID
            r = self.client.get_accounts()
            assert r.status_code == 200, r.raise_for_status()
            data = r.json()
            self.account_id = data[0]['securitiesAccount']['accountId']
            self.accountSize = data[0]['securitiesAccount']['currentBalances']['']
            self.stream_client = StreamClient(self.client, account_id=self.account_id)
            print("Successfully logged in your TD Ameritrade Account")
            # Get symbol info
            self.symbol = input("Enter the symobl you want to trade : ")
            # Get bar size
            self.barsize = int(input("Enter the barsize you want to trade in minutes : "))
            self.stream_client = StreamClient(self.client, account_id=self.account_id)
            asyncio.run(self.read_stream())
        except Exception as e:
            print(e)
    # Stream realtime_updates
    async def read_stream(self):
        try:
            await self.stream_client.login()
            await self.stream_client.quality_of_service(StreamClient,QOSLevel.EXPRESS)
            await self.stream_client.chart_equality_subs([self.symbol])
            self.stream_client.add_chart_equity_handler(self.onBarUpdate())
            print("Streaming real-time data now.")
            while True:
                try:
                    await self.stream_client.handle_message()
                except Exception as e:
                    print(e)
        except Exception as e:
                    print(e)
    # onBarupdate
    def onBarUpdate(self,msg):
        try:
            msg = json.dumps(msg, indent=4)
            msg = json.loads(msg)
            # Retrieve Bar
            for bar in msg['content']:
                # Check the strategy
                bartime = datetime.datetime.fromtimestamp(msg['timestamp']/1000).astimezone(pytz.timezone("America/New_York"))
                minute_diff = (bartime-self.initialbartime).total_seconds()/60.0
                self.currentBar.date = bartime
                # On_Bar close
                if (minute_diff > 0 and math.floor(minutes_diff)%self.barsize == 0):
                    self.initialbartime = bartime
                    # Calculate RSI
                    closes = []
                    for histbar in self.bars:
                        closes.append(histbar.close)
                    self.close_array = pd.Series(np.asarray(closes))
                    if (len(self.bars)) > 0:
                        # Calc RSI on bar close
                        # carefully watch
                        self.rsi = ta.momentum.rsi(self.close_array.self.rsiPeriod, True)
                        # Print last rsi
                        print(self.rsi[len(self.rsi)-1])
                        # code entry and exit 
                        # if the RSI <= 30 and we are not in a position, buy!
                        if self.rsi[len(self.rsi)-1] <= 30 and not inPosition:
                            # submit a buy order
                            # at bid, 1 share
                            order = tda.orders.equities.equity_buy_market(self.symbol, 1)
                            inPosition = True
                        # if the RSI >= 70 and we are in a position, sell!
                        if self.rsi[len(self.rsi)-1] >= 70 and not inPosition:
                            # submit a buy order
                            # at bid, 1 share
                            order = tda.orders.equities.equity_sell_market(self.symbol, 1)
                            inPosition = False
                    # Bar cloesd append
                    self.currentBar.close = bar['CLOSE_PRICE']
                    print("New bar!")
                    self.bars.append(self.currentBar)
                    self.currentBar = Bar()
                    self.currentBar.open = bar['OPEN_PRICE']
                # Build realtime bar
                if (self.currentBar.open == 0):
                    self.currentBar.open = bar['OPEN_PRICE']
                if (self.currentBar.high == 0 or bar['HIGH_PRICE'] > self.currentBar.high):
                    self.currentBar.high = bar['HIGH_PRICE']
                if (self.currentBar.low == 0 or bar['LOW_PRICE'] > self.currentBar.low):
                    self.currentBar.low = bar['LOW_PRICE']
        except Exception as e:
            print(e)
    # Connect to TD Ameritrade OAUTH Login
    def make_webdriver(self):
        # Import selenium here because it's slow to import
        from selenium import  webdriver
        driver = webdriver.Chrome(ChromeDriverManager().install())
        atexit.register(lambda: driver.quit())
        return driver
        
# Start Bot
bot = Bot()
