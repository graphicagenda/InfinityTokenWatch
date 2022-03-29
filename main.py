import os
import requests
import json
import sqlite3
from datetime import datetime
from collections import namedtuple 
from notifypy import Notify
# TODO from pycoingecko import CoinGeckoAPI

__location = os.getcwd()
notification = Notify(
    custom_mac_notificator="./resource/imt/Infinity Mining Token Alert.app"
)

'''
Etherscan Token Tracker: https://etherscan.io/token/0xc66e9e56cfe33471f0826b2531b5ba490de4732a
Etherscan Token DeFi Chart: https://etherscan.io/dex/uniswapv2/0x8c729123bbae7219a989365d5ea046a5e64264f5
IMT Dextools: https://www.dextools.io/app/ether/pair-explorer/0x8c729123bbae7219a989365d5ea046a5e64264f5
'''


Langfile = namedtuple('Langfile', ['which', 'head', 'agent', 'action', 'perform'])
Token = namedtuple('Token', ['name', 'decimals', 'contract', 'uniswap'])
Network = namedtuple('Network', ['name', 'latestblock'])
API = namedtuple('API', ['token'])


class IMTToken:
    def __init__(self, start_block=14176196):
        # @TODO CG: cg = CoinGeckoAPI()
        self.contract = '0xC66e9E56cFe33471F0826B2531b5BA490de4732A'
        self.lp_address = '0x8c729123bbae7219a989365d5ea046a5e64264f5'
        self.supply = 5000000000
        self.decimals = 18
        self.start_block = start_block  # 14176196
        self.end_block = 99999999
        self.api_key = os.environ['etherscan_api_key']
        self.url = self.etherscan_endpoint()
        # TODO Get more than just the newest set of last_tx and reverse it!
        self.data = self.request_data(self.url)
        if len(self.data) >= 1:
            self.last_tx = self.data[0]

        # @TODO CG: get_token_price = cg_endpoint()
        # @TODO CG: cg = get_token_price[CONTRACT]

    @staticmethod
    def request_data(url):
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
        )

        return json.loads(r.text)['result']

    def etherscan_endpoint(self):
        return f"https://api.etherscan.io/api?module=account&" \
              f"action=tokentx&" \
              f"contractaddress={self.contract}&" \
              f"sort=desc&page=1&" \
              f"apikey={self.api_key}&" \
              f"startblock={self.start_block}&" \
              f"endblock={self.end_block}&" \
              f"page=1"


class Transaction:
    def __init__(self, etherscan_data, lp_address):
        self.eth_block = int(etherscan_data['blockNumber'])
        self.dt = get_formatted_time(int(etherscan_data['timeStamp']))

        self.__buy_lang = Langfile('buy', 'BUY!!!', etherscan_data['to'], 'Purchased', 'Received')
        self.__sell_lang = Langfile('sell', 'Sell :(', etherscan_data['from'], 'Sold', 'Sent')
        self.__transfer_lang = Langfile('transfer', 'Transfer', etherscan_data['from'], 'Sent', 'Moved')

        self.lang = {'buy': self.get_buy_lang(), 'sell': self.get_sell_lang(), 'transfer': self.get_transfer_lang()}

        self.trigger = get_trigger(etherscan_data['from'], etherscan_data['to'], lp_address, self.lang)
        self.wallet_address = etherscan_data['from'] if self.trigger == self.lang['sell'] else etherscan_data['to']

        self.raw_value = int(int(etherscan_data['value']) * (.1 ** int(etherscan_data['tokenDecimal'])))
        self.raw_full_amount = self.raw_value / .89

        self.IMT_amount = "{:,}".format(self.raw_value)
        self.full_IMT_amount = "{:,}".format(int(self.raw_full_amount))
        # @TODO CG: full_IT_amount_usd = f"${'{:,.0f}'.format(raw_full_amount * float(cg_data['usd']))}"

        # IT_Quotes
        # @TODO CG: quote = f"${'{:.5f}'.format(cg_data['usd'])}"
        # @TODO CG: vol = f"${'{:,.0f}'.format(cg_data['usd_24h_vol'])}"
        # @TODO CG: mc = f"${'{:,.0f}'.format(cg_data['usd'] * int(SUPPLY))}"

        self.title = f'{self.trigger.head} {self.trigger.perform} {self.IMT_amount} IMT'

        self.squares = int( (self.raw_full_amount / .1 ** -5 ) / 3.33 )
        self.squares = self.squares if self.squares > 0 else 1

        self.message = f"{self.dt} [#{self.eth_block}]"
        # @TODO CG: message += f"\nMarket Cap {mc} ..."
        # @TODO CG: message += f"\nPrice: {quote} .. 24h Vol. {vol}"
        self.message += f"\n{self.trigger.action} {self.full_IMT_amount} IMT\n"  # @TODO CG: ({full_IT_amount_usd})
        self.message += f"{'🟩' * self.squares if self.trigger.which != 'sell' else '🟥' * self.squares}"

    def __str__(self):
        return f"{self.message}\n" \
               f"chain = {'Ethereum'}\n" \
               f"block = {self.eth_block}\n" \
               f"date = {self.dt}\n" \
               f"token = {'IMT'}\n" \
               f"amount = {self.IMT_amount}\n" \
               f"which = {self.trigger.which}\n" \
               f"head = {self.trigger.head}\n" \
               f"agent = {self.trigger.agent}\n" \
               f"action = {self.trigger.action}\n" \
               f"perform = {self.trigger.perform}\n"

    def get_buy_lang(self):
        return self.__buy_lang

    def get_sell_lang(self):
        return self.__sell_lang

    def get_transfer_lang(self):
        return self.__transfer_lang


"""
@TODO once CG is in place 
def cg_endpoint():
    '''
    {'0x7fe4fbad1fee10d6cf8e08198608209a9275944c': {'usd': 0.00513434, 'usd_24h_vol': 73169.88252678538,
                                                    'usd_24h_change': -8.649695532882431,
                                                    'last_updated_at': 1637997550}}
    '''
    return cg.get_token_price(id='ethereum', vs_currencies='usd',
                       contract_addresses='0x7fe4fbad1fee10d6cf8e08198608209a9275944c', include_24hr_vol=True,
                       include_24hr_change=True, include_market_cap=False, include_last_updated_at=True)                    
"""


def notify(sound, address, title, text):
    notification.application_name = title
    notification.title = address
    notification.message = text
    notification.audio = sound
    notification.send()


def change_working_dir():
    os.chdir(__location)


def request_last_tx(url):
    r = requests.post(
        url,
        headers={"Content-Type": "application/json"},
    )
    # TODO Get more than just the newest set of last_tx and reverse it!
    return json.loads(r.text)['result'][0]


def get_formatted_time(timestamp):
    dateFormat = "%m/%d/%Y %I:%M%p"
    return datetime.fromtimestamp(timestamp).strftime(dateFormat)


def get_trigger(_from, _to, _lp, lang):
    if _from == _lp:
        return lang['buy']
    elif _to == _lp:
        return lang['sell']
    else:
        return lang['transfer']


def create_database(cursor):
    sql = '''
    CREATE TABLE IF NOT EXISTS tx ( 
        block int UNIQUE NOT NULL,
        chain VARCHAR(255) DEFAULT 'ethereum',
        token_name VARCHAR(20) DEFAULT 'Infinity Mining Token',
        token VARCHAR(20) DEFAULT 'IMT',
        hash VARCHAR(255) DEFAULT '',
        date VARCHAR(255) DEFAULT '',
        time_stamp VARCHAR(255) DEFAULT '',
        wallet_address VARCHAR(255) DEFAULT '',
        amount VARCHAR(20) DEFAULT '',
        full_amount VARCHAR(20) DEFAULT '',
        which VARCHAR(10) DEFAULT '',
        head VARCHAR(255) DEFAULT '',
        agent VARCHAR(255) DEFAULT '',
        action VARCHAR(255) DEFAULT '',
        perform VARCHAR(255) DEFAULT '',
        data TEXT DEFAULT '',
        PRIMARY KEY (block)
    );'''

    cursor.execute(sql)


def write_tx_record(*args):
    sql = f'''INSERT OR REPLACE INTO tx (block, hash, date, time_stamp, wallet_address, amount, full_amount, which, head, agent, action, perform, data)
             VALUES(
                "{args[0]}",
                "{args[1]}",
                "{args[2]}",
                "{args[3]}",
                "{args[4]}",
                "{args[5]}",
                "{args[6]}",
                "{args[7]}",
                "{args[8]}",
                "{args[9]}",
                "{args[10]}",
                "{args[11]}",
                "{args[12]}"
                );'''
    cursor.execute(sql)
    # Commit the changes in the database
    conn.commit()


if __name__ == "__main__":
    try:
        change_working_dir()
        with open('__STARTBLOCK', 'r') as settings:
            start_block = int(settings.readline().replace('\n', ''))
            # if len(sys.argv) > 1:
            #    self.start_block += -abs(int(sys.argv[2]))
            # print(start_block)
    except Exception as e:
        start_block = 14176196

    change_working_dir()
    conn = sqlite3.connect('etherscan_tx.sqlite')
    # Connect to SQLite table
    cursor = conn.cursor()
    create_database(cursor)
    conn.commit()

    imt = IMTToken(int(start_block))

    processed = {}
    for x in reversed(imt.data):
        tx = Transaction(x, imt.lp_address)
        # @GK No need to print all - print(tx.dt, x)
        argList = [x['blockNumber'],
                   x['hash'],
                   tx.dt,
                   x['timeStamp'],
                   tx.wallet_address,
                   tx.raw_full_amount,
                   tx.full_IMT_amount,
                   tx.trigger.which,
                   tx.trigger.head,
                   tx.trigger.agent,
                   tx.trigger.action,
                   tx.trigger.perform,
                   x]
        if x['blockNumber'] in processed:
            if tx.raw_full_amount > processed[x['blockNumber']]:
                # store entry into SQL database
                write_tx_record(*argList)
        else:
            # block, date, wallet_address, amount, full_amount, head, agent, action, perform, data
            # store entry into SQL database
            write_tx_record(*argList)

    if len(imt.data) >= 1:
        last_tx = Transaction(imt.last_tx, imt.lp_address)

        if last_tx.eth_block >= start_block:
            change_working_dir()
            with open('__STARTBLOCK', 'w') as settings:
                new_start_block = last_tx.eth_block + 1
                settings.write(str(new_start_block))
                print('+', end="")

            if last_tx.trigger.which != 'transfer':
                playsound = './resource/audio/short-scale.wav' if last_tx.trigger.which == 'buy' else './resource/audio/short-riff.wav'
                notify(playsound, f"{last_tx.wallet_address[:6]}...{last_tx.wallet_address[-4:]}", last_tx.title, last_tx.message)

    else:
        print('/', end="")

    # Closing the connection
    conn.close()
