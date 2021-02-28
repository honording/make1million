from __future__ import print_function, unicode_literals

import json
import os, sys
import time

from robinhood import RobinHood
from common import bColors
from common import FormatNumber
from common import isClose

from PyInquirer import style_from_dict, Token, prompt, Separator, ValidationError
from pprint import pprint



def cashValidator(val_in, val):
    try:
        float(val_in)
    except ValueError:
        raise ValidationError(message="Please enter a number",
                              cursor_position=len(val_in))
    if float(val_in) > val:
        raise ValidationError(message="Please enter a number less or equal than " + str(val),
                              cursor_position=len(val_in))
    if float(val_in) < 0:
        raise ValidationError(message="Please enter a number larger or equal than 0",
                              cursor_position=len(val_in))
    return True

def stockValidator(symbol, rs):
    if symbol == "":
        return True
    info, price = rs.returnCompanyInfo(symbol)
    if info == []:
        raise ValidationError(message="Please enter a valid stock symbol (empty to finish)",
                              cursor_position=len(symbol))
    return True

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

style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})


# prompt_holdings = {
#     'type': 'checkbox',
#     'message': 'Select existing holdings to rebalance',
#     'name': 'holdings',
#     'choices': [
#         {
#             'name': 'AAPL',
#             'checked': True
#         },
#         {
#             'name': 'ASML',
#             'checked': True
#         }
#     ]
# }


# past_cal_day = 1
# past_trading_day = 1
# while past_trading_day <= 4:
#     if past_cal_day == 1:
#         summary = my_robinhood.returnDayWeekSummary(past_cal_day, "day", latest=True)
#     else:
#         summary = my_robinhood.returnDayWeekSummary(past_cal_day, "day", latest=False)
#     if summary != None:
#         past_trading_day += 1
#         printSummary(summary)
#     past_cal_day += 1




def askOptions():
    os.system('clear')
    questions = [
        {
            'type': 'list',
            'name': 'options',
            'message': 'What do you want to do?',
            'choices': [
                'Load Actions',
                'Create New Action',
                'Quit'
            ]
        }
    ]
    return prompt(questions, style = style)["options"]

def createRebalanceList(rs):
    os.system('clear')

    questions = []

    available_cash = rs.returnAvailableCash()

    prompt_cash = {
        'type': 'input',
        'message': 'Enter the amount of cash to rebalance',
        'name': 'cash',
        'default': "0",
        'validate': lambda val: cashValidator(val, available_cash),
        'filter': lambda val: float(val)
    }

    if not isClose(available_cash, 0):
        prompt_cash['default'] = str(available_cash)
        questions.append(prompt_cash)

    answers = prompt(questions, style = style)

    cash_for_rebalancing = answers['cash']

    questions = [
        {
            'type': 'input',
            'name': 'symbol',
            'message': 'What is your stock symbol to add?',
            'validate': lambda val: stockValidator(val, rs),
            'filter': lambda val: val.upper()
        }
    ]
    rebalance_list = []
    while True:
        answers = prompt(questions, style = style)
        symbol = answers["symbol"]
        if symbol == "":
            break
        info, price = rs.returnCompanyInfo(symbol)
        print("  Company:", info[0]['name'])
        print("  Latest Close Price:", price[0])
        print("  Fractional Trade:", info[0]['fractional_tradability'])
        answers = prompt({
            'type': 'confirm',
            'name': 'add',
            'message': 'Confirm to add?',
            'default': True
        }, style = style)
        if answers['add']:
            rebalance_list.append(symbol)

    return rebalance_list, cash_for_rebalancing

def createAction(rebalance_list, cash):
    

def user_prompt(rs):
    option = askOptions()
    while option != "Quit":
        if option == "Load Actions":
            print("nb")
        if option == "Create New Action":
            rebalance_list, cash_for_rebalancing = createRebalanceList(rs)
            createAction(rebalance_list, cash_for_rebalancing)
        option = askOptions()

user_prompt(my_robinhood)

my_robinhood.MFALogoff()
