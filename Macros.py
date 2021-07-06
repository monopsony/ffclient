a = """
list set MasterHousing MasterGlamour CraftQuests
sell list
sales filter (salesPerDay > 0.4) & (craftPrice < 500000)
sales sort expProfitPerDay
sales show 20
"""

sell = """
sell list
sales filter (salesPerDay > 0.4) & (craftPrice < 500000)
sales sort expProfitPerDay
sales show 20
"""


test = """
list set test2
sell list
sales sort expProfitPerDay
sales show 20
"""
