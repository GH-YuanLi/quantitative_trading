import datetime
import http.server
import os
import socketserver
import subprocess
import webbrowser

import pandas as pd
import plotly.graph_objects as go

# import dash_core_components as dcc
# import dash_html_components as html
from dash import dcc, html
from dash.dependencies import Input, Output, State
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
	folder_path: str = './',
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
			x=df.trade_time_str,
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
		title='AG {} ~ {} 夜盘 21:00-01:00 交互式回放'.format(
			start_time.strftime('%Y%m%d'), end_time.strftime('%Y%m%d')
		),
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
	# fig.update_xaxes(rangeslider=dict(visible=True), rangeslider_thickness=0.03, row=3, col=1)
	fig.update_yaxes(
		title='ADX',
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
	file_name = 'AG {} to {} 夜盘交互式回放.html'.format(start_time.strftime('%Y%m%d'), end_time.strftime('%Y%m%d'))
	save_path = os.path.join(
		folder_path,
		file_name,
	)
	fig.write_html(save_path)

	# 设置HTTP服务器
	handler = http.server.SimpleHTTPRequestHandler
	port = 8050
	location = os.path.join(os.path.abspath('.'), save_path)
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


# 交互式：添加时间范围搜索栏，按输入的时间范围截取趋势、或时间节点前后20分钟的观测时间范围
def dash_w_filter(
	df: pd.DataFrame,
	dt_obs: list,
	dt_breaks: list,
	start_time,
	end_time,
	type: str = 'date',  # 可视化横坐标类型
):
	assert type in ['date', 'category'], "type should be one of ['date', 'category']"

	def _build_fig(df_slice: pd.DataFrame, rb_values=None) -> go.Figure:
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

		# K线
		fig.add_trace(
			go.Candlestick(
				x=df_slice.trade_time_str,
				open=df_slice['open'],
				high=df_slice['high'],
				low=df_slice['low'],
				close=df_slice['close'],
				name='K线',
				increasing=dict(line=dict(color='red')),
				decreasing=dict(line=dict(color='green')),
			),
			row=3,
			col=1,
		)

		# 布林带
		fig.add_trace(
			go.Scatter(
				x=df_slice.trade_time_str,
				y=df_slice['boll_UB'],
				line=dict(color='rgba(0,100,80,0.5)'),
				name='Boll Upper',
			),
			row=3,
			col=1,
		)
		fig.add_trace(
			go.Scatter(
				x=df_slice.trade_time_str,
				y=df_slice['boll_LB'],
				line=dict(color='rgba(0,100,80,0.5)'),
				name='Boll Lower',
			),
			row=3,
			col=1,
		)
		fig.add_trace(
			go.Scatter(
				x=df_slice.trade_time_str, y=df_slice['boll_MB'], line=dict(color='blue', width=1), name='Boll Mid'
			),
			row=3,
			col=1,
		)

		# Donchian
		fig.add_trace(
			go.Scatter(
				x=df_slice.trade_time_str, y=df_slice['DC_Upper'], line=dict(color='gray', dash='dot'), name='Don High'
			),
			row=3,
			col=1,
		)
		fig.add_trace(
			go.Scatter(
				x=df_slice.trade_time_str, y=df_slice['DC_Lower'], line=dict(color='gray', dash='dot'), name='Don Low'
			),
			row=3,
			col=1,
		)
		fig.add_trace(
			go.Scatter(
				x=df_slice.trade_time_str, y=df_slice['DC_Middle'], line=dict(color='gray', dash='dot'), name='Don Mid'
			),
			row=3,
			col=1,
		)

		# 5.4 ADX
		fig.add_trace(
			go.Scatter(
				x=df_slice.trade_time_str,
				y=df_slice['ADX'],
				line=dict(color='orange'),
				name='ADX(10)',  # yaxis="y",
			),
			secondary_y=False,
			row=1,
			col=1,
		)

		# 5.5 ATR
		fig.add_trace(
			go.Scatter(
				x=df_slice.trade_time_str,
				y=df_slice['ATR'],
				line=dict(color='purple'),
				name='ATR(10)',  # yaxis="y2",
			),
			secondary_y=True,
			row=1,
			col=1,
		)

		# 5.6 volume
		colors = {True: 'red', False: 'green'}
		fig.add_trace(
			go.Bar(
				x=df_slice.trade_time_str,
				y=df_slice['volume'],
				name='Volume',
				opacity=0.9,
				marker=dict(
					color=df_slice['flag_increase'].map(colors),
					line=dict(color=df_slice['flag_increase'].map(colors), width=0.1),
				),
				showlegend=False,
			),
			row=2,
			col=1,
		)

		# 根据切片设置标题的日期范围
		fig.update_layout(
			title='<b>AG {} ~ {} 夜盘交互式回放</b>'.format(
				start_time.strftime('%Y年%m月%d日'), end_time.strftime('%Y年%m月%d日')
			),
			width=2000,
			height=1000,
			hovermode='x unified',
			dragmode='pan',
		)
		fig.update_xaxes(
			rangeslider=dict(visible=False),
			rangebreaks=[dict(values=(rb_values if rb_values is not None else dt_breaks), dvalue=60 * 1000)],
			type=type,
		)
		fig.update_yaxes(title='ADX', secondary_y=False, row=1, col=1)
		fig.update_yaxes(title='ATR', secondary_y=True, row=1, col=1)
		fig.update_yaxes(title='成交量', row=2, col=1)
		fig.update_yaxes(title='价格', row=3, col=1)
		return fig

	# 默认时间范围：使用数据中的最小/最大 trade_time
	df = df.reindex(dt_obs)
	start_default = str(min(df['trade_time_str']))
	end_default = str(max(df['trade_time_str']))

	# 初始子集
	df_init = df[(df['trade_time_str'] >= start_default) & (df['trade_time_str'] <= end_default)]
	fig = _build_fig(df_init)

	# 创建统一的界面，同时支持两种过滤模式
	app = JupyterDash(__name__)
	app.layout = html.Div(
		[
			html.Div(
				[
					# 过滤模式一：通过时间节点选择（观测时间前后20分钟）
					html.Div(
						[
							html.Label(
								'观测时间模式：选择观测时间（前后20分钟）',
								style={'font-weight': 'bold', 'margin-bottom': '10px'},
							),
							html.Div(
								[
									html.Label('观测时间', style={'margin-right': '10px'}),
									dcc.Input(
										id='observe-time',
										type='text',
										value=None,
										placeholder='YYYY-MM-DD HH:MM:SS',
										style={'width': '160px', 'margin-right': '10px'},
									),
									html.Button(
										'应用观测时间',
										id='apply-point',
										n_clicks=0,
										style={
											'background-color': '#4CAF50',
											'color': 'white',
											'border': 'none',
											'padding': '8px 16px',
										},
									),
								],
								style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'},
							),
						],
						style={
							'border': '1px solid #ddd',
							'padding': '15px',
							'border-radius': '5px',
							'margin-bottom': '20px',
						},
					),
					# 过滤模式二：通过时间范围选择
					html.Div(
						[
							html.Label(
								'时间范围模式：选择开始和结束时间',
								style={'font-weight': 'bold', 'margin-bottom': '10px'},
							),
							html.Div(
								[
									html.Label('开始时间', style={'margin-right': '10px'}),
									dcc.Input(
										id='start-time',
										type='text',
										value=start_default,
										# value=None,
										placeholder='YYYY-MM-DD HH:MM:SS',
										style={'width': '160px', 'margin-right': '10px'},
									),
									html.Label('结束时间', style={'margin-right': '10px'}),
									dcc.Input(
										id='end-time',
										type='text',
										value=end_default,
										# value=None,
										placeholder='YYYY-MM-DD HH:MM:SS',
										style={'width': '160px', 'margin-right': '10px'},
									),
									html.Button(
										'应用时间范围',
										id='apply-range',
										n_clicks=0,
										style={
											'background-color': '#2196F3',
											'color': 'white',
											'border': 'none',
											'padding': '8px 16px',
											'margin-right': '10px',
										},
									),
									html.Button(
										'明细数据下载',
										id='download-detail',
										n_clicks=0,
										style={
											# 'background-color': '#2196F3',
											# 'color': 'white',
											'border': 'none',
											'padding': '8px 16px',
											'margin-right': '10px',
										},
									),
								],
								style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '20px'},
							),
						],
						style={
							'border': '1px solid #ddd',
							'padding': '15px',
							'border-radius': '5px',
							'margin-bottom': '20px',
						},
					),
				],
				style={'margin': '20px 0'},
			),
			dcc.Graph(id='dashFig', figure=fig),
		],
		style={'font-family': 'Arial', 'font-size': '0.9em', 'padding': '20px'},
	)

	# 回调函数：处理观测时间模式
	@app.callback(
		Output('dashFig', 'figure', allow_duplicate=True),
		Input('apply-point', 'n_clicks'),
		State('observe-time', 'value'),  # 观测时间
		prevent_initial_call=True,
	)
	def _apply_observe_time(n_clicks, obs_value):
		try:
			if not obs_value:
				return _build_fig(df_init, rb_values=dt_breaks)

			# 获取观测时间前后20分钟的时间范围
			start_obs_v = str(pd.to_datetime(obs_value) - pd.Timedelta(minutes=20))
			end_obs_v = str(pd.to_datetime(obs_value) + pd.Timedelta(minutes=20))

			# 截取范围
			df_slice = df[(df['trade_time_str'] >= start_obs_v) & (df['trade_time_str'] <= end_obs_v)]
			# 将缺失时间限定到当前输入范围，避免无关的断点
			local_breaks = [t for t in dt_breaks if start_obs_v <= t <= end_obs_v]

			if len(df_slice) == 0:
				return _build_fig(df_init, rb_values=dt_breaks)
			return _build_fig(df_slice, rb_values=(local_breaks or dt_breaks))
		except Exception as e:
			print(f'观测时间模式错误: {e}')
			return _build_fig(df_init, rb_values=dt_breaks)

	# 回调函数：处理时间范围模式
	@app.callback(
		Output('dashFig', 'figure'),
		Input('apply-range', 'n_clicks'),
		State('start-time', 'value'),  # 开始时间
		State('end-time', 'value'),  # 终止时间
		prevent_initial_call=True,
	)
	def _apply_time_range(n_clicks, start_value, end_value):
		try:
			start_v = start_value or start_default
			end_v = end_value or end_default

			# 截取范围
			df_slice = df[(df['trade_time_str'] >= start_v) & (df['trade_time_str'] <= end_v)]
			# 将缺失时间限定到当前输入范围，避免无关的断点
			local_breaks = [t for t in dt_breaks if start_v <= t <= end_v]

			# 容错：若输入为空，使用默认
			if len(df_slice) == 0:
				return _build_fig(df_init, rb_values=dt_breaks)
			return _build_fig(df_slice, rb_values=(local_breaks or dt_breaks))

		except Exception as e:
			print(f'时间范围模式错误: {e}')
			return _build_fig(df_init, rb_values=dt_breaks)

	@app.callback(
		Output('dashFig', 'children'),
		Input('download-detail', 'n_clicks'),
		State('start-time', 'value'),  # 开始时间
		State('end-time', 'value'),  # 终止时间
		prevent_initial_call=True,
	)
	def _download_details(n_clicks, start_value, end_value):
		try:
			# 获取变量
			variable_lst = [
				'open',
				'close',
				'high',
				'low',
				'boll_MB',
				'boll_UB',
				'boll_LB',
				'DC_Upper',
				'DC_Lower',
				'DC_Middle',
				'ADX',
				'ATR',
			]
			# 截取范围
			df_downloads = df[(df['trade_time_str'] >= start_value) & (df['trade_time_str'] <= end_value)][variable_lst]

			file_name = f"""AG {pd.to_datetime(start_value).strftime('%Y%m%d')} - {pd.to_datetime(end_value).strftime('%Y%m%d')} 夜盘明细数据_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"""
			location = os.path.join(os.path.abspath('.'), 'output', file_name)

			df_downloads.to_excel(location, index=True)
			print(f'\n选取的明细数据已保存至 {location}\n')

		except Exception as e:
			print(f'{e}')

	webbrowser.open_new('http://localhost:8051/')
	print(' ✓ 将自动打开浏览器')
	app.run(port=8051)


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
		title='<b>AG {} ~ {} 夜盘 21:00-01:00 交互式回放</b>'.format(
			start_time.strftime('%Y%m%d'), end_time.strftime('%Y%m%d')
		),
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


# 表格展示并存为 html / Excel
def table_show(
	df: pd.DataFrame,
	dt_obs,
	start_time,
	end_time,
	labels: list = ['label_1', 'label_2', 'label_3'],
	folder_path: str = './output/',
):
	df = df.reindex(dt_obs)
	df = df[df[labels].notnull().any(axis=1)][
		['trade_time', 'DC_Upper', 'DC_Lower', 'DC_high_20', 'DC_low_20', 'DC_high_diff_20', 'DC_low_diff_20']
		+ labels
		+ ['cnt_rule_trigger']
	]

	# fig = go.Figure(data=[go.Table(
	# 				header=dict(
	# 					values=list(df.columns),
	# 					# fill_color='paleturquoise',
	# 					align='center'),
	# 				cells=dict(
	# 					values=[df[i] for i in df.columns],
	# 				# fill_color='lavender',
	# 				align='center'
	# 				))
	# 				])

	# fig.layout.update(title_text = f"<b>AG {start_time.strftime("%Y%m%d")} to {end_time.strftime("%Y%m%d")} 夜盘触发规则交易记录</b>")
	file_name = 'AG {} to {} 夜盘起涨点_{}.xlsx'.format(
		start_time.strftime('%Y%m%d'), end_time.strftime('%Y%m%d'), datetime.datetime.now().strftime('%Y%m%d')
	)
	save_path = os.path.join(
		folder_path,
		file_name,
	)
	df.to_excel(save_path, index=False)

	# 自动打开写入的Excel文件
	location = os.path.join(os.path.abspath('.'), save_path)
	if os.name == 'nt':  # 如果是 Windows 系统
		os.startfile(location)
		print(' ✓ 已自动打开 Excel 文件')
	else:  # 如果是其他系统，可以尝试使用 subprocess 模块
		try:
			subprocess.Popen(['xdg-open', location])
		except OSError:
			print('Could not open the file.')

	# # 设置HTTP服务器

	# 自动打开浏览器
	# try:
	# 	webbrowser.open(location)
	# 	print(' ✓ 已自动打开浏览器\n')
	# except Exception as e:
	# 	print(f' ⚠ 无法自动打开浏览器: {e}')
	# 	print('请手动访问: ', os.path.join(os.path.abspath('.'), save_path) + '\n')


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
	# 使用时间范围搜索栏的交互式版本：
	# dash_time_range_filter(df, dt_obs, dt_breaks, start_time, end_time, type='date')
