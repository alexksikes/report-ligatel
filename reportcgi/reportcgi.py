#!/usr/bin/env python

# Author: Alex Ksikes

import cgi, urllib
import cgitb; cgitb.enable()
    
import datetime
def index():
    ### Get url variables ###
    (month, year, period, payment, status, mini_search, countries, exp) = get_input()
    
    ### Header ###
    header(exp)
        
    ### Print the UI ###
    if not exp:
        ui(month, year, period, payment, status, mini_search, countries)
    
    ### Get the results ###
    get_results(month, year, period, payment, status, mini_search, countries, exp)
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
      
    print '''
    <title>Ligatel Financial Report</title></head>
    <body>
    <h3>Ligatel Financial Report</h3>'''
    
def ui(month, year, period, payment, status, mini_search, countries):
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
    <input type='checkbox' name='countries' value='honduras' unchecked/>Honduras 
    ''' % ('columbia' in countries and 'checked' or '', 
           'brazil' in countries and 'checked' or '') 
    #       'honduras' in countries and 'checked' or '')
    
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
    
    print '</form>'
    
    ### Set calendar up ###
    setup_calendar()
    
    #### Export link ###
    print '''<p><a href='reportcgi.py?%s&export=yes'><strong>Export in csv</strong></a></p>''' \
    % urllib.urlencode(cgi.FormContentDict(), True)
    
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
        try: 
            countries.remove('honduras')
        except:
            pass
    
    exp = form.getvalue('export', '')
    
    return (month, year, period, payment, status, mini_search, countries, exp)
  
import report    
def get_results(month, year, period, payment, status, mini_search, countries, exp):
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
    
    # print the report
    report.list_invoices(month, year, period=period, total=True, header=True, 
                         csv=csv, html=html, payment=payment, status=status, 
                         emails=None, mini_search=mini_search, countries=countries)

### Not used    
def make_csv_filename(month, year, period):
    rname = str(month) + '-' + str(year)
    if period:
        rname = period[0].replace('/', '-') + '.' + period[1].replace('/', '-')
    return rname + '.csv'

index()
