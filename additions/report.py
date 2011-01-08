# Author: Alex Ksikes

# egypt disconnects from sftp after more than 2 hours
# all open files get lost
# how is overdue determined?
# some payment types are NULL, what do we output?
# numbers don't add up!

# TODO:
# - scheduled, add to cron if not already specified
# - send html emails
# - cgi and script may interfere when creating files, also permissions would be different
# it would open an already existing file but with the wrong permission leading to an error on the cgi side
# - in html we could show number of results and totals at the top (like a search engine)
# - safari does not unchecks everything
# - better sort that does all fields (so print aggregate doe snot need to sort by total amount)
# - utf-8 support, check mysql stores it right
# - include email of customer
# - see if you can automatically send invoice thru customer email

import MySQLdb, os
from fix_cash_invoices import *

# helpper function
def get_mysql_period(start_date, period=None, date_field_name='tbl_invoice.invoice_date'):
    if not period:
        q = \
        '''where %s between '%s' and last_day('%s') + interval 1 day''' \
        % (date_field_name, start_date, start_date)
    else:
        (from_date, to_date) = period
        q = \
        "where %s between " % date_field_name + \
        "STR_TO_DATE('" + from_date + "', '%d/%m/%Y') and STR_TO_DATE('" + to_date + "', '%d/%m/%Y') + interval 1 day "
    return q

def get_invoice_details(cursor, start_date, period=None):
    # is item_amount for a single item, should we take into account item_qty?
    q = '''select 
    invoice_id, 
    item_type, 
    item_qty, 
    item_amount 
    from tbl_invoice_details 
    left join tbl_invoice using (invoice_id)'''
    
    q += get_mysql_period(start_date, period)
    
    cursor.execute(q)
    
    invoice_details = {}
    for result in cursor:
        invoice_id, item_qty = map(int, [result['invoice_id'], result['item_qty']]) 
        item_amount = float(result['item_amount'])
        item_type = result['item_type'].lower().strip()
        if not invoice_details.has_key(invoice_id):
            invoice_details[invoice_id] = {item_type: item_qty * item_amount}
        else:
            invoice_details[invoice_id][item_type] = item_qty * item_amount
    return invoice_details
    
def list_invoices(month, year, period=None, total=False, header=False, 
                  csv=False, html=False, payment=[], status=[], 
                  emails=None, mini_search=[], countries=['columbia'], 
                  aggregate=[], sort=[], column=[], billing_days={}):
    start_date = '%s-%s-01' % (year, month)
    
    q = '''select 
    concat_ws(' ', tbl_customer.first_name, tbl_customer.last_name) as customer, 
    tbl_invoice.invoice_id as invoice_id, 
    tbl_customer.city as place, 
    tbl_customer.email as email, 
    concat_ws(' ', tbl_reseller.first_name, tbl_reseller.last_name) as reseller, 
    tbl_dids.did as did, 
    tbl_plan.plan_name as plan_name, 
    date_format(tbl_invoice.invoice_date,'%d/%m/%y %H:%i:%s') as date, 
    tbl_invoice.invoice_date as date_s,
    tbl_invoice.amount as total_amount, 
    tbl_invoice.shipping_charges as shipping_charges,
    tbl_invoice.activation_charges as activation_charges, 
    tbl_customer_plans.plan_amount as monthly_fee, 
    tbl_customer_plans.cplan_id as plan_id,
    tbl_invoice.status as status, 
    tbl_invoice.invoice_status as invoice_status,
    payment_types.paymenttype_name as transaction_type
    
    from tbl_invoice 

    left join payment_types using (paymenttype_id) 
    left join tbl_customer using (customer_id) 
    left join tbl_reseller using (reseller_id) 
    left join tbl_customer_plans using (cplan_id) 
    left join tbl_plan on tbl_plan.plan_id = tbl_customer_plans.plan_id 
    left join tbl_dids using(cplan_id)'''
    
    # flexible date choice
    q += get_mysql_period(start_date, period)
    
    # sort by specific fields, can't do all fields but it's good for now
    if not sort:
        sort = ['date', 'customer', 'reseller', 'transaction_type']
    if 'date' in sort:
        sort[sort.index('date')] = 'date_s'
    q += ' order by ' + ', '.join(sort)
    
    # what is 'monthly_fee', ??
    fields = ['invoice_id', 'customer', 'email', 'place', 'country', 'reseller', 'did', 
              'plan_name', 'date', 'date_monthly',
              'total_amount', 'total_amount_monthly', 'equip', 'shipping_charges', 'activation_charges', 
              'plan', 'callcost', 'callcost_monthly',
              'status', 'invoice_status', 'transaction_type']
    totals, a_totals = {}, {}
    
    # separator choice
    sep = '\t'
    if csv:
        sep = ','
    
    # email option filename
    if emails or html:
        rname = str(month) + '-' + str(year)
        if html:
            rname = rname  + '.html'
        if period:
            (from_date, to_date) = period
            rname = from_date.replace('/', '-') + '.' + to_date.replace('/', '-')
        rname = os.path.join('/tmp/', rname)
        sys.stdout = open(rname, 'w')    # use tmp file instead
    
    once = header    # to print header info once (hacky)
    
    # for each database
    cursors = db_select(countries)
    
    for (i, cursor) in enumerate(cursors):
        # because of bad db design we put tbl_invoice_details in memory
        invoice_details = get_invoice_details(cursor, start_date, period)
        
        # fixing the cash invoices
        billing_day = billing_days.get(countries[i], 28) # defaults to 28
        cash_invoices = cashInvoices(cursor, start_date, period, invoice_details, billing_day)
        
        cursor.execute(q)
        # print header information if requested
        if header and cursor.rowcount > 0 and once:
            h = sep.join(format_name(f) for f in fields)
            if column:
               h = sep.join(format_name(c) for c in column)
            print h 
            once = False
        for result in cursor:
            # fix a bug skip empty dids
            if not result['did']:
                continue
            
            # filter by transaction type or status 
            # (we should rather check the payment_type type id!)
            # after looking at the table id 1 and 2 have the same payment type name
            # so it's better this way
            if payment:
                if not result['transaction_type'] or \
                    result['transaction_type'].lower().strip() not in payment:
                    continue
            if status:
                c = result['status'].strip().lower()
                if c == 'false' and 'due' not in status:
                    continue
                elif c == 'true' and 'paid' not in status:
                    continue
            
            # fix the cash invoices
            cash_invoices.fix(result)
            
            # if we aggregate by date range (right simply aggregate by month)
            if 'date' in aggregate:
                result['date'] = get_bin_date(result['date'])
            
            # print them all
            s, cells = "", {}
            for f in fields:
                # depending on field do some formatting
                if f in ['equip', 'plan', 'callcost']:
                    cell = invoice_details[int(result['invoice_id'])].get(f, 0.0)
                elif f in ['customer', 'reseller', 'place', 'plan']:
                    cell = format_name(result[f])
                elif f in ['email']:
                    cell = result[f].lower().strip()
                elif f == 'country':
                    cell = countries[i].capitalize()
                elif f == 'status':
                    cell = 'Due'
                    if str(result[f]).strip().lower() == 'true':
                        cell = 'Paid'
                else:
                    cell = result[f]
                # some formating (empty field, field with a ',')
                if cell == None:
                    cell = ''
                # used to compute totals and for search
                cells[f] = cell
                # some columns may not be displayed
                if column and f not in column:
                    continue
                s += re.sub('[,\t]', ' ', str(cell)) + sep
            # mini search
            if mini_search and not search(cells, mini_search):
                continue
            # compute totals
            if total:
                compute_totals(totals, cells)
            # compute aggregation    
            if aggregate:
                compute_aggregate(a_totals, aggregate, cells)
                continue
            print s[:-1]
        cursor.close()
    
    # output aggregated results
    if aggregate:
        print_aggregate(a_totals, fields, aggregate, sep, column)
    
    # ouput totals of requested
    if totals:
        print_totals(totals, fields, sep, html, column)
    
    sys.stdout = sys.__stdout__
    # html option
    if html:
        htmlize(rname, sep, header, total)
        if not emails:
            print open(rname).read()
    # email option
    if emails:
        send_mail(rname, emails)
        print 'Report %s emailed to %s.' % (os.path.basename(rname), ' '.join(emails))
    
    # clean up
    if emails or html:
        os.remove(rname)    # use tmp file instead
    
def compute_totals(totals, cells):
    for (f, cell) in cells.items():
        if f in ['total_amount', 'equip', 'shipping_charges', 
                 'activation_charges', 'plan', 'callcost', 
                 'callcost_monthly', 'total_amount_monthly']:
            cell = float(cell)
        elif f in ['did', 'invoice_id']:
            if not cell:
                continue
            cell = 1
        else:
            continue
        if totals.has_key(f):
            totals[f] += cell
        else:
            totals[f] = cell

# This function was added later
# We did not want to change the main structure of the program
# We could not use MySQL COUNT(DISTINCT expr1[,expr2,...,exprN]) or GROUP BY
def compute_aggregate(a_totals, a_fields, cells):
   k = tuple([cells[a_field] for a_field in a_fields])
   if not a_totals.has_key(k):
       a_totals[k] = {}
   compute_totals(a_totals[k], cells)

def num_date(str_date):
    s = str_date.split('/')
    s.reverse()
    return int(''.join(s))
    
# This is redundant but was added later
def print_aggregate(a_totals, fields, a_fields, sep, column):
    # sort by date or total amount
    if 'date' in a_fields:
        i = a_fields.index('date')
        keys = sorted(a_totals,
               cmp=lambda x, y: cmp(num_date(x[i]), num_date(y[i])))
    else:
        keys = sorted(a_totals, 
               cmp=lambda x, y: cmp(a_totals[x]['total_amount'], a_totals[y]['total_amount']),
               reverse=True)
    
    if column:
        fields = column
        
    for a_f in keys:
        s, cells = '', a_totals[a_f]
        for f in fields:
            if f in a_fields:
                s += str(a_f[a_fields.index(f)])
            elif f in ['total_amount', 'total_amount_monthly', 'equip', 'shipping_charges', 
                 'activation_charges', 'plan', 'callcost', 'callcost_monthly']:
                s += str(cells[f])
            s += sep
        print s[:-1]

def get_bin_date(str_date):
    d = str_date.split('/')
    return "%s/%s" % (d[1], d[2].split()[0])
    
def print_totals(totals, fields, sep, html=False, column=[]):
    s = ''
    if html:
        s += 'Totals '
        if column:
            fields = column
        for f in fields:
            if totals.has_key(f):
                s += str(totals[f])
            s += sep
        s = s[:-1]
    else:
        for f in fields:
            if totals.has_key(f):
                s += format_name(f) + sep + str(totals[f]) + '\n'
    print s,
    
import re
def format_name(n):
    return " ".join([s.capitalize() for s in re.split('[_\s]+', n.lower())])

def send_mail(filename, emails):
    subject = 'report ' + os.path.basename(filename)
    cmd = 'mutt -a %s -s "%s" %s < %s' % (filename, subject, ','.join(emails), filename)
    sys.stdout = sys.__stdout__
    os.system(cmd)

def search(cells, keywords):
    s = ' '.join(map(str, cells.values()))
    for k in keywords:
        if not re.search(k, s, re.I):
            return False
    return True

def htmlize(filename, sep, header=False, total=False):
    title = os.path.basename(filename).split('.')[0]
    s = \
    '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
    <html>
    <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <title>%s</title>
    </head>
    <body>
    <p><h1>Report : %s</h1></p>
    <p><table border=1>''' % (title, title)
    
    # have an informative html title (show options used)
    
    # for now we ignore the doctype and header
    lines = open(filename).readlines()
    
    # nothing to print
    if not lines:
        open(filename, 'w').write('')
        return
    
    s = '<p><table border=1 width="100%">'
    for l in lines[:-1]:
        if header:
            s += '\n<tr><th>%s</th></tr>' % l.replace(sep, '</th><th>')
            header = False
        else:
            s += '\n<tr><td>%s</td></tr>' % l.replace(sep, '</td><td>')
    if total:
        s += '\n<tr><td><strong>%s</strong></td></tr>' % lines[-1].replace(sep, '</strong></td><td><strong>')
    s += '\n</table></p>'
    open(filename, 'w').write(s)


host="rome.ligatel.com"
user_pass_db = {'columbia': ('user', 'passwd', 'db'),
                'brazil': ('user', 'passwd', 'db'),
                'honduras': ('user', 'passwd', 'db')}
def db_select(countries):
    cursors = []
    for country in countries:
        (user, passwd, db) = user_pass_db[country]
        cursors.append(MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)
                       .cursor(MySQLdb.cursors.DictCursor))
    return cursors

def usage():
    print "Usage: python report.py [options] month_num year"
    print
    print "Description:" 
    print "Monthly invoices report sorted by reseller, transaction type and dates."
    print
    print "Display Options:" 
    print "-p, --period [from_date,to_date] : flexible time period" 
    print "-t, --totals                     : output totals" 
    print "-e, --header                     : output header" 
    print "-c, --csv                        : csv output format for exel" 
    print "-l, --html                       : html output" 
    print "-h, --help                       : this help message"
    print
    print "Filter Options:" 
    print "--credit_cards : paid by credit cards only" 
    print "--cash         : paid by cash only"
    print "--bradesco     : paid by brandesco"
    print "--paid         : paid only" 
    print "--due          : due only" 
    print "--over_due     : over due invoices only" 
    print
    print "Database Options:" 
    print "--columbia (default) : invoices from Columbia" 
    print "--brazil             : invoices from Brazil"
    print "--honduras           : invoices from Honduras"
    print
    print "Exotic Options:" 
    print "-m, --email [email_1,...,email_n]     : email report"
    print "-s, --mini_search 'keywords'          : filter results by keywords"
    print "-a, --aggregate [field_1,...,field_n] : aggregate on certain fields"
    print "                                        (customer, place, reseller, did, plan_name,"
    print "                                        date (by month), status, invoice_status,"
    print "                                        transaction_type)"
    print "-b, --billing [country,day_num]       : the cash invoices are created manually"
    print "                                        specify a billing day for a specific country"
    print "                                        (eg day/01/2007 (included) --- day-1/02/2007 (included))"
    print "                                        default is 28"
    print "--sort [field_1,...,field_n]          : sort by date, customer, reseller ..."
    print "--column [field_1,...,field_n]        : show only certain columns"
    print
    print "Examples:"
    print "'1) python report.py 2 2007'"
    print "* List all invoices from 01/02/2007 till 31/02/2007"
    print "'2) python report.py -p 12/03/2006,17/05/2007'"
    print "* List all invoices from 12/03/2006 till 17/05/2007"
    print "'3) python report.py --email alex@ligatel.com,mighel@ligatel.com 2 2007"
    print "* Email invoices from 01/02/2007 till 31/02/2007 to mighel and alex"
    print
    print "Email bugs/suggestions to Alex Ksikes (alex.ksikes@gmail.com)" 
    
import sys, getopt
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "p:teclhm:s:a:b:", 
                        ["period=", "totals", "header", "csv", "html", "help",
                         "email=", "mini_search=", "aggregate=",
                         "billing=", "sort=", "column=",
                         "credit_cards", "cash", "bradesco", "paid", "due", "over_due",
                         "columbia", "brazil", "honduras"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    period = emails = mini_search = None
    total = csv = html = header = False
    payment, status, countries, aggregate, sort, column = [], [], [], [], [], []
    billing_days = {}
    
    for o, a in opts:
        if o in ("-p", "--period"):
            period = a.split(',')
            args.append(-1); args.append(-1) # hacky  
        if o in ("-t", "--totals"):
            total = True   
        if o in ("-e", "--header"):
            header = True   
        if o in ("-c", "--csv"):
            csv = True  
        if o in ("-l", "--html"):
            html = True  
        if o  == "--credit_cards":
            payment.append('credit card')
        if o  == "--cash":
            payment.append('cash transaction')  
        if o  == "--bradesco":
            payment.append('bradesco')  
        if o  == "--paid":
            status.append('paid')  
        if o  == "--due":
            status.append('due')  
        if o  == "--over_due":
            print "Not yet implented!"
            sys.exit()
        if o  == "--brazil":
            countries.append('brazil')  
        if o  == "--columbia":
            countries.append('columbia')  
        if o  == "--honduras":
            countries.append('honduras')  
        if o in ("-m", "--email"):
            emails = a.split(',')
        if o in ("-s", "--mini_search"):
            mini_search = re.split('\s+', a)
        if o in ("-a", "--aggregate"):
            aggregate = a.split(',')
        if o in ("-b", "--billing"):
            (country, billing_day) = a.split(',')
            billing_days[country] = int(billing_day)
        if o == "--sort":
            sort = a.split(',')
        if o == "--column":
            column = a.split(',')
        if o in ("-h", "--help"):
            usage()
            sys.exit()
    # columbia is default
    if not countries:
        countries = ['columbia']
    if len(args) < 2 and not period:
        usage()
    else:
        list_invoices(args[-2], args[-1], period, total, header, 
                      csv, html, payment, status, emails, mini_search, 
                      countries, aggregate, sort, column, billing_days)
            
if __name__ == '__main__':
    main()
