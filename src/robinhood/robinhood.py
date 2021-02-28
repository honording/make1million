import robin_stocks.robinhood as rs
import pyotp
import sys
import ntplib
import copy

from datetime import datetime as dt
from datetime import timedelta as dt_delta
from dateutil.parser import parse as dt_parse
from pytz import timezone as dt_timezone

from common import bColors
from common import FormatNumber
from common import isClose





class RobinHood:
    class __OrderHistory:
        def __init__(self, value):
            """
            Class init
            """
            self.__value = value

            # FIXME
            self.__time_zone = dt_timezone("America/New_York")

            for order in self.__value:
                last_transaction_datetime_est = dt_parse(order["last_transaction_at"]).astimezone(self.__time_zone)
                order["last_transaction_at"] = last_transaction_datetime_est

        def returnValue(self):
            """
            Return intial value
            """
            return self.__value

    def __init__(self, \
                 ultimate_target = 1000000, \
                 start_amount = 40000, \
                 start_datetime = 20200601, \
                 end_datetime = None):
        """
        Class init
        """
        self.__dividends_hisotry = None
        self.__orders_hisotry = None
        self.__bank_transfer_history = None

        self.__instrument_symbol_map = {}

        def getYearMonthDay(datetime):
            """
            Return year month and day from a 8 digits interger
            """
            return datetime // 10000, datetime // 100 % 100, datetime % 100

        self.__time_zone = dt_timezone("America/New_York")
        self.__ultimate_target = ultimate_target
        self.__start_amount = start_amount
        year, month, day = getYearMonthDay(start_datetime)
        self.__start_datetime = dt(year, month, day, tzinfo=self.__time_zone)
        if end_datetime == None:
            self.__end_datetime = dt.now(self.__time_zone)
        else:
            year, month, day = getYearMonthDay(end_datetime)
            self.__end_datetime = dt(year, month, day, tzinfo=self.__time_zone)


    def __getDividendsHistory(self):
        """
        Fetch all history dividends
        """
        print(f"{bColors.OKGREEN}Info: Pulling user's dividends.{bColors.ENDC}")
        self.__dividends_hisotry = rs.get_dividends()


    def __getOrderHistory(self):
        """
        Fetch all history orders
        """
        print(f"{bColors.OKGREEN}Info: Pulling user's orders.{bColors.ENDC}")
        self.__orders_hisotry = self.__OrderHistory(rs.get_all_stock_orders())


    def __getBankTransferHistory(self):
        """
        Fetch all history bank transcations
        """
        print(f"{bColors.OKGREEN}Info: Pulling user's bank transfer.{bColors.ENDC}")
        self.__bank_transfer_history = rs.get_bank_transfers()


    def __returnDayWeekStockHistory(self, symbol, offset, interval):
        """
        Return stock history for a givin day or week.
        """
        def returnSpan(offset, interval):
            """
            docstring
            """
            if interval == "day":
                if offset <= 7:
                    return "week"
                elif offset <= 27:
                    return "month"
                elif offset <= 90:
                    return "3month"
                elif offset <= 365:
                    return "year"
                elif offset <= 1780:
                    return "5year"
                else:
                    raise ValueError("offset is in wrong range (expect >= 0 and <= 1780).")
            elif interval == "week":
                if offset <= 4:
                    return "month"
                elif offset <= 12:
                    return "3month"
                elif offset <= 52:
                    return "year"
                elif offset <= 260:
                    return "5year"
                else:
                    raise ValueError("offset is in wrong range (expect >= 0 and <= 260).")
        
        def equalDayWeek(date_a, date_b, interval):
            """
            Compare if two dates are in the same week
            """
            if interval == "day":
                return date_a == date_b
            monday_a = date_a - dt_delta(days=date_a.weekday())
            monday_b = date_b - dt_delta(days=date_b.weekday())
            return monday_a == monday_b

        if interval != "week" and interval != "day":
            raise ValueError("interval is in wrong, expected day or week.")

        offset = abs(offset)
        interval_day = 1
        if interval == "week":
            interval_day = 7
        
        expected_date = (self.__end_datetime - dt_delta(days=offset*interval_day)).date()

        expected_historical = None
        stock_historicals = rs.get_stock_historicals(symbol, span=returnSpan(offset, interval), interval=interval)
        for stock_historical in stock_historicals:
            # Fix UTC to EST
            begins_date = dt_parse(stock_historical["begins_at"]).astimezone(self.__time_zone) + dt_delta(minutes=870)
            stock_historical["begins_at"] = begins_date
            stock_historical["ends_at"] = begins_date + dt_delta(minutes=390)
            if interval == "week":
                stock_historical["ends_at"] += dt_delta(days=4-begins_date.weekday())
            if equalDayWeek(begins_date.date(), expected_date, interval):
                expected_historical = stock_historical
        
        return expected_historical

    def __returnTodayStockHistory(self, symbol):
        """
        Return today's stock history for a givin symbol
        """
        expected_date = self.__end_datetime.date()

        # 5minute, 10minute, hour
        interval = "10minute"
        delta = {"5minute": 5, \
                 "10minute": 10, \
                 "hour": 60}

        stock_history = {}
        trade_date = None

        stock_historicals = rs.get_stock_historicals(symbol, span="day", interval=interval)
        for stock_historical in stock_historicals:
            begins_datetime_est = dt_parse(stock_historical["begins_at"]).astimezone(self.__time_zone)
            trade_info = {"start_time": begins_datetime_est, \
                          "end_time": begins_datetime_est + dt_delta(minutes=delta[interval]), \
                          "open_price": stock_historical["open_price"], \
                          "close_price": stock_historical["close_price"] }

            trade_date = begins_datetime_est.date()
            if trade_date in stock_history:
                # stock_history[trade_date]
                if trade_info["start_time"] < stock_history[trade_date]["start_time"]:
                    stock_history[trade_date]["start_time"] = trade_info["start_time"]
                    stock_history[trade_date]["open_price"] = trade_info["open_price"]
                if trade_info["end_time"] > stock_history[trade_date]["end_time"]:
                    stock_history[trade_date]["end_time"] = trade_info["end_time"]
                    stock_history[trade_date]["close_price"] = trade_info["close_price"]
            else:
                stock_history[trade_date] = trade_info

        return stock_history[trade_date]


    def __returnMergedOrders(self):
        """
        Return a merged order dict indexed by stocks.
        """
        def sortHelper(v):
            return v["last_transaction_at"]

        if self.__orders_hisotry == None:
            self.__getOrderHistory()
        
        merged_orders = {}

        for order in self.__orders_hisotry.returnValue():
            last_transaction_datetime_est = order["last_transaction_at"]
            if last_transaction_datetime_est > self.__start_datetime and last_transaction_datetime_est < self.__end_datetime:
                instrument = order["instrument"]
                if instrument in merged_orders:
                    merged_orders[instrument].append(order)
                else:
                    merged_orders[instrument] = [order]

        # Replace stock url with symbols
        for instrument in list(merged_orders):
            if not instrument in self.__instrument_symbol_map:
                self.__instrument_symbol_map[instrument] = rs.get_instrument_by_url(instrument)["symbol"]
            symbol = self.__instrument_symbol_map[instrument]
            merged_orders[symbol] = merged_orders.pop(instrument)
            merged_orders[symbol].sort(key=sortHelper)

        return merged_orders

    def returnUltimateTarget(self):
        """
        Return ultimate target
        """
        return self.__ultimate_target


    def returnDayWeekSummary(self, offset, interval, latest = False):
        """
        Return day or week summary by the end of day or week
        """
        sanity_check = self.__returnDayWeekStockHistory("SPY", offset, interval)
        if sanity_check == None:
            return None

        current_floating_earnings = 0
        total_history_trans_earnings = 0
        total_fees = 0
        total_cash_flow = 0

        summary = {}

        merged_orders = self.__returnMergedOrders()

        for symbol, transactions in merged_orders.items():
            # print(symbol, len(transactions))

            current_quantity = 0
            current_trans_amount = 0 

            history_trans_amount = 0

            for transaction in transactions:
                if transaction["state"] == "filled" and transaction["last_transaction_at"] <= sanity_check["ends_at"]:
                    side = transaction["side"]
                    cumulative_quantity = float(transaction["cumulative_quantity"])
                    average_price = float(transaction["average_price"])
                    total_fees = total_fees + float(transaction["fees"])
                    if side == "buy":
                        current_quantity += cumulative_quantity
                        current_trans_amount -= cumulative_quantity * average_price
                    else:
                        current_quantity -= cumulative_quantity
                        current_trans_amount += cumulative_quantity * average_price
                    if isClose(current_quantity, 0):
                        history_trans_amount += current_trans_amount
                        current_quantity = 0
                        current_trans_amount = 0
            total_history_trans_earnings += history_trans_amount
            total_cash_flow += current_trans_amount
            # print("Total Trans Earnings:", FormatNumber(history_trans_amount, "{:.2f}", "$"))
            if not isClose(current_quantity, 0):
                price = 0
                if latest:
                    price = float(rs.get_latest_price(symbol, includeExtendedHours=True)[0])
                else:
                    stock_history = self.__returnDayWeekStockHistory(symbol, offset, interval)
                    if stock_history["interpolated"]:
                        # print("False date, using 10minute data instead")
                        stock_history = self.__returnTodayStockHistory(symbol)
                    # print(stock_history)
                    price = float(stock_history["close_price"])
                # print("Price:", price)
                # print("Quantity:", FormatNumber(current_quantity, "{:.2f}"))
                floating_earning = price * current_quantity + current_trans_amount
                current_floating_earnings += floating_earning
                # print("Floating Earning:", FormatNumber(floating_earning, "{:.2f}", "$"))
            # print("-------------------------------")
        

        if latest:
            summary["datetime"] = self.__end_datetime
            summary["principles"] = self.returnPrinciplesBalance()
            summary["dividends"] = self.returnTotalDividends()
        else:
            summary["datetime"] = sanity_check["ends_at"]
            summary["principles"] = self.returnPrinciplesBalance(sanity_check["ends_at"])
            summary["dividends"] = self.returnTotalDividends(sanity_check["ends_at"])
        
        summary["current_floating_earnings"] = current_floating_earnings
        summary["total_history_trans_earnings"] = total_history_trans_earnings
        summary["total_cash_flow"] = total_cash_flow
        summary["principles"] = self.returnPrinciplesBalance(sanity_check["ends_at"])
        summary["dividends"] = self.returnTotalDividends(sanity_check["ends_at"])
        summary["total_cash_flow"] = total_cash_flow
        summary["total_fees"] = total_fees

        return summary


    def returnPrinciplesBalance(self, date=None):
        """
        Return bank transfer balance from start date time
        """
        if self.__bank_transfer_history == None:
            self.__getBankTransferHistory()

        end_datetime = self.__end_datetime
        if date != None:
            end_datetime = date
        
        principle_change = 0
        for transaction in self.__bank_transfer_history:
            posted_date = dt_parse(transaction["expected_landing_datetime"]).astimezone(self.__time_zone)
            if posted_date >= self.__start_datetime and posted_date <= end_datetime:
                if transaction["state"] == "completed":
                    if transaction["direction"] == "deposit":
                        principle_change += float(transaction["amount"])
                    else:
                        principle_change -= float(transaction["amount"])
        return principle_change + self.__start_amount
    
    def returnTotalDividends(self, date=None):
        """
        Return total dividends up to date
        """
        if self.__dividends_hisotry == None:
            self.__getDividendsHistory()

        end_datetime = self.__end_datetime
        if date != None:
            end_datetime = date

        total_dividends = 0

        for dividend in self.__dividends_hisotry:
            paid_datetime_est = dt_parse(dividend["paid_at"]).astimezone(self.__time_zone)
            if paid_datetime_est >= self.__start_datetime and paid_datetime_est <= end_datetime:
                total_dividends = total_dividends + float(dividend["amount"])
        return total_dividends    


    def forceUpdate(self, bank_transfer = True, stock_orders = True, stock_dividends = True):
        """
        docstring
        """
        if bank_transfer:
            self.__getBankTransferHistory()
        if stock_orders:
            self.__getOrderHistory()
        if stock_dividends:
            self.__getDividendsHistory()


    def MFALogin(self, auth_info):
        """
        Login with MFA codes
        """
        totp  = pyotp.TOTP(auth_info["token"]).now()
        try:
            login = rs.login(auth_info["user_name"], auth_info["user_passwd"], store_session=True, mfa_code=totp)
        except:
            print(f"{bColors.FAIL}Fail: Unable to login robinhood by given credentials.{bColors.ENDC}")
            sys.exit()
        print(f"{bColors.OKGREEN}Info: Login successful.{bColors.ENDC}")


    def MFALogoff(self):
        """
        Log off from robinhood account
        """
        rs.logout()
        print(f"{bColors.OKGREEN}Info: Logoff successful.{bColors.ENDC}")
