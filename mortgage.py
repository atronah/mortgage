from datetime import date, timedelta
from calendar import monthrange

class Mortgage(object):
    def __init__(self, start_date, amount, rate, duration):
        self.start_date = start_date
        self.amount = amount
        self.rate = rate
        self.duration = duration
        self.holidays = []
        self.extra_payments = []

    @staticmethod
    def add_months(to_date, months_count=1):
        month = to_date.month + months_count
        year = to_date.year + (month - 1) // 12
        month = month % 12 or 12
        day = min(to_date.day, monthrange(year, month)[1])
        return date(year, month, day)

    @staticmethod
    def calculate_montly_payment(balance, rate, repayments_left):
        month_rate = rate / 100 / 12 # 12 - months in year, 100 - %
        return balance * month_rate / (1 - (1 + month_rate)**(-repayments_left))

    @staticmethod
    def calculate_interest_charges(from_date, to_date, balance, rate):
        days_in_year = (date(to_date.year + 1, 1, 1) - date(to_date.year, 1, 1)).days
        days_in_prev_year = days_in_year \
                            if to_date.year == from_date.year \
                            else (date(from_date.year + 1, 1, 1) - date(from_date.year, 1, 1)).days
        if days_in_year == days_in_prev_year:
            days_rate = rate * (to_date - from_date).days / (days_in_year * 100)
        else:
            days_rate = (date(from_date.year, 12, 31) - from_date).days / days_in_prev_year
            days_rate += ((to_date - date(to_date.year, 1, 1)).days + 1) / days_in_year
            days_rate = rate * days_rate / 100
        return balance * days_rate


    def is_holiday(self, checked_date):
        return checked_date.weekday() in (5, 6) or checked_date in self.holidays

    def skip_holidays(self, for_date):
        while self.is_holiday(for_date):
            for_date += timedelta(days=1)
        return for_date

    def add_extra_payment(self, payment_date, payment_amount):
        self.extra_payments.append((payment_date, payment_amount))

    def repayments_schedule(self):
        extra_payments = self.extra_payments
        extra_payments.sort(key=lambda x: x[0])
        extra_payment = None

        adate = self.start_date
        fdate = self.skip_holidays(adate)
        payment = 0.0
        interest_charge = 0.0
        balance = self.amount
        is_extra = False

        yield adate, fdate, payment, interest_charge, balance, is_extra

        payment_number = 1
        extra_payment = extra_payments.pop(0) if extra_payments else None
        recalculate_payment = True
        while payment_number <= self.duration:
            prev_date = adate
            adate = self.add_months(self.start_date, payment_number)

            interest_charge = round(self.calculate_interest_charges(prev_date, adate, balance, self.rate), 2)
            if extra_payment and extra_payment[0] < adate:
                payment_number -= 1
                is_extra = True
                adate, payment = extra_payment
                extra_payment = extra_payments.pop(0) if extra_payments else None
                interest_charge = round(self.calculate_interest_charges(prev_date, adate, balance, self.rate), 2)
            elif is_extra:
                payment = interest_charge
                is_extra = False
                recalculate_payment = True
            elif recalculate_payment:
                payment = self.calculate_montly_payment(balance, self.rate, self.duration - payment_number + 1)
                recalculate_payment = False

            fdate = self.skip_holidays(adate)
            balance = round(balance + interest_charge - payment, 2)
            if balance < 300:
                payment = payment + balance
                balance = 0.0
            payment = round(payment, 2)

            yield adate, fdate, payment, interest_charge, balance, is_extra

            payment_number += 1
