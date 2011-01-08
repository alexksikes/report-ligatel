# Author: Alex Ksikes
###########################################################
### CRAP to handle the billing period for cash invoices ###
### This is the crap that makes the program slow        ###
###########################################################

# It seems the manually billing only takes into account the start date
# as featured by the voice engine
# So if a phone call is made accross mutiple billing cycles
# The client will only be charged from the start till the end of the 
# first billing cycle.
# Example: I make a phone call on the 27th
# The billing is done on the 28th of this month
# I hang up on the 30th of this month
# I would only get charged from the 27th till the 28th
# Some very expensive phone calls can be made this way
# Should I reproduce the mistake or should I take into account the end
# of the phone call instead of its start date?
# Note the client will never be charged if he never hangs up

# -add shipping charges !=0 in the heuristic

# SELECT start from cdr WHERE start BETWEEN '2007-01-28' AND DATE_ADD('2007-01-28', INTERVAL 1 MONTH) order by start asc
# SELECT start, DATE_ADD(start, INTERVAL billed_duration SECOND) as end from cdr

import datetime

class cashInvoices:
    def __init__(self, cursor, start_date, period, invoice_details, billing_day):
        self.billing_day = billing_day
        self.invoice_details = invoice_details
        self.first_invoice = {}
        self.get_call_costs_precise(cursor, start_date, period)
        
    def get_call_costs_precise(self, cursor, start_date, period):
        self.call_costs = {}
        for period in self.get_billing_cycle(start_date, period):
            start_date = period[0]
            from_date = '/'.join(map(str, [period[0].day, period[0].month, period[0].year]))
            to_date = '/'.join(map(str, [period[1].day, period[1].month, period[1].year]))
            
            q = '''select
            round(substring(sipaccount,3,8)) as plan_id, 
            start as date, 
            sum(call_charge_tenthousandths) as callcost
            from cdr '''
            
            q += \
            "where start between " + \
            "STR_TO_DATE('" + from_date + "', '%d/%m/%Y') and STR_TO_DATE('" + to_date + "', '%d/%m/%Y') + interval 1 day " + \
            "group by plan_id "
            
            cursor.execute(q)
            for r in cursor: 
                call_cost = float('%0.2f' % (r['callcost'] / 10000))
                plan_id = int(r['plan_id'])
                month = self.billing_month(start_date)
                self.call_costs[(plan_id, month)] = call_cost
        
    def get_billing_cycle(self, start_date, period=None):
        if not period:
            from_date = start_date.split('-')
            from_date.reverse()
            from_date = '/'.join(from_date)
        else:
            (from_date, to_date) = period
        
        from_date = map(int, from_date.split('/'))
        from_date = datetime.datetime(from_date[2], from_date[1], from_date[0])
        if not period:
        #    to_date = next_billing_date(from_date)
            to_date = self.next_billing_date(datetime.datetime(from_date.year, from_date.month, self.billing_day))
        else:
            to_date = map(int, to_date.split('/'))
            to_date = datetime.datetime(to_date[2], to_date[1], to_date[0])
    
        intervals = []
        next_date = self.next_billing_date(from_date)
        while next_date < to_date:
            intervals.append((from_date, next_date))
            from_date = datetime.datetime(next_date.year, next_date.month, next_date.day + 1)
            next_date = self.next_billing_date(from_date)
        intervals.append((from_date, to_date))
        return intervals

    def next_billing_date(self, date):
        if date.day > self.billing_day - 1:
            date = add_month(date)
        return datetime.datetime(date.year, date.month, self.billing_day - 1)
    
    def billing_month(self, date):
        date_n = self.next_billing_date(date)
        date_p = add_month(date_n, n=-1)
        return '%s/%s/%s - %s/%s/%s' % (self.billing_day, date_p.month, date_p.year,
                                        self.billing_day - 1, date_n.month, date_n.year)

    def fix(self, result):
        date = self. billing_month(result['date_s'])
        plan_id = result['plan_id']
        call_cost = self.call_costs.get((plan_id, date), 0)
        
        ### handle the first invoice bullshit
        invoice_id = int(result['invoice_id'])
        equip = self.invoice_details[invoice_id].get('equip', 0.0)
        shipping = result['shipping_charges']
        activation = result['activation_charges']
        # very weak heuristic but otherwise 
        # we have to go thru the entire cdr table and sort by date
        # an invoice is a first invoice if equip or activation cost != 0
        # note that it breaks if someone orders a new phone
        # Miguel says that it does not happen
        if activation != 0 or equip !=0:
            self.first_invoice[plan_id] = call_cost
            result['callcost_monthly'] = 0
        else:
            result['callcost_monthly'] = call_cost + self.first_invoice.get(plan_id, 0)
            self.first_invoice[plan_id]= 0
        result['date_monthly'] = date
        
        ### handle the recomputing of the total amount
        plan = self.invoice_details[invoice_id].get('plan', 0.0)
        result['total_amount_monthly'] = result['callcost_monthly'] + \
                                         equip + shipping + activation + plan
    
def add_month(date, n=1):
    OneDay = datetime.timedelta(days=1)
    # add n+1 months to date then subtract 1 day
    # to get eom, last day of target month
    q,r = divmod(date.month+n, 12)
    eom = datetime.date(date.year+q, r+1, 1) - OneDay
    if date.month != (date+OneDay).month or date.day >= eom.day:
        return eom
    return eom.replace(day=date.day)
                        
###########################################################
###                     END of CRAP                     ###
###########################################################
