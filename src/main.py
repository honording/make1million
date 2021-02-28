import json
import os
import time

from robinhood import RobinHood
from common import bColors
from common import FormatNumber

def printSummary(summary):
    """
    print day or week summary
    """
    total_floating_earnings = summary["current_floating_earnings"] + \
                              summary["total_history_trans_earnings"] + \
                              summary["dividends"] - \
                              summary["total_fees"]
    
    available_cash = summary["principles"] + \
                     summary["total_history_trans_earnings"] + \
                     summary["dividends"] - \
                     summary["total_fees"] + \
                     summary["total_cash_flow"]

    print("================================", summary["datetime"].date(), "================================")
    print("Current Floating Earnings:", FormatNumber(summary["current_floating_earnings"], "{:.2f}", "$"))
    print("Total History Earnings:", FormatNumber(summary["total_history_trans_earnings"], "{:.2f}", "$"))
    print("Total Paid Dividends:", FormatNumber(summary["dividends"], "{:.2f}", "$"))
    print("Total Fees:", FormatNumber(summary["total_fees"], "{:.2f}", "$"))
    print("Total Floating Earnings:", FormatNumber(total_floating_earnings, "{:.2f}", "$"), \
            "tarward to", FormatNumber(total_floating_earnings/my_robinhood.returnUltimateTarget()*100, "{:.3f}", trailing="%"), \
            "of", FormatNumber(my_robinhood.returnUltimateTarget(), "{:d}", "$") )
    print("                        ", FormatNumber(total_floating_earnings/summary["principles"]*100, "{:.2f}", trailing="%"), \
            "of", FormatNumber(summary["principles"], "{:.2f}", "$"))
    print("Available Cash:", FormatNumber(available_cash, "{:.2f}", "$"))

with open(os.environ.get("WORKSPACE") + "/config/user_auth.json") as f:
    auth_info = json.load(f)

my_robinhood = RobinHood()
my_robinhood.MFALogin(auth_info["robinhood"])

past_cal_day = 1
past_trading_day = 1
while past_trading_day <= 4:
    if past_cal_day == 1:
        summary = my_robinhood.returnDayWeekSummary(past_cal_day, "day", latest=True)
    else:
        summary = my_robinhood.returnDayWeekSummary(past_cal_day, "day", latest=False)
    if summary != None:
        past_trading_day += 1
        printSummary(summary)
    past_cal_day += 1

my_robinhood.MFALogoff()
