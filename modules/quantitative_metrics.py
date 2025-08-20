import pandas as pd

from modules import data_preprocessing

# ------------------------------------------------------------
# 2. 指标策略
# ------------------------------------------------------------


# 布林线：过去20个收盘价
def calculate_bollinger_bands(df, N=20, k=2):
    """
    计算布林线指标

    参数:
    df: 包含K线数据的DataFrame，必须包含列['trade_time', 'open', 'close', 'high', 'low', 'volume', 'amount']
    N: 移动平均周期（默认20）
    k: 标准差倍数（默认2）

    返回:
    包含布林线数据的DataFrame（新增MB, UB, LB列）
    """
    # 确保数据按时间排序
    # df = df.sort_values("trade_time").reset_index(drop=True)

    # 计算中轨线（N日收盘价的简单移动平均）
    df["boll_MB"] = df["close"].rolling(window=N).mean()

    # 计算N日收盘价的标准差
    df["boll_std"] = df["close"].rolling(window=N).std()

    # 计算上轨和下轨
    df["boll_UB"] = df["boll_MB"] + k * df["boll_std"]
    df["boll_LB"] = df["boll_MB"] - k * df["boll_std"]

    return df.drop("boll_std", axis=1)


# Donchian channel：过去20个最高和最低价
def calculate_donchian_channel(df, period=20):
    """
    计算 Donchian Channel

    参数
    ----
    df : pd.DataFrame
        必须包含列 ['trade_time', 'high', 'low']，且已按时间升序排列
    period : int
        回看周期，默认 20

    返回
    ----
    pd.DataFrame
        原表附加 ['DC_Upper', 'DC_Lower', 'DC_Middle']
    """
    # df = df.copy()
    df["DC_Upper"] = df["high"].rolling(window=period).max()
    df["DC_Lower"] = df["low"].rolling(window=period).min()
    df["DC_Middle"] = (df["DC_Upper"] + df["DC_Lower"]) / 2
    return df


# ADX index
def calculate_adx(df, period=10):
    """
    计算 ADX、+DI、-DI

    参数
    ----
    df : pd.DataFrame
        必须包含列 ['trade_time', 'high', 'low', 'close']，且已按时间升序排列
    period : int
        ADX 周期，默认 14

    返回
    ----
    pd.DataFrame
        原表附加 ['TR', '+DM', '-DM', '+DI', '-DI', 'DX', 'ADX']
    """
    df = df.copy()

    # 1. True Range
    df["prev_close"] = df["close"].shift(1)
    df["HL"] = df["high"] - df["low"]
    df["HC"] = (df["high"] - df["prev_close"]).abs()
    df["LC"] = (df["low"] - df["prev_close"]).abs()
    df["TR"] = df[["HL", "HC", "LC"]].max(axis=1)

    # 2. +/-DM
    df["up_move"] = df["high"] - df["high"].shift(1)
    df["down_move"] = df["low"].shift(1) - df["low"]

    df["+DM"] = 0.0
    df.loc[df["up_move"] > df["down_move"], "+DM"] = df["up_move"].clip(lower=0)

    df["-DM"] = 0.0
    df.loc[df["down_move"] > df["up_move"], "-DM"] = df["down_move"].clip(lower=0)

    # 3. Wilder 平滑
    alpha = 1.0 / period

    df["TR_smooth"] = df["TR"].ewm(alpha=alpha, adjust=False).mean()
    df["+DM_smooth"] = df["+DM"].ewm(alpha=alpha, adjust=False).mean()
    df["-DM_smooth"] = df["-DM"].ewm(alpha=alpha, adjust=False).mean()

    # 4. +/-DI
    df["+DI"] = 100 * df["+DM_smooth"] / df["TR_smooth"]
    df["-DI"] = 100 * df["-DM_smooth"] / df["TR_smooth"]

    # 5. DX
    df["DX"] = 100 * (df["+DI"] - df["-DI"]).abs() / (df["+DI"] + df["-DI"])

    # 6. ADX
    df["ADX"] = df["DX"].ewm(alpha=alpha, adjust=False).mean()

    # 清理中间列
    drop_cols = [
        "prev_close",
        "HL",
        "HC",
        "LC",
        "up_move",
        "down_move",
        "TR",
        "+DM",
        "-DM",
        "TR_smooth",
        "+DM_smooth",
        "-DM_smooth",
        "DX",
        "+DI",
        "-DI"
    ]
    df.drop(columns=drop_cols, inplace=True)

    return df


# ATR index
def calculate_atr(df, period=10):
    """
    计算 ATR

    参数
    ----
    df : pd.DataFrame
        必须包含列 ['trade_time', 'high', 'low', 'close']，且已按时间升序排列
    period : int
        ATR 周期，默认 14

    返回
    ----
    pd.DataFrame
        原表附加 ['TR', 'ATR']
    """
    df = df.copy()

    # 1. True Range
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    df["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # 2. Wilder 平滑
    df["ATR"] = df["TR"].ewm(alpha=1 / period, adjust=False).mean()

    return df.drop("TR", axis=1)



# 计算指标：布林线、唐奇安通道、ADX、ATR，并创建宽表
class cal_metrics:
    def __init__(self, df, boll_period=20, dc_period=20, adx_period=10, atr_period=10):
        self.df = df
        self.boll_period = boll_period
        self.dc_period = dc_period
        self.adx_period = adx_period
        self.atr_period = atr_period

    def add_metrics(self):
        df = calculate_bollinger_bands(self.df, self.boll_period)
        df = calculate_donchian_channel(df, self.dc_period)
        df = calculate_adx(df, self.adx_period)
        df = calculate_atr(df, self.atr_period)
        df['flag_increase'] = df['close'] >= df['open']

        df['date'] = pd.to_datetime(df['trade_time'])

        return df


if __name__ == "__main__":
    data_prep = data_preprocessing.Data_preprocessing()
    df = data_prep.load_data()
    dt_all, dt_obs, dt_breaks = data_prep.time_filter(df)

    df = data_prep.fill_missing_data(df, dt_all)

    df = cal_metrics(df).add_metrics()

    print(df.head())


# # ------------------------------------------------------------
# # 2. Backtrader 策略：把指标保存为实例属性
# # ------------------------------------------------------------

# class IndicatorOnly(bt.Strategy):
#     def __init__(self):
#         self.boll      = bt.ind.BollingerBands(self.data.close, period=20, devfactor=2)
#         self.adx       = bt.ind.ADX(self.data, period=10)
#         # self.adx       = bt.talib.ADX(self.data.high, self.data.low, self.data.close, timeperiod=10)
#         self.atr       = bt.ind.ATR(self.data, period=10)
#         self.don_high  = bt.ind.Highest(self.data.high, period=20)
#         self.don_low   = bt.ind.Lowest(self.data.low,  period=20)

# # ------------------------------------------------------------
# # 3. 把 pandas DataFrame 喂给 Backtrader
# # ------------------------------------------------------------
# class PandasData(bt.feeds.PandasData):
#     lines = ('amount',)
#     params = (
#         ('datetime', None),
#         ('open', 'open'),
#         ('high', 'high'),
#         ('low', 'low'),
#         ('close', 'close'),
#         ('volume', 'volume'),
#         ('amount', 'amount'),
#     )

# cerebro = bt.Cerebro()
# data_feed = PandasData(dataname=df)
# cerebro.adddata(data_feed)
# cerebro.addstrategy(IndicatorOnly)
# results = cerebro.run()        # ← 返回列表
# strat   = results[0]           # ← 取第一个（也是唯一一个）策略实例

# # ------------------------------------------------------------
# # 4. 统一把指标数组取出来
# # ------------------------------------------------------------
# size = len(df)
# boll_up  = np.array(strat.boll.top.get(size=size))
# boll_mid = np.array(strat.boll.mid.get(size=size))
# boll_bot = np.array(strat.boll.bot.get(size=size))
# # adx_arr  = np.array(strat.adx.get(size=size))
# # atr_arr  = np.array(strat.atr.get(size=size))
# don_hi   = np.array(strat.don_high.get(size=size))
# don_lo   = np.array(strat.don_low.get(size=size))
# don_mid   = (don_hi + don_lo) / 2
