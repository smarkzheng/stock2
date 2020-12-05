import datetime
from my_stock import read_stock,proc_stock
import pandas as pd
import time
import math

class market:        
    def __init__(self,silent=False):
        self.status = 'unknown'
        self.time = datetime.datetime.today()        
        self.get_status(silent)
        
    def get_status(self,silent=True):
        if silent == False:
            print('query market status...')
        self.time = datetime.datetime.today()
        t_open = self.time.replace(hour=8,minute=30,second=0,microsecond=0)     #   the time of market open
        t_close = self.time.replace(hour=15,minute=0,second=0,microsecond=0)       #   the time of market close
        
        date_today = str(self.time.year)+'-'+str(self.time.month)+'-'+str(self.time.day)        # convert the date in the format of datetime object to a string
        df = read_stock('SPY')      #   query the SPY price from Yahoo finance in order to get the latest date registered in the price log
        df_latest_date = df.iloc[-1]['Date']
        
        if silent == False:
            print('SPY quote is ${:.2f}'.format(df.iloc[-1]['Close']),
                  'last checked at:',
                  '{}-{}-{},{}:{}'.format(self.time.year,self.time.month,self.time.day,self.time.hour,self.time.minute))
            
        yyyy,mm,dd = date_today.split('-')
        ls_date_today = [int(i) for i in [yyyy,mm,dd]]
        yyyy,mm,dd = df_latest_date.split('-')
        ls_df_latest_date = [int(i) for i in [yyyy,mm,dd]]
        
        if ls_date_today == ls_df_latest_date:            
            if self.time >= t_open and self.time <= t_close:
                self.status = 'open'
            else:
                self.status = 'closed'
        else:            
            self.status = 'closed'
            
        if silent == False:
            print('market',self.status)
        return self.status
    
class portfolio:    
    def __init__(self):
        df_stocks = pd.read_csv('portfolio.csv')
        df_stocks.set_index(['symbol'],inplace=True)
        self.details = df_stocks
        self.n_lines = len(self.details)
        self.total_value = self.details['current value'].sum()
        
    def update(self):
        self.n_lines = len(self.details)
        for i in range(1,self.n_lines):
            symbol = self.details.iloc[i].name
            df = read_stock(symbol)
            self.details.at[symbol,'current price'] = df.iloc[-1]['Close']
            self.details.at[symbol,'current value'] = df.iloc[-1]['Close'] * self.details.loc[symbol]['number of shares']
        self.total_value = self.details['current value'].sum()
        
    def buy(self,symbol):
        df = read_stock(symbol)
        purchase_price = df.iloc[-1]['Close']
        n_stock = math.floor(self.details.loc['_CASH']['current value']/purchase_price)
        stock = pd.Series({'purchased on':df.iloc[-1]['Date'],
                 'number of shares':n_stock,'averaged cost':purchase_price,
                 'total cost':n_stock * purchase_price,
                 'current price':purchase_price,'current value':n_stock * purchase_price})
        stock.rename(symbol,inplace=True)        
        print('executing following purchase:')
        print(stock)
        self.details.at['_CASH','current value'] -= n_stock * purchase_price
        self.details = self.details.append(stock)
        self.update()
        
        return stock
    
    def sell(self,symbol):
        df = read_stock(symbol)
        sell_price = df.iloc[-1]['Close']
        n_stock = self.details.loc[symbol]['number of shares']
        
        stock = pd.Series({'purchased on':self.details.loc[symbol]['purchased on'],
                 'number of shares':n_stock,'averaged cost':self.details.loc[symbol]['averaged cost'],
                 'total cost':self.details.loc[symbol]['total cost'],
                 'current price':sell_price,'current value':n_stock * sell_price,
                 '% gain': (n_stock * sell_price - self.details.loc[symbol]['total cost'])/
                 self.details.loc[symbol]['total cost']*100})
        stock.rename(symbol,inplace=True)
        print('executing following sell:')
        print(stock)
        self.details.at['_CASH','current value'] += n_stock * sell_price
        self.details.drop([symbol],inplace=True)
        self.update()
        
        
def check_buy(row):
    df = read_stock(row.name)
    df = proc_stock(df,20,row['d'],row['r'])
    if len(df) == 0:
        return False
    else:
        return df.iloc[-1]['Buy']

def check_sell(row,df_SP500):
    df = read_stock(row.name)
    d = df_SP500.loc[row.name]['d']
    r = df_SP500.loc[row.name]['r']
    df = proc_stock(df,20,d,r)
    if len(df) == 0:
        return False
    else:
        if (df.iloc[-1]['Close'] < 0.95 * row['averaged cost']) or df.iloc[-1]['Sell']:
            return True
        else:
            return False
    
while True:    
    # code below will execute everyday at 9:00 AM
    my_market = market()
    if my_market.status == 'closed':
        print('trader bot shuting down...')
    else:
        print('trader bot starting up...')
        
        my_portfolio = portfolio()     #   open the portfolio
        my_portfolio.update()
        
        while my_market.get_status()=='open' and (my_portfolio.n_lines > 1):
            time.sleep(5*60)   #   frequency of checking the sell signal is set to 2 minutes
            print('checking sell signal...')
            df_SP500 = pd.read_csv('strategy_table.csv')
            df_SP500.set_index(['Symbol'],inplace=True)
            ls_cand = my_portfolio.details.iloc[1:].apply(check_sell,args=(df_SP500,),axis=1)
            ls_cand = ls_cand[ls_cand==True]        
            if (len(ls_cand) == 0):
                print('sell signal not detected')
                my_portfolio.update()
                print('portfolio value:{:.2f}'.format(my_portfolio.total_value))
            else:
                for cand in ls_cand.index:
                    my_portfolio.sell(cand)
                    
        if my_market.get_status() == 'open':
            t_check_buy = datetime.datetime.today().replace(hour=15,minute=0,second=0,microsecond=0)
            time.sleep((t_check_buy - datetime.datetime.today()).seconds)
            print('start to check buy signal...')
            df_SP500 = pd.read_csv('strategy_table.csv')
            df_SP500.set_index(['Symbol'],inplace=True)
            check_buy_start = time.time()
            df_check_buy = df_SP500.apply(check_buy,axis=1)
            check_buy_end = time.time()
            print('checking buy signal took:',check_buy_end - check_buy_start,'seconds')
            cand_name = df_SP500[df_check_buy].sort_values(by=['Signal Avg. Gain %'],ascending=False).iloc[0].name
            cand_prospect = df_SP500.loc[cand_name]['Signal Avg. Gain %']
            print('symbol:',cand_name,'prospect: {:.2f}%'.format(cand_prospect))
            my_portfolio.buy(cand_name)
            
        try:
            my_portfolio.details.to_csv('portfolio_'+str(my_market.time.year)+'-'+
                                      str(my_market.time.month)+'-'+
                                      str(my_market.time.day)+'.csv')
        except:
            pass
    
        my_portfolio.details.to_csv('portfolio.csv')
        print('trader bot shutting down...')
        
    t_next_run = datetime.datetime.today().replace(hour=9,minute=0,second=0,microsecond=0)
    t_next_run += datetime.timedelta(days=1)
    print('next execution at:',t_next_run)
    time.sleep((t_next_run - datetime.datetime.today()).seconds)    