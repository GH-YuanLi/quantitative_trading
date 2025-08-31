# setup rules to filter the data：通过规则打标签，并展示数据

# rule one: <name the rule>
class rule_1:
	"""
	rule description: find trafing time m, s.t. satisfies one of the the conditions below
	"""

	def __init__(self, df):
		self.df = df
		self.name = 'rule_1'
		self.description = 'rule description: find trafing time m, s.t. satisfies one of the the conditions below'

	def apply(self, shift=20):
		# 计算过程
		self.df['DC_high_20'] = self.df['DC_Upper'].shift(-shift)
		self.df['DC_low_20'] = self.df['DC_Lower'].shift(-shift)
		self.df['DC_high_diff_20'] = +self.df['DC_Upper'].shift(-shift) - self.df['DC_Upper']
		self.df['DC_low_diff_20'] = -self.df['DC_Lower'].shift(-shift) + self.df['DC_Lower']
		# 规则打标
		# 1.m+20时刻的唐奇安高点-m时刻的唐奇安高点 >= 15
		self.df.loc[self.df['DC_high_diff_20'] >= 15, 'flag_DC_high_le_15'] = True
		# 2.m时刻的唐奇安低点-m+20时刻的唐奇安低点 >= 15
		self.df.loc[self.df['DC_low_diff_20'] >= 15, 'flag_DC_low_le_15'] = True

		return self.df

	def stat(self):
		# 1）统计这一年有多少个交易日
		# 2）这一年出现了多少次满足寻找目标要求且非连续的m，所谓非连续即假如某个m满足要求了，若m-1也是满足要求的，则m不计入统计结果，无论这个m-1有没有被统计进去
		# 3）根据trade_date（即相同的trade_date代表在同一交易日），计算出每天平均出现多少次满足2）要求的m（保留1位小数），并计算出出现次数的标准差
		# 按年度打印出统计结果，统计结果不需要保存进任何csv文件
		self.df['year'] = self.df['date'].dt.year
		self.df["flag_trade_day"] = self.df["trade_day"]
		stat_1 = self.df.pivot_table(
			index = ['year', 'trade_day'],
			values = ["flag_trade_day"],
			aggfunc = {"flag_trade_day":"nunique"}
		)
		# print(stat_1)
		df_stat = self.df[(self.df.flag_DC_high_le_15 == 1) | (self.df.flag_DC_low_le_15 == 1)]
		df_stat['date_shift'] = df_stat['date'].shift(1)
		df_stat['time_diff'] = df_stat.apply(lambda x: (x['date'] - x['date_shift']).seconds / 60, axis=1)
		df_stat.loc[df_stat.time_diff > 1, 'flag_stat_1'] = 1

		stat_2 = df_stat.pivot_table(
			index=['year', 'trade_day'],
			values=['flag_stat_1'],
			aggfunc={'flag_stat_1':'sum'},
		)
		stat_3 = stat_1.merge(stat_2, right_index = True, left_index = True, how = 'left').fillna(0).reset_index().rename(columns = {"trade_day":"交易日数量", "flag_stat_1":"单交易日规则满足数量"})
		# print(stat_3)
		stat_3.to_csv("stat_3.csv", encoding = 'utf-8-sig', index = False)
		stat = stat_3.pivot_table(
			index = 'year',
			values = ['交易日数量', '单交易日规则满足数量'],
			aggfunc = {'交易日数量':'count', '单交易日规则满足数量':['mean', 'std']},
		)
		print(stat)




# rule two: <name the rule>
def rule_2(df):
	"""
	rule description: describe the rule here
	"""
	df.loc[df['volume'] > 1000, 'label_2'] = 'volume > 1000'
	return df


# rule three: <name the rule>
def rule_3(df):
	"""
	rule description: describe the rule here
	"""
	df.loc[df['volume'] == 996, 'label_3'] = 'volume = 996'
	return df
