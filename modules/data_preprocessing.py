import datetime
import os
from datetime import time

import pandas as pd

# pd.set_option('display.max_columns', None)

# ------------------------------------------------------------
# 1. 准备数据集：加载数据 & 观测时间过滤
# ------------------------------------------------------------


class Data_preprocessing:
    def __init__(self, start_date, end_date):
        # self.data_path = os.path.join("./data/", "AG_1min_20100101_20250801.csv")
        self.data_path = os.path.join("./data/", "AG_1min_20100101_20250801.parquet")
        self.start_date = start_date
        self.end_date = end_date

    def load_data(self):
        # dataframe to parquet datafile
        # df = pd.read_csv(
        #     self.data_path,
        #     parse_dates=["trade_time"],
        #     # low_memory=False
        # )
        # df['open'] = df['open'].astype(float)
        # df['close'] = df['close'].astype(float)
        # df['amount'] = df['amount'].astype(float)
        # df.to_parquet(os.path.join("./data/", "AG_1min_20100101_20250801.parquet"))

        df = pd.read_parquet(self.data_path, engine="pyarrow")

        # 提取需要观测的数据范围
        df = (
            df[
                # (df["trade_time"].dt.year == 2024)
                # & (df["trade_time"].dt.month == 1)
                # & ((df["trade_time"].dt.day >= 2) & (df["trade_time"].dt.day <= 6))
                (df["trade_time"] >= self.start_date)
                & (df["trade_time"] <= self.end_date + datetime.timedelta(days=1))
            ]
            .sort_values("trade_time")
            .copy()
        )
        # print(df.trade_time.min(), df.trade_time.max())
        return df

    def time_filter(self, df):
        # 筛选时间，保留交易日 21:00 ~ 次日 01:00的数据
        def night_filter(group):
            date = group.name
            start = pd.Timestamp.combine(date, time(1, 1))
            end = pd.Timestamp.combine(date, time(20, 59))
            return group[
                ~((group["trade_time"] >= start) & (group["trade_time"] <= end))
            ]
        try:
            df_night_shift = df.groupby(df["trade_time"].dt.date, group_keys=False).apply(
                night_filter
            )

            # 创建完整时间序列
            self.dt_all = pd.date_range(
                start=df["trade_time"].iloc[0], end=df["trade_time"].iloc[-1], freq="1min"
            )
            #  获取所有观测时间
            self.dt_obs = [
                d.strftime("%Y-%m-%d %H:%M:%S")
                for d in pd.to_datetime(df_night_shift["trade_time"])
            ]
            # 获取所有缺失时间
            self.dt_breaks = [
                d
                for d in self.dt_all.strftime("%Y-%m-%d %H:%M:%S").tolist()
                if d not in self.dt_obs
            ]

            return self.dt_all, self.dt_obs, self.dt_breaks
        except Exception as e:
            print(e)

    def fill_missing_data(self, df, dt_all):
        # 数据补全
        df = df.set_index("trade_time").reindex(dt_all).reset_index()
        df.rename(columns={"index": "datetime"}, inplace=True)
        df["trade_time"] = df["datetime"].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S")
        )  # 创建交易时间字段，将时间格式转换为字符串

        # 重命名列明，以符合 backtrader 的约定
        df.rename(
            columns={
                "datetime": "datetime",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
                "amount": "amount",
            },
            inplace=True,
        )
        # 删除无用的列
        df.drop(["ts_code", "trade_date", "session"], axis=1, inplace=True)

        df.set_index("datetime", inplace=True)
        df.sort_index(inplace=True)

        return df


if __name__ == "__main__":
    data_prep = Data_preprocessing()
    df = data_prep.load_data()
    dt_all, dt_obs, dt_breaks = data_prep.time_filter(df)

    df_new = data_prep.fill_missing_data(df, dt_all)

    print(df_new.head())
