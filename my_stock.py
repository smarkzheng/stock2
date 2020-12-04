import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt

def read_stock(symbol):
    today = datetime.date.today()
    p1 = today-datetime.timedelta(days=300)-datetime.date(1969, 12, 31)
    p2 = today-datetime.date(1969, 12, 31)
    p1 = str(int(p1.total_seconds()))
    p2 = str(int(p2.total_seconds()))
    url = 'https://query1.finance.yahoo.com/v7/finance/download/{}?P={}?period1={}&period2={}&interval=1d&events=history&includeAdjustedClose=true'
    url = url.format(symbol, symbol,p1,p2)
    try:
        df = pd.read_csv(url)
    except:
        print(symbol,' not found')
        df = []
    return df

def proc_stock(df,win_MA,win_dip,win_ral):
    if len(df) != 0:
        df.drop(['Open','High','Low','Adj Close','Volume'],axis=1,inplace=True)
        df['MA']=df['Close'].rolling(win_MA).mean()
        df['Dip']=df['Close'].rolling(win_dip).min()
        df['Rally']=df['Close'].rolling(win_ral).max()
        df['Buy'] = df.apply(buy_sig,axis=1)
        df['Sell'] = df.apply(sell_sig,axis=1)
    return df

def buy_sig(day):
    if day['Close'] > day['MA']:        
        if day['Close'] == day['Dip']:
            return True
        else:
            return False
    else:
        return False    
def sell_sig(day):
    if day['Close'] == day['Rally']:
        return True
    else:
        return False
    
def paper_trade(df,cash,sg,show_steps,show_plot):
    
    try:
        n_stock = 0
        pos = 0
        net_val = []
        benchmark_index = df[df['Buy']==True].iloc[0].name

        for i in range(0,len(df)):
            if (df.iloc[i]['Buy']==True) and cash > 0:
                n_stock = cash / df.iloc[i]['Close']
                pos = df.iloc[i]['Close']
                cash = 0
                if show_steps:
                    print('executed buy at','{:.2f}'.format(df.iloc[i]['Close']),'on',df.iloc[i]['Date'])
            if ((df.iloc[i]['Sell']==True) and n_stock > 0) or (df.iloc[i]['Close']<=(1-sg/100)*pos):
                cash = n_stock * df.iloc[i]['Close']
                n_stock = 0
                pos = 0
                if show_steps:
                    print('executed sell at','{:.2f}'.format(df.iloc[i]['Close']),'on',df.iloc[i]['Date'])
            net_val.append(cash + n_stock * df.iloc[i]['Close'])

        df['Net Value']=net_val

        # df['Benchmark Gain %'] = (df['Close'] - df.iloc[benchmark_index]['Close']) / df.iloc[benchmark_index]['Close']*100
        df['Benchmark Gain %'] = (df['Close'] - df.iloc[0]['Close']) / df.iloc[benchmark_index]['Close']*100
        df['Strategy Gain %'] = (df['Net Value'] - df.iloc[benchmark_index]['Net Value']) / df.iloc[benchmark_index]['Net Value'] * 100

        benchmark_gain = int(df.iloc[-1]['Benchmark Gain %'])
        strategy_gain = int(df.iloc[-1]['Strategy Gain %'])

        if show_plot:            
            plt.plot(df.iloc[benchmark_index:]['Benchmark Gain %'],label='benchmark, '+str(benchmark_gain)+'%')
            plt.plot(df.iloc[benchmark_index:]['Strategy Gain %'],label='strategy, '+str(strategy_gain)+'%')
            plt.legend()
            plt.xlabel('trading day')
            plt.ylabel('% gain')        
            plt.show()
        return [benchmark_gain,strategy_gain]
    except:
        return [np.nan,np.nan]

def paper_trade_subplot(df,cash,sg,plot_ax):
    
    try:
        n_stock = 0
        pos = 0
        net_val = []
        benchmark_index = df[df['Buy']==True].iloc[0].name

        for i in range(0,len(df)):
            if (df.iloc[i]['Buy']==True) and cash > 0:
                n_stock = cash / df.iloc[i]['Close']
                pos = df.iloc[i]['Close']
                cash = 0                                
            if ((df.iloc[i]['Sell']==True) and n_stock > 0)  or (df.iloc[i]['Close']<=(1-sg/100)*pos):
                cash = n_stock * df.iloc[i]['Close']
                n_stock = 0  
                pos = 0                              
            net_val.append(cash + n_stock * df.iloc[i]['Close'])

        df['Net Value']=net_val

        # df['Benchmark Gain %'] = (df['Close'] - df.iloc[benchmark_index]['Close']) / df.iloc[benchmark_index]['Close']*100
        df['Benchmark Gain %'] = (df['Close'] - df.iloc[0]['Close']) / df.iloc[benchmark_index]['Close']*100
        df['Strategy Gain %'] = (df['Net Value'] - df.iloc[benchmark_index]['Net Value']) / df.iloc[benchmark_index]['Net Value'] * 100

        benchmark_gain = int(df.iloc[-1]['Benchmark Gain %'])
        strategy_gain = int(df.iloc[-1]['Strategy Gain %'])

        plot_ax.plot(df.iloc[benchmark_index:]['Benchmark Gain %'],label='benchmark, '+str(benchmark_gain)+'%')
        plot_ax.plot(df.iloc[benchmark_index:]['Strategy Gain %'],label='strategy, '+str(strategy_gain)+'%')
        plot_ax.legend()
        plot_ax.set_xlabel('trading day')
        plot_ax.set_ylabel('% gain')        

        return [benchmark_gain,strategy_gain]
    except:
        return [np.nan,np.nan]
    
def paper_trade_buy_stat(df,cash,sg,show_steps,show_plot):        
    import numpy as np
    try:
        n_stock = 0
        pos = 0
        net_val = []
        benchmark_index = df[df['Buy']==True].iloc[0].name
        ls_gain = []

        for i in range(0,len(df)):
            if (df.iloc[i]['Buy']==True) and cash > 0:
                n_stock = cash / df.iloc[i]['Close']
                pos = df.iloc[i]['Close']
                cash = 0
                if show_steps:
                    print('executed buy at','{:.2f}'.format(df.iloc[i]['Close']),'on',df.iloc[i]['Date'])
            if ((df.iloc[i]['Sell']==True) and n_stock > 0) or (df.iloc[i]['Close']<=(1-sg/100)*pos):
                ls_gain.append((df.iloc[i]['Close']-pos)/pos*100)
                cash = n_stock * df.iloc[i]['Close']
                n_stock = 0
                pos = 0                
                if show_steps:
                    print('executed sell at','{:.2f}'.format(df.iloc[i]['Close']),'on',df.iloc[i]['Date'])
            net_val.append(cash + n_stock * df.iloc[i]['Close'])

        df['Net Value']=net_val

        # df['Benchmark Gain %'] = (df['Close'] - df.iloc[benchmark_index]['Close']) / df.iloc[benchmark_index]['Close']*100
        df['Benchmark Gain %'] = (df['Close'] - df.iloc[0]['Close']) / df.iloc[benchmark_index]['Close']*100
        df['Strategy Gain %'] = (df['Net Value'] - df.iloc[benchmark_index]['Net Value']) / df.iloc[benchmark_index]['Net Value'] * 100

        benchmark_gain = int(df.iloc[-1]['Benchmark Gain %'])
        strategy_gain = int(df.iloc[-1]['Strategy Gain %'])

        if show_plot:            
            plt.plot(df.iloc[benchmark_index:]['Benchmark Gain %'],label='benchmark, '+str(benchmark_gain)+'%')
            plt.plot(df.iloc[benchmark_index:]['Strategy Gain %'],label='strategy, '+str(strategy_gain)+'%')
            plt.legend()
            plt.xlabel('trading day')
            plt.ylabel('% gain')        
            plt.show()
        if len(np.array(ls_gain))!=0:
            return [np.array(ls_gain).mean(),buy_sig(df.iloc[-1])]
        else:
            return [np.nan,False]        
        
    except:
        return [np.nan,False]        