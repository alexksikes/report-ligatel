#!/usr/bin/env python

# Author: Alex Ksikes

# TODO : 
# - show the totals at the top like a search engine (keep it also at the bottom)
# - print nothing if it's the very beginning only
# - don't show the export link when no results are found
# - don't show header when no results are found
# - time stamp
# - replace long agrument functions by a dict param
# - ordering of the sort by takne into account in the ui
# - auto complete off
# - customer and invoice id reverse (made a modification to have invoice first check this)
# - forbid using 1 as billing day

import cgi, urllib, os
import cgitb; cgitb.enable()
    
import datetime
def index():
    ### Get url variables ###
    (month, year, period, payment, status, mini_search, countries, exp, aggregate, sort, column) = get_input()
    
    ### Header ###
    header(exp)
    
    ### Log query ###
    log()
        
    ### Print the UI ###
    if not exp:
        ui(month, year, period, payment, status, mini_search, countries, aggregate, sort, column)
    
    ### Get the results ###
    get_results(month, year, period, payment, status, mini_search, countries, exp, aggregate, sort, column)
    if not exp:
        print '</body></html>'

def header(exp):
    if exp:
        print 'Content-disposition: attachment; filename=report.csv'
        print
        return
    else:
        print 'Content-type: text/html'
    
    print '''
    <!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
    <html>
    <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">'''

    ### Calendar ###
    print '''
    <!-- calendar stylesheet -->
    <link rel="stylesheet" type="text/css" media="all" href="/reportcgi/calendar.css" />
    
    <!-- main calendar program -->
    <script type="text/javascript" src="/reportcgi/calendar.js"></script>'''
    
    ### Custom javascript ###
    print '''
    <!-- custom javascript -->
    <script type="text/javascript" src="/reportcgi/dynamic.js"></script>'''
      
    print '''
    <title>Ligatel Financial Report</title></head>
    <body>
    <h3><a href='reportcgi.py' style="text-decoration: none; color: black;">Ligatel Financial Report</a>
    <span style="font-size: 12;">( <a href='reportcgi.py'>reset</a> )
    ( <a href='/reportcgi/logs/search_log'>logs</a> )
    ( <a href=''>flag paid/unpaid</a> )
    </span>
    </h3>'''
    
def ui(month, year, period, payment, status, mini_search, countries, aggregate, sort, column):
    print "<form method='get' action='reportcgi.py'>"
    
    #### Filter by keywords ###
    print '''
    <p>
    <strong>Keywords : </strong><input type='text' name='keywords' value='%s' size='40'/>''' % ' '.join(mini_search)
    
    ### Calendar ###
    print ''' | 
    <strong>From</strong> (d/m/yyyy) : <input type="text" name="from_date" id="from_date" value="%s"/>
    <strong>Till</strong> (d/m/yyyy) : <input type="text" name="to_date" id="to_date" value="%s"/>
    ''' % (period and period[0] or '', 
           period and period[1] or '')
    
    print '''
    <input type='submit' value='Submit' size='45'/>
    </p>
    '''
    
    #### DB choice ###
    print '''
    <p>
    <input type='checkbox' name='countries' value='columbia' %s/>Columbia 
    <input type='checkbox' name='countries' value='brazil' %s/>Brazil 
    <input type='checkbox' name='countries' value='honduras' %s/>Honduras 
    ''' % ('columbia' in countries and 'checked' or '', 
           'brazil' in countries and 'checked' or '', 
           'honduras' in countries and 'checked' or '')
    
    #### Payment choice ###
    print '''
     |
    <input type='radio' name='payment' value='' %s/> All Payments 
    <input type='radio' name='payment' value='credit card' %s/> Credit Cards Only 
    <input type='radio' name='payment' value='cash transaction' %s/> Cash Only
    <input type='radio' name='payment' value='bradesco' %s/> Bradesco
    ''' % (payment == '' and 'checked' or '', 
           payment == 'credit card' and 'checked' or '', 
           payment == 'cash transaction' and 'checked' or '',
           payment == 'bradesco' and 'checked' or '')
    
    #### Paid | Due choice ###
    print '''
     |
    <input type='radio' name='status' value='' %s/> Paid and Due
    <input type='radio' name='status' value='paid' %s/> Paid
    <input type='radio' name='status' value='due' %s/> Due
    <input type='radio' name='status' value='over due' %s/> Over Due
    </p>''' % (status == '' and 'checked' or '', 
               status == 'paid' and 'checked' or '', 
               status == 'due' and 'checked' or '', 
               status == 'over due' and 'checked' or '')
    
    #### Aggregate choice ###
    print '<p><strong>Aggregate by : </strong>'
    for a_f in ('customer, place, country, reseller, did, plan_name, status, invoice_status, transaction_type').split(', '):
        print "<input type='checkbox' name='aggregate' value='%s' %s/>%s" \
                % (a_f, a_f in aggregate and 'checked' or '', a_f.replace('_',' ').capitalize())
    print " | <input type='checkbox' name='aggregate' value='date' %s/>Date (by month)" \
            % ('date' in aggregate and 'checked' or '')
    print '</p>'
#    print '''
#    </p><div style="font-size: 12; color:red;">
#    (aggregated data sorted by total amount)</div>'''
    ### Set calendar up ###
    setup_calendar()
    
    #### Export link ###
    print '''
    <a href='reportcgi.py?%s&export=yes'><strong>Export in csv</strong></a>''' \
    % urllib.urlencode(cgi.FormContentDict(), True)
    
    #### Pretty print ###
    print ''' | 
    <a href=''><strong>Generate Printed Invoices (One PDF)</strong></a>'''
    
    #### Tuning options ###
    print '''
    <a href="javascript:toggle('tuning')"><strong>More Tuning</strong></a>
    <div id="tuning" style="display: none;">'''
    
    ### Sort By ###
    s_f = 'date, customer, invoice_id, place, country, reseller, did, plan_name, status, invoice_status, transaction_type'
    print '<p><strong>Sort by : </strong>'
    for f in s_f.split(', '):
        print "<input type='checkbox' name='sort' value='%s' %s/>%s" \
                % (f, f in sort and 'checked' or '', f.replace('_',' ').capitalize())
    print '</p>'
    
    ### Show only ###
    print '<p><strong>Show only : </strong>'
    for f in s_f.split(', '):
        print "<input type='checkbox' name='column' value='%s' %s/>%s" \
                % (f, f in column and 'checked' or '', f.replace('_',' ').capitalize())
    print '</p>'
    
    ### Billing day selection ###
    print '''
    <p style="margin-bottom :0px;">
    <strong>Cash Invoices Billing Day : </strong> '''
    for country in ('columbia, brazil, honduras').split(', '):
        if country != 'columbia':
            print ' | '
        print '%s : <select name="billing_day_%s">' % (country.capitalize(), country)
        for day in range(29)[2:]:
            checked = ''
            if day == 28:
                checked = 'selected="selected"'
            print '<option value="%s" %s>%s</option>' % (day, checked, day)
        print '</select>'
    print '''
    <div style="font-size: 12; color:red;">
    (from beginning of day of the month till end of day - 1 of the next month)</div>'''
    print '</p></div></form>'
    
def setup_calendar():
    print '''
    <script type="text/javascript">
    Calendar.setup({
        inputField     :    "from_date",
        ifFormat       :    "%d/%m/%Y",
        align          :    "Bc"
    });
    Calendar.setup({
        inputField     :    "to_date",
        ifFormat       :    "%d/%m/%Y",
        align          :    "Bc"
    });
    </script>'''

# get form inputs    
def get_input():
    form = cgi.FieldStorage()
    keywords = form.getvalue('keywords', '')
    if keywords:
        mini_search = keywords.split(' ')
    else:
        mini_search = []
    
    month = form.getvalue('month', '')
    year = form.getvalue('year', '')
    
    payment = form.getvalue('payment', '')
    status = form.getvalue('status', '')
    
    period = (form.getvalue('from_date', ''), form.getvalue('to_date', ''))
    if period == ('', ''):
        period = None
    
    countries = form.getvalue('countries', ['columbia'])
    if not isinstance(countries, list):
        countries = [countries]
    
    exp = form.getvalue('export', '')
    
    aggregate = form.getvalue('aggregate', [])
    if not isinstance(aggregate, list):
        aggregate = [aggregate]
    
    sort = form.getvalue('sort', [])
    if not isinstance(sort, list):
        sort = [sort]
    
    column = form.getvalue('column', [])
    if not isinstance(column, list):
        column = [column]
    
    return (month, year, period, payment, status, mini_search, countries, exp, aggregate, sort, column)

import report    
def get_results(month, year, period, payment, status, mini_search, countries, exp, aggregate, sort, column):
    # assumes all invoices are chosen
    if not period and (mini_search or payment or status):
        today = datetime.datetime.now()
        lday = {'year':2005, 'month':01, 'day':01}
        period = ['%s/%s/%s' % (lday['day'], lday['month'], lday['year']), 
                  '%s/%s/%s' % (today.day, today.month, today.year)]
    
    # don't print anything if nothting is selected    
    if not (mini_search or period or payment or status):
        period, month, year = None, 01, 2003
    
    # if we are exporting in csv
    csv, html = False, True
    if exp:
        csv, html = True, False
    
    # some fixes
    payment = payment != '' and [payment] or []
    status = status != '' and [status] or []
    
    # we always show the amounts and make sure the column are in order
    if column:
        col = []
        fields = ['customer', 'invoice_id', 'place', 'country', 'reseller', 'did', 
                  'plan_name', 'date', 'date_monthly',
                  'total_amount', 'total_amount_monthly', 'equip', 'shipping_charges', 'activation_charges', 
                  'plan', 'callcost', 'callcost_monthly',
                  'status', 'invoice_status', 'transaction_type']
        for f in fields:
            if f in column:
                col.append(f)
            elif f in ['total_amount', 'total_amount_monthly', 
                     'equip', 'shipping_charges', 'activation_charges', 
                     'plan', 'callcost', 'callcost_monthly']:
                col.append(f)
        column = col
        
    # print the report
    report.list_invoices(month, year, period=period, total=True, header=True, 
                         csv=csv, html=html, payment=payment, status=status, 
                         emails=None, mini_search=mini_search, countries=countries, 
                         aggregate=aggregate, sort=sort, column=column)

import datetime
def log():
    root = '/var/www/internal.ligatel.com/reportcgi/logs/'
    ip = cgi.escape(os.environ["REMOTE_ADDR"])
    time = (datetime.datetime.today() - datetime.timedelta(0,0,0,0,0,7,0)).ctime()
    queries = '\t'.join(map(str, cgi.FormContentDict().values()))
    logs = '%s\t%s\t%s\n' % (ip, time, queries)
    #logs += '\t( <a href="reportcgi.py?%s">link</a> )\n' \
    #         % urllib.urlencode(cgi.FormContentDict(), True)
    if queries:
        open(os.path.join(root, 'search_log'), 'a').write(logs)
    
### Not used    
def make_csv_filename(month, year, period):
    rname = str(month) + '-' + str(year)
    if period:
        rname = period[0].replace('/', '-') + '.' + period[1].replace('/', '-')
    return rname + '.csv'

index()
