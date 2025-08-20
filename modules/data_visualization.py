import http.server
import os
import socketserver
import webbrowser

import pandas as pd
import plotly.graph_objects as go

# import dash_core_components as dcc
# import dash_html_components as html
from dash import dcc, html
from dash.dependencies import Input, Output
from jupyter_dash import JupyterDash
from plotly.subplots import make_subplots

from modules import data_preprocessing, quantitative_metrics

# ------------------------------------------------------------
# 3. 数据可视化
# ------------------------------------------------------------


def html_subplot(
	df: pd.DataFrame,
	dt_obs: list,
	dt_breaks: list,
	start_time,
	end_time,
	type: str = 'date',
	folder_path: str = './graphs/',
):
	df = df.reindex(dt_obs)

	fig = make_subplots(
		rows=4,
		cols=1,  # 5*2的图形
		shared_xaxes=True,
		specs=[
			[{'secondary_y': True}],
			[{}],
			[{'rowspan': 2}],
			[None],
		],  # 5*1；5*2)
	)

	# 5.1 K 线
	fig.add_trace(
		go.Candlestick(
			x=df.trade_time,
			open=df['open'],
			high=df['high'],
			low=df['low'],
			close=df['close'],
			name='K线',
			increasing=dict(line=dict(color='red')),
			decreasing=dict(line=dict(color='green')),
		),
		row=3,
		col=1,
	)

	# 5.2 布林带
	fig.add_trace(
		go.Scatter(
			x=df.trade_time,
			# y=df["boll_up"],
			y=df['boll_UB'],
			line=dict(color='rgba(0,100,80,0.5)'),
			name='Boll Upper',
		),
		row=3,
		col=1,
	)
	fig.add_trace(
		go.Scatter(
			x=df.trade_time,
			# y=df["boll_bot"],
			y=df['boll_LB'],
			line=dict(color='rgba(0,100,80,0.5)'),
			#  fill='tonexty',
			name='Boll Lower',
		),
		row=3,
		col=1,
	)
	fig.add_trace(
		go.Scatter(
			x=df.trade_time,
			# y=df["boll_mid"],
			y=df['boll_MB'],
			line=dict(color='blue', width=1),
			name='Boll Mid',
		),
		row=3,
		col=1,
	)

	# 5.3 Donchian channel
	fig.add_trace(
		go.Scatter(
			x=df.trade_time,
			# y=df["don_hi"],
			y=df['DC_Upper'],
			line=dict(color='gray', dash='dot'),
			name='Don High',
		),
		row=3,
		col=1,
	)
	fig.add_trace(
		go.Scatter(
			x=df.trade_time,
			# y=df["don_lo"],
			y=df['DC_Lower'],
			line=dict(color='gray', dash='dot'),
			name='Don Low',
		),
		row=3,
		col=1,
	)
	fig.add_trace(
		go.Scatter(
			x=df.trade_time,
			# y=df["don_mid"],
			y=df['DC_Middle'],
			line=dict(color='gray', dash='dot'),
			name='Don Mid',
		),
		row=3,
		col=1,
	)

	# 5.4 ADX
	fig.add_trace(
		go.Scatter(
			x=df.trade_time,
			y=df['ADX'],
			line=dict(color='orange'),
			name='ADX(10)',
			# yaxis="y",
		),
		secondary_y=False,
		row=1,
		col=1,
	)

	# 5.5 ATR
	fig.add_trace(
		go.Scatter(
			x=df.trade_time,
			y=df['ATR'],
			line=dict(color='purple'),
			name='ATR(10)',
			# yaxis="y2",
		),
		secondary_y=True,
		row=1,
		col=1,
	)

	# 5.6 volume
	colors = {True: 'red', False: 'green'}

	# for t in df['flag_increase'].unique():
	#     dfp = df[df['flag_increase']==t]
	#     fig.add_trace(go.Bar(x=dfp.index, y = dfp['volume'],
	#                          marker=dict(color=colors[t], opacity = 0.6)),
	#                          row=2, col=1)
	fig.add_trace(
		go.Bar(
			x=df.trade_time,
			y=df['volume'],
			name='Volume',
			opacity=0.9,
			marker=dict(
				color=df['flag_increase'].map(colors),
				line=dict(color=df['flag_increase'].map(colors), width=0.1),
			),
			showlegend=False,
		),
		row=2,
		col=1,
	)

	# update layour
	fig.update_layout(
		title=f'AG {start_time.strftime("%Y%m%d")} ~ {end_time.strftime("%Y%m%d")} 夜盘 21:00-01:00 交互式回放.html',
		# xaxis=dict(
		# rangeslider=dict(visible=True),  # Optional: adds zoom slider if needed?
		#     # rangebreaks=[        # 定义需要跳过的范围 (Define ranges to skip)
		#     #     # 跳过没有数据的区域 (Skip areas without data)
		#     #     # dict(bounds=["sun", "mon"]),
		#     #     # dict(bounds=[1, 21], pattern="hour"),
		#     #     # dict(values=find_empty_time_periods(df))
		#     #     dict(values=dt_breaks)
		#     # ],
		#     # type='date',
		# type="category"
		#     ),
		# yaxis=dict(
		#     title='价格',
		#     # range=[min(boll_bot) * 0.6, max(boll_up) * 1.3],
		#     # fixedrange=True,  # Prevents vertical zooming/scrolling
		#     # autorange=True
		#     ),
		# yaxis2=dict(title='ADX', overlaying='y', side='right', range=[-min(clean_y2axis_value), max(clean_y2axis_value) * 5],
		#             anchor='x', position=0.05, showgrid=False),
		# yaxis3=dict(title='ATR', overlaying='y', side='right',
		#             anchor='x', position=0.10, showgrid=False),
		width=2000,
		height=1000,
		hovermode='x unified',
		dragmode='pan',
	)
	fig.update_xaxes(
		rangeslider=dict(visible=False),  # Optional: adds zoom slider if needed
		rangebreaks=[dict(values=dt_breaks, dvalue=60 * 1000)],  # 60秒/分钟* 1000毫秒/秒
		rangeselector=dict(
			# buttons=list(
			#     [
			#         dict(count=1, label="1h", step="hour", stepmode="backward"),
			#         dict(count=2, label="2h", step="hour", stepmode="backward"),
			#         dict(count=1, label="1d", step="day", stepmode="backward"),
			#         dict(count=2, label="2d", step="day", stepmode="backward"),
			#         # dict(count=1, label="1m", step="month", stepmode="todate"),
			#         # dict(count=1, label="1y", step="year", stepmode="backward"),
			#         dict(step="all"),
			#     ]
			# )
		),
		type=type,
		# dtick="M1", # 每月显示一次刻度
		# tickformat="%Y-%m-%d", # 日期格式
	)
	fig.update_xaxes(rangeslider=dict(visible=True), rangeslider_thickness=0.03, row=3, col=1)
	fig.update_yaxes(
		title='ATR & ADX',
		secondary_y=False,
		# range=[df[['ADX', 'ATR']].min().min() - (df[['ADX', 'ATR']].max().max() - df[['ADX', 'ATR']].min().min()) * 0.1, df[['ADX', 'ATR']].max().max() + (df[['ADX', 'ATR']].max().max() - df[['ADX', 'ATR']].min().min()) * .1],
		row=1,
		col=1,
	)
	fig.update_yaxes(
		title='ATR',
		secondary_y=True,
		# range=[df[['ADX', 'ATR']].min().min() - (df[['ADX', 'ATR']].max().max() - df[['ADX', 'ATR']].min().min()) * 0.1, df[['ADX', 'ATR']].max().max() + (df[['ADX', 'ATR']].max().max() - df[['ADX', 'ATR']].min().min()) * .1],
		row=1,
		col=1,
	)
	fig.update_yaxes(title='成交量', row=2, col=1)
	fig.update_yaxes(title='价格', row=3, col=1)

	# 保存为HTML文件
	file_name = f'AG {start_time.strftime("%Y%m%d")} to {end_time.strftime("%Y%m%d")} 夜盘交互式回放.html'
	save_path = os.path.join(
		folder_path,
		file_name,
	)
	fig.write_html(save_path)

	# 设置HTTP服务器
	handler = http.server.SimpleHTTPRequestHandler
	port = 8050
	location = os.path.join(os.path.abspath("."), save_path)
	with socketserver.TCPServer(('', port), handler):
		print('\n🚀 HTTP服务器启动成功!')
		# print(f"   地址: http://localhost:{port}")
		print(f'   图表地址: {location}')
		print('\n按 Ctrl+C 停止服务器')

		# 自动打开浏览器
		try:
			# webbrowser.open(f"http://localhost:{port}/{file_name}")
			webbrowser.open(location)
			print(' ✓ 已自动打开浏览器\n')
		except Exception as e:
			print(f' ⚠ 无法自动打开浏览器: {e}')
			print('请手动访问: ', os.path.join(os.path.abspath('.'), save_path) + '\n')


# K线自适应调整y轴范围 dash 可视化
def dash_auto_resize(
	df: pd.DataFrame,
	dt_obs: list,
	dt_breaks: list,
	start_time,
	end_time,
):
	fig = go.Figure()

	# 5.1 K 线
	fig.add_trace(
		go.Candlestick(
			x=df.index,
			open=df['open'],
			high=df['high'],
			low=df['low'],
			close=df['close'],
			name='K线',
			increasing=dict(line=dict(color='red')),
			decreasing=dict(line=dict(color='green')),
		),
		# row=1, col=1
	)

	# 5.2 布林带
	fig.add_trace(
		go.Scatter(
			x=df.index,
			# y=df["boll_up"],
			y=df['boll_UB'],
			line=dict(color='rgba(0,100,80,0.5)'),
			name='Boll Upper',
		),
		# row=1, col=1
	)
	fig.add_trace(
		go.Scatter(
			x=df.index,
			# y=df["boll_bot"],
			y=df['boll_LB'],
			line=dict(color='rgba(0,100,80,0.5)'),
			#  fill='tonexty',
			name='Boll Lower',
		),
		# row=1, col=1
	)
	fig.add_trace(
		go.Scatter(
			x=df.index,
			# y=df["boll_mid"],
			y=df['boll_MB'],
			line=dict(color='blue', width=1),
			name='Boll Mid',
		),
		# row=1, col=1
	)

	# 5.5 Donchian
	fig.add_trace(
		go.Scatter(
			x=df.index,
			# y=df["don_hi"],
			y=df['DC_Upper'],
			line=dict(color='gray', dash='dot'),
			name='Don High',
		),
		# row=1, col=1
	)
	fig.add_trace(
		go.Scatter(
			x=df.index,
			# y=df["don_lo"],
			y=df['DC_Lower'],
			line=dict(color='gray', dash='dot'),
			name='Don Low',
		),
		# row=1, col=1
	)

	fig.update_layout(
		title=f'AG {start_time.strftime("%Y%m%d")} ~ {end_time.strftime("%Y%m%d")} 夜盘 21:00-01:00 交互式回放.html',
		width=2000,
		height=1000,
		hovermode='x unified',
		dragmode='pan',
	)
	fig.update_xaxes(
		rangeslider=dict(visible=False),  # Optional: adds zoom slider if needed
		rangebreaks=[dict(values=dt_breaks, dvalue=60 * 1000)],  # 60秒/分钟* 1000毫秒/秒
		rangeselector=dict(
			buttons=list(
				[
					dict(count=1, label='1h', step='hour', stepmode='backward'),
					dict(count=2, label='2h', step='hour', stepmode='backward'),
					dict(count=1, label='1d', step='day', stepmode='backward'),
					dict(count=2, label='2d', step='day', stepmode='backward'),
					# dict(count=1, label="1m", step="month", stepmode="todate"),
					# dict(count=1, label="1y", step="year", stepmode="backward"),
					dict(step='all'),
				]
			)
		),
		# type="category",
		# dtick="M1", # 每月显示一次刻度
		# tickformat="%Y-%m-%d", # 日期格式
	)
	fig.update_xaxes(
		rangeslider=dict(visible=True),
		# rangeslider_thickness = 0.03,
		# row=1, col=1
	)
	fig.update_yaxes(
		title='价格',
		# row=1, col=1
	)

	# Build App
	app = JupyterDash(__name__)
	app.layout = html.Div(
		[
			dcc.Graph(id='dashFig', figure=fig),
		],
		style={'font-family': 'Arial', 'font-size': '0.9em'},
	)

	# get callback from rangeslider and update ranges on x & y axis
	@app.callback(Output('dashFig', 'figure'), [Input('dashFig', 'relayoutData')])
	def rangesliderchg(relayoutData):
		if relayoutData and 'xaxis.range' in relayoutData.keys():
			s = df.loc[
				df['date'].between(relayoutData['xaxis.range'][0], relayoutData['xaxis.range'][1]),
				[
					'open',
					'close',
					'high',
					'low',
					'boll_UB',
					'boll_MB',
					'boll_LB',
					'DC_Upper',
					'DC_Lower',
					'DC_Middle',
				],
			]
			# s = df.loc[df["trade_time"].between(relayoutData['xaxis.range'][0], relayoutData['xaxis.range'][1]), ["open","close","high","low","boll_up","boll_mid","boll_bot","don_hi","don_lo"]]
			s_range = s.max().max() - s.min().min()
			fig['layout']['yaxis']['range'] = [
				s.min().min() - s_range * 0.1,
				s.max().max() + s_range * 0.1,
			]
			fig['layout']['xaxis']['range'] = relayoutData['xaxis.range']
		return fig

	# Run app and display result inline in the notebook
	webbrowser.open_new('http://localhost:8050/')
	print(' ✓ 将自动打开浏览器')
	app.run(port=8050)
	# app.run()


# test
if __name__ == '__main__':
	# 数据预处理
	data_prep = data_preprocessing.Data_preprocessing()
	df = data_prep.load_data()
	dt_all, dt_obs, dt_breaks = data_prep.time_filter(df)

	df = data_prep.fill_missing_data(df, dt_all)

	# 指标计算
	df = quantitative_metrics.cal_metrics(df).add_metrics()
	# print(df.info())

	start_time, end_time = '2019-01-01', '2019-01-02'

	# 可视化
	html_subplot(df, dt_obs, dt_breaks, start_time, end_time, type='date')
	# html_subplot(df, dt_obs, dt_breaks, start_time, end_time)
	# dash_auto_resize(df, dt_obs, dt_breaks, start_time, end_time)
