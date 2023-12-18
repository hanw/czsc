# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2023/5/11 20:36
describe: 信号观察页面
"""
import os
os.environ['czsc_max_bi_num'] = '20'
os.environ['czsc_research_cache'] = r"/Users/hanwang/p/CZSC_Data"
import czsc
import numpy as np
import pandas as pd
import streamlit as st
from datetime import timedelta
from czsc.utils import sorted_freqs
from czsc.connectors.research import get_raw_bars, get_symbols

import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts

import json
import numpy as np
import yfinance as yf
import pandas as pd
import pandas_ta as ta

COLOR_BULL = 'rgba(38,166,154,0.9)' # #26a69a
COLOR_BEAR = 'rgba(239,83,80,0.9)'  # #ef5350

# Request historic pricing data via finance.yahoo.com API
df = yf.Ticker('AAPL').history(period='4mo')[['Open', 'High', 'Low', 'Close', 'Volume']]

# Some data wrangling to match required format
df = df.reset_index()
df.columns = ['time','open','high','low','close','volume']                  # rename columns
df['time'] = df['time'].dt.strftime('%Y-%m-%d')                             # Date to string
df['color'] = np.where(  df['open'] > df['close'], COLOR_BEAR, COLOR_BULL)  # bull or bear
df.ta.macd(close='close', fast=6, slow=12, signal=5, append=True)           # calculate macd

# export to JSON format
candles = json.loads(df.to_json(orient = "records"))
volume = json.loads(df.rename(columns={"volume": "value",}).to_json(orient = "records"))
macd_fast = json.loads(df.rename(columns={"MACDh_6_12_5": "value"}).to_json(orient = "records"))
macd_slow = json.loads(df.rename(columns={"MACDs_6_12_5": "value"}).to_json(orient = "records"))
df['color'] = np.where(  df['MACD_6_12_5'] > 0, COLOR_BULL, COLOR_BEAR)  # MACD histogram color
macd_hist = json.loads(df.rename(columns={"MACD_6_12_5": "value"}).to_json(orient = "records"))

st.set_page_config(layout="wide")

chartMultipaneOptions = [
    {
        "height": 600,
        "layout": {
            "background": {
                "type": "solid",
                "color": 'white'
            },
            "textColor": "black"
        },
        "grid": {
            "vertLines": {
                "color": "rgba(197, 203, 206, 0.5)"
                },
            "horzLines": {
                "color": "rgba(197, 203, 206, 0.5)"
            }
        },
        "crosshair": {
            "mode": 0
        },
        "priceScale": {
            "borderColor": "rgba(197, 203, 206, 0.8)"
        },
        "timeScale": {
            "borderColor": "rgba(197, 203, 206, 0.8)",
            "barSpacing": 15
        },
        "watermark": {
            "visible": True,
            "fontSize": 48,
            "horzAlign": 'center',
            "vertAlign": 'center',
            "color": 'rgba(171, 71, 188, 0.3)',
            "text": 'AAPL - D1',
        }
    },
    {
        "height": 100,
        "layout": {
            "background": {
                "type": 'solid',
                "color": 'transparent'
            },
            "textColor": 'black',
        },
        "grid": {
            "vertLines": {
                "color": 'rgba(42, 46, 57, 0)',
            },
            "horzLines": {
                "color": 'rgba(42, 46, 57, 0.6)',
            }
        },
        "timeScale": {
            "visible": False,
        },
        "watermark": {
            "visible": True,
            "fontSize": 18,
            "horzAlign": 'left',
            "vertAlign": 'top',
            "color": 'rgba(171, 71, 188, 0.7)',
            "text": 'Volume',
        }
    },
    {
        "height": 100,
        "layout": {
            "background": {
                "type": "solid",
                "color": 'white'
            },
            "textColor": "black"
        },
        "timeScale": {
            "visible": False,
        },
        "watermark": {
            "visible": True,
            "fontSize": 18,
            "horzAlign": 'left',
            "vertAlign": 'center',
            "color": 'rgba(171, 71, 188, 0.7)',
            "text": 'MACD',
        }
    }
]

seriesCandlestickChart = [
    {
        "type": 'Candlestick',
        "data": candles,
        "options": {
            "upColor": COLOR_BULL,
            "downColor": COLOR_BEAR,
            "borderVisible": False,
            "wickUpColor": COLOR_BULL,
            "wickDownColor": COLOR_BEAR
        }
    }
]

seriesVolumeChart = [
    {
        "type": 'Histogram',
        "data": volume,
        "options": {
            "priceFormat": {
                "type": 'volume',
            },
            "priceScaleId": "" # set as an overlay setting,
        },
        "priceScale": {
            "scaleMargins": {
                "top": 0,
                "bottom": 0,
            },
            "alignLabels": False
        }
    }
]

seriesMACDchart = [
    {
        "type": 'Line',
        "data": macd_fast,
        "options": {
            "color": 'blue',
            "lineWidth": 2
        }
    },
    {
        "type": 'Line',
        "data": macd_slow,
        "options": {
            "color": 'green',
            "lineWidth": 2
        }
    },
    {
        "type": 'Histogram',
        "data": macd_hist,
        "options": {
            "color": 'red',
            "lineWidth": 1
        }
    }
]

st.subheader("信号观察")

signals_module = st.sidebar.text_input("信号模块名称：", value="czsc.signals")
parser = czsc.SignalsParser(signals_module=signals_module)

with st.sidebar:
    st.header("信号配置")
    with st.form("my_form"):
        conf = st.text_input("请输入信号：", value="60分钟_D0停顿分型_BE辅助V230106_看多_强_任意_0")
        symbol = st.selectbox("请选择股票：", get_symbols('ALL'), index=0)
        freqs = st.multiselect("请选择周期：", sorted_freqs, default=['30分钟', '日线', '周线'])
        freqs = czsc.freqs_sorted(freqs)
        sdt = st.date_input("开始日期：", value=pd.to_datetime('2022-01-01'))
        edt = st.date_input("结束日期：", value=pd.to_datetime('2023-01-01'))
        submit_button = st.form_submit_button(label='提交')


# 获取K线，计算信号
bars = get_raw_bars(symbol, freqs[0], pd.to_datetime(sdt) - timedelta(days=365*3), edt)
signals_config = czsc.get_signals_config([conf], signals_module=signals_module)
sigs = czsc.generate_czsc_signals(bars, signals_config, df=True, sdt=sdt)
sigs.drop(columns=['freq', 'cache'], inplace=True)
cols = [x for x in sigs.columns if len(x.split('_')) == 3]
assert len(cols) == 1
sigs['match'] = sigs.apply(czsc.Signal(conf).is_match, axis=1)
sigs['text'] = np.where(sigs['match'], sigs[cols[0]], "")

# 在图中绘制指定需要观察的信号
# chart = czsc.KlineChart(n_rows=3, height=800)
# chart.add_kline(sigs, freqs[0])
# # 可以参考这里的代码，绘制其他自定义指标
# chart.add_sma(sigs, row=1, ma_seq=(5, 10, 20), visible=True)
# chart.add_vol(sigs, row=2)
# chart.add_macd(sigs, row=3)
# df1 = sigs[sigs['text'] != ""][['dt', 'text', 'close', 'low']].copy()
# chart.add_scatter_indicator(x=df1['dt'], y=df1['low'], row=1, name='信号', mode='markers',
#                             marker_size=20, marker_color='red', marker_symbol='triangle-up')
# st.plotly_chart(chart.fig, use_container_width=True, config={
#     "scrollZoom": True,
#     "displayModeBar": True,
#     "displaylogo": False,
#     'modeBarButtonsToRemove': [
#         'toggleSpikelines',
#         'select2d',
#         'zoomIn2d',
#         'zoomOut2d',
#         'lasso2d',
#         'autoScale2d',
#         'hoverClosestCartesian',
#         'hoverCompareCartesian']})


renderLightweightCharts([
    {
        "chart": chartMultipaneOptions[0],
        "series": seriesCandlestickChart
    },
    {
        "chart": chartMultipaneOptions[1],
        "series": seriesVolumeChart
    },
    {
        "chart": chartMultipaneOptions[2],
        "series": seriesMACDchart
    }
], 'multipane')