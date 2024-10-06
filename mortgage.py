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
    def calculate_monthly_payment(balance, rate, repayments_left):
        month_rate = rate / 100 / 12  # 12 - months in year, 100 - %
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
        self.extra_payments.sort(key=lambda x: x[0])

    def repayments_schedule(self):
        adate = self.start_date
        fdate = self.skip_holidays(adate)
        payment = 0.0
        interest_charge = 0.0
        balance = self.amount
        is_extra = False

        yield adate, fdate, payment, interest_charge, balance, is_extra

        payment_number = 1
        extra_payment = self.extra_payments.pop(0) if self.extra_payments else None
        recalculate_payment = True
        while payment_number <= self.duration:
            prev_date = adate
            adate = self.add_months(self.start_date, payment_number)

            interest_charge = round(self.calculate_interest_charges(prev_date, adate, balance, self.rate), 2)
            if not extra_payment and self.extra_payments:
                extra_payment = self.extra_payments.pop(0)

            if extra_payment and extra_payment[0] < adate:
                payment_number -= 1
                is_extra = True
                adate, payment = extra_payment
                extra_payment = self.extra_payments.pop(0) if self.extra_payments else None
                interest_charge = round(self.calculate_interest_charges(prev_date, adate, balance, self.rate), 2)
            elif is_extra:
                payment = interest_charge
                is_extra = False
                recalculate_payment = True
            elif recalculate_payment:
                payment = self.calculate_monthly_payment(balance, self.rate, self.duration - payment_number + 1)
                recalculate_payment = False

            fdate = self.skip_holidays(adate)
            balance = round(balance + interest_charge - payment, 2)
            if balance < 300:
                payment = payment + balance
                balance = 0.0
            payment = round(payment, 2)

            if (payment > 0):
                yield adate, fdate, payment, interest_charge, balance, is_extra

            payment_number += 1


def summary(mortgage):
    total_pay, total_interest = 0, 0
    for _, _, payment, interest_charge, _, _ in mortgage.repayments_schedule():
        total_pay += payment
        total_interest += interest_charge
    return round(total_pay, 2), round(total_interest,2)


price = 3300000
rate = 8
duration = 60
prepay = round(price * 0.2, 2)
credited = round(price - prepay, 2)
parents_month_payment = 50000
my_month_payment = 25000
my_month_extra_payment_start_date = date(2025, 12, 1)  # auto credit finish
my_month_extra_payment = 0

m = Mortgage(date(2024, 11, 1), credited, rate, duration)

my_balance = 0.00
num = 0
total_pay = 0
total_pay_to_bank = 0
for adate, fdate, payment, interest_charge, balance, is_extra in m.repayments_schedule():
    if not is_extra:
        my_balance += parents_month_payment # from parents
        my_balance += my_month_payment # from me

        if adate >= my_month_extra_payment_start_date:
            my_balance += my_month_extra_payment  # from me after close auto credit
        my_balance -= payment
        num += 1
    print(('+' if is_extra else ' ') +
          f'{adate},'
          f' {str(payment).ljust(8, " ")},'
          f' (%: {str(interest_charge).ljust(8, " ")}),'
          f' debt: {str(balance).ljust(8, " ")},'
          f' extra={str(round(my_balance, 2)).ljust(8, " ")},'
          f' {num=}',
          sep='\t')
    total_pay += payment
    total_pay_to_bank += interest_charge
    if num % 3 == 0 and my_balance > 0:
         m.add_extra_payment(adate, my_balance)
         my_balance = 0
print(f'{price=}, {prepay=}, {credited=}')
print(f'{rate=}, {duration=}')
print(f'parents_month_payment={round(parents_month_payment, 2)}')
print(f'my_month_payment={round(my_month_payment, 2)}')
print(f'my_month_extra_payment={round(my_month_extra_payment, 2)}')
print(f'total_pay={round(total_pay, 2)}')
print(f'overpay={round(total_pay - credited, 2)}')
print(f'total_pay_to_bank={round(total_pay_to_bank, 2)}')
print(f'num of months={num} ({num // 12.0} years and {num % 12})')



# m = Mortgage(date(2018,8,25), 3211032, 9.56, 240)
#
# for adate, fdate, payment, interest_charge, balance, is_extra in m.repayments_schedule():
#     print(adate, fdate, str(payment).ljust(8, ' '), str(interest_charge).ljust(8, ' '), str(balance).ljust(8, ' '), is_extra, sep='\t')

# print(summary(m))
