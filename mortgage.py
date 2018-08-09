from datetime import date
from calendar import monthrange


class Mortgage(object):
    def __init__(self, total, rate, duration, start_date):
        self.total = total
        self.rate = rate
        self.duration = duration
        self.start_date = start_date
        self.data = {}
        
    def recalculate(self):
        on_date = self.start_date
        info = self.data.setdefault(on_date, {})
        info['upb'] = self.total # unpaid principal balance
        info['interest_charges'] = 0.0
        info['mpr'] = 0.0 # monthly principal repayment
        info['epr'] = 0.0 # early partial repayment (extra repayments)
        
        for n in range(self.duration):
            prev_date = on_date
            year = prev_date.year + (0 if prev_date.month < 12 else 1)
            month = ((prev_date.month + 1) % 12) or 12
            on_date = date(year,
                           month,
                           min(prev_date.day, monthrange(year, month)[1]))
            info = self.data.setdefault(on_date, {})
            prev_info = self.data[prev_date]
            
            
            if prev_info['mpr'] and not prev_info.get('epr', None):
                info['mpr'] = prev_info['mpr']
            else:
                month_rate = self.rate / 100 / 12 # 12 - months in year, 100 - % 
                repayments_left = self.duration - n
                info['mpr'] = round(prev_info['upb'] * month_rate / (1 - (1 + month_rate)**(-repayments_left)), 2)
                
            days_in_year = (date(on_date.year + 1, 1, 1) - date(on_date.year, 1, 1)).days
            days_in_prev_year = days_in_year if on_date.year == prev_date.year \
                                else (date(prev_date.year + 1, 1, 1) - date(prev_date.year, 1, 1)).days
            if days_in_year == days_in_prev_year:
                days_rate = self.rate * (on_date - prev_date).days / (days_in_year * 100)
            else:
                days_rate = (date(prev_date.year, 12, 31) - prev_date).days / days_in_prev_year
                days_rate += ((on_date - date(on_date.year, 1, 1)).days + 1) / days_in_year
                days_rate = self.rate * days_rate / 100
                
            info['interest_charges'] = round(prev_info['upb'] * days_rate, 2)
            info['upb'] = round(prev_info['upb'] + info['interest_charges'] - info['mpr'], 2)
            if info['upb'] <= 300:
                info['mpr'] = round(info['mpr'] + info['upb'], 2)
                info['upb'] = 0
    
    def add_prepayment(self, prepayment_date, amount, prepayment_type):
        raise NotImplementedError
    
