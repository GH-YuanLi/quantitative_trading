import datetime as dt
import os
import time

import pandas as pd
import tushare as ts
from tqdm import tqdm

# ------------------------------------------------------------
# 0. 获取数据
# ------------------------------------------------------------


# 设置Tushare的token
ts.set_token(
    "d75ae646c0ca9f00cd95dabd11d8689768976d613a19a682d535d0f7"
)  # 替换为你的Tushare token
pro = ts.pro_api()


def get_main_and_continuous_contracts(exchange, fut_code):
    """获取期货品种的主力与连续合约"""
    df = pro.fut_basic(
        exchange=exchange, fut_type="2", fut_code=fut_code, fields="ts_code,symbol,name"
    )
    return df["ts_code"].tolist()


def get_mapping_contracts(ts_code, start_date, end_date):
    """获取主力/连续合约对应的普通合约"""
    df = pro.fut_mapping(ts_code=ts_code, start_date=start_date, end_date=end_date)
    return df[["trade_date", "mapping_ts_code"]].drop_duplicates()


def fetch_day_data(contract_code, trade_date, freq):
    """抓取某一天的完整交易数据（夜盘+白盘）"""
    all_parts = []

    # 交易日 T 的夜盘：21:00~次日02:30
    night_start = dt.datetime.strptime(trade_date, "%Y%m%d").replace(
        hour=21, minute=0, second=0
    )
    night_end = night_start + dt.timedelta(hours=5, minutes=30)  # 次日 02:30

    # 交易日 T 的白盘：09:00~15:00
    day_start = dt.datetime.strptime(trade_date, "%Y%m%d").replace(
        hour=9, minute=0, second=0
    )
    day_end = day_start + dt.timedelta(hours=6)

    for session_name, start, end in [
        ("夜盘", night_start, night_end),
        ("白盘", day_start, day_end),
    ]:
        try:
            df = pro.ft_mins(
                ts_code=contract_code,
                freq=freq,
                start_date=start.strftime("%Y-%m-%d %H:%M:%S"),
                end_date=end.strftime("%Y-%m-%d %H:%M:%S"),
            )
            if not df.empty:
                df["session"] = session_name
                all_parts.append(df)
        except Exception as e:
            print(f"⚠️ 获取 {session_name} 数据失败: {e}")

    return pd.concat(all_parts, ignore_index=True) if all_parts else pd.DataFrame()


def download_futures_minute_data(exchange, fut_code, freq, start_date, end_date):
    """
    只下载某品种【主力合约】的分钟数据（夜盘+白盘）
    参数同前
    """
    # 1. 取主力合约（过滤掉连续合约）
    df_contracts = pro.fut_basic(
        exchange=exchange, fut_type="2", fut_code=fut_code, fields="ts_code,symbol,name"
    )
    # 主力合约名称示例：'沪银主力'，连续合约示例：'沪银连续'
    main_contract_list = [
        c
        for c in df_contracts["ts_code"]
        if "连续" not in df_contracts[df_contracts["ts_code"] == c]["name"].values[0]
    ]
    if not main_contract_list:
        print("未找到主力合约，退出")
        return pd.DataFrame()

    # 只取第一条（理论上只有一个）
    main_contract = main_contract_list[0]
    print(f"使用主力合约: {main_contract}")

    # 2. 获取主力每日映射的真实合约
    mapping_df = pro.fut_mapping(
        ts_code=main_contract,
        start_date=start_date.strftime("%Y%m%d"),
        end_date=end_date.strftime("%Y%m%d"),
    )
    if mapping_df.empty:
        print("未找到任何映射，退出")
        return pd.DataFrame()

    mapping_df = mapping_df.sort_values("trade_date")
    total_days = len(mapping_df)
    print(f"共需处理 {total_days} 个交易日")

    all_data = pd.DataFrame()

    # 3. 逐日抓取
    with tqdm(total=total_days, desc="下载进度") as pbar:
        for _, row in mapping_df.iterrows():
            trade_date = row["trade_date"]
            real_contract = row["mapping_ts_code"]

            # 夜盘 21:00–次日 02:30
            night_start = dt.datetime.strptime(trade_date, "%Y%m%d").replace(
                hour=21, minute=0
            )
            night_end = night_start + dt.timedelta(hours=5, minutes=30)

            # 白盘 09:00–15:00
            day_start = dt.datetime.strptime(trade_date, "%Y%m%d").replace(
                hour=9, minute=0
            )
            day_end = day_start + dt.timedelta(hours=6)

            daily_parts = []
            for session, start, end in [
                ("夜盘", night_start, night_end),
                ("白盘", day_start, day_end),
            ]:
                try:
                    part = pro.ft_mins(
                        ts_code=real_contract,
                        freq=freq,
                        start_date=start.strftime("%Y-%m-%d %H:%M:%S"),
                        end_date=end.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                    if not part.empty:
                        part["session"] = session
                        daily_parts.append(part)
                except Exception as e:
                    tqdm.write(f"{trade_date} {session} 失败: {e}")

            if daily_parts:
                daily_df = pd.concat(daily_parts, ignore_index=True)
                daily_df["trade_date"] = trade_date
                all_data = pd.concat([all_data, daily_df], ignore_index=True)

            pbar.update(1)
            pbar.set_postfix(
                {"日期": trade_date, "合约": real_contract, "累计": len(all_data)}
            )
            time.sleep(0.1)

    return all_data


def save_to_csv(data, filename):
    """保存数据到CSV文件"""
    if not data.empty:
        data.to_csv(filename, index=False, encoding="utf-8-sig")
        print(f"\n数据已保存到: {filename}")
    else:
        print("\n没有数据需要保存")


def main():
    params = {
        "exchange": "SHFE",
        "fut_code": "AG",
        "freq": "1min",                             # 数据频率
        "start_date": dt.datetime(2020, 1, 1),      # 开始日期
        "end_date": dt.datetime(2025, 8, 1),        # 结束日期
    }
    output_file = f"{params['fut_code']}_{params['freq']}_{params['start_date']:%Y%m%d}_{params['end_date']:%Y%m%d}.csv"

    print("开始下载期货分钟级数据...")
    print(f"品种: {params['fut_code']}")
    print(f"交易所: {params['exchange']}")
    print(f"频率: {params['freq']}")
    print(
        f"时间范围: {params['start_date'].strftime('%Y-%m-%d')} 到 {params['end_date'].strftime('%Y-%m-%d')}"
    )

    data = download_futures_minute_data(
        exchange=params["exchange"],
        fut_code=params["fut_code"],
        freq=params["freq"],
        start_date=params["start_date"],
        end_date=params["end_date"],
    )

    save_to_csv(data, os.path.join("./data/", output_file))
    print("\n下载完成！")


if __name__ == "__main__":
    main()
