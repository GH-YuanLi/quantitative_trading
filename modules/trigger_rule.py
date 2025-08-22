# setup rules to filter the data：通过规则打标签，并展示数据

# rule one: <name the rule>
def rule_1(df):
	"""
	rule description: describe the rule here
	"""
	df.loc[df['close'] >= 7000, 'label_1'] = 'close > 7000'
	return df


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