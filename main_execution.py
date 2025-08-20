"""
量化交易策略：
0. 获取数据
1. 准备数据集：加载数据 & 观测时间过滤
2. 指标策略
3. 数据可视化
4. 创建策略
5. 创建回测
"""

import datetime
import logging
import sys
import warnings

import pandas as pd

from modules import data_preprocessing, data_visualization, quantitative_metrics

# import os
from utils import utils

pd.options.mode.chained_assignment = None
dt = datetime.datetime.now().strftime('%Y%m%d')

timestamp = utils.get_timestamp('%Y%m%d%H%M%S')

warnings.filterwarnings('ignore')
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S',
	filename=f'./logs/log_detail_{timestamp}.log',
)


logging.info('MISSION START... ...')


# 下载最新交易数据
while True:
	flag_download = input('\n - 是否从Tushare下载最新交易数据（Y/N）：').strip().replace("'", '')
	try:
		assert flag_download.upper() in ['Y', 'N'], 'Invalid input'
		print('模块开发中，敬请期待')
		if flag_download.upper() == 'Y':
			# data_fetch.main()
			pass
		else:
			pass
		break
	except Exception as e:
		print(e, end='. ')
		print('Please try again.')


# 选择观测时间
while True:
	start_time = input(' - 请选择想要观测的起始时间（YYYYMMDD）：').strip().replace("'", '')
	try:
		start_time = datetime.datetime.strptime(str(start_time), '%Y%m%d')
		# start_year = start_time.year
		# start_month = start_time.month
		# start_day = start_time.day
		break
	except Exception as e:
		print(e, end='. ')
		print('Invalid date format, please input again')
while True:
	end_time = input(' - 请选择想要观测的终止时间（YYYYMMDD）：').strip().replace("'", '')
	try:
		end_time = datetime.datetime.strptime(str(end_time), '%Y%m%d')
		assert start_time <= end_time, 'Invalid date range'
		# if start_time > end_time:
		#     print("Invalid date range, please input again")
		#     continue
		# else:
		# end_year = end_time.year
		# end_month = end_time.month
		# end_day = end_time.day
		break
	except Exception as e:
		print(e, end='. ')
		print('Please input again')
logging.info(f' - 观测时间范围：{start_time} ~ {end_time + datetime.timedelta(days=1)}')
print(f' ✓ 已选择的观测时间范围：{start_time} ~ {end_time + datetime.timedelta(days=1)}')

logging.info(' - 观测指标：布林线、唐奇安通道、ADX、ATR')


# print(date_format)

# 数据预处理
print('\n数据预处理中...\n')
data_prep = data_preprocessing.Data_preprocessing(start_time, end_time)
df = data_prep.load_data()

try:
	dt_all, dt_obs, dt_breaks = data_prep.time_filter(df)
except Exception:
	print('⚠ Warning: no trading exists for the date you selected!')
	sys.exit(1)

# 数据补全
df = data_prep.fill_missing_data(df, dt_all)

# 指标计算
df = quantitative_metrics.cal_metrics(df).add_metrics()
# print(df.info())


# 选择可视化的横坐标时间格式
while True:
	date_format = input(' - 请选择可视化的时间格式（日期、字符串）：').strip().replace("'", '')
	try:
		assert date_format in ['日期', '字符串'], 'Invalid format name'
		if date_format == '日期':
			type = 'date'
		elif date_format == '字符串':
			type = 'category'
		break
	except Exception as e:
		print(e, end='. ')
		print('Please input again')

# 可视化
print('\n数据可视化中...\n')
data_visualization.html_subplot(df, dt_obs, dt_breaks, start_time, end_time, type)
logging.info(' - 完成数据可视化')


# 选择是否展示自适应K线图
while True:
	flag = input(' - 是否展示自适应K线图 (Y/N)：').strip().replace("'", '')
	try:
		assert flag.upper() in ['Y', 'N'], 'Invalid input'
		if flag.upper() == 'Y':
			data_visualization.dash_auto_resize(df, dt_obs, dt_breaks, start_time, end_time)

			# # 设置HTTP服务器
			# handler = http.server.SimpleHTTPRequestHandler
			# port = 8050
			# with socketserver.TCPServer(("", port), handler) as httpd:
			#     # 自动打开浏览器
			#     try:
			#         webbrowser.open(f"http://localhost:{8050}")
			#         print("✓ 已自动打开浏览器")
			#     except Exception as e:
			#         print(f"⚠ 无法自动打开浏览器: {e}")
			#         print(f"请手动访问: http://localhost:{8050}")
			#     # 启动服务器
			#     httpd.serve_forever()

		elif flag.upper() == 'N':
			break

	except Exception as e:
		print(e, end='. ')
		print('Please try again')

logging.info(' - 完成自适应可视化K线图展示')
# dash_auto_resize(df, dt_obs, dt_breaks, obs_year, obs_month)

print('\n ✓ 运行结束\n')
