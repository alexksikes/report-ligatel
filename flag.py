#!/usr/bin/env python

# Author: Alex Ksikes

import cgi
import cgitb; cgitb.enable()

#print 'Content-type: text/html'
#print 
#print '''
#<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
#<html>
#<head>
#<meta http-equiv="content-type" content="text/html; charset=UTF-8">
#</head>
#<body>
#hey
#</body>
#'''

print "Content-type: text/html\n\n";


print "<html><body><h1>hello, this is a python script!</h1><br></body></html>";


#
#
#
#import time
#
#from report import db_select
#def flag(id, country):
#    q = "update tbl_invoice set status='%s' where id='%s'" % id
##    db_select([country]).execute(q)
#    time.sleep(10)
#
#form = cgi.FieldStorage()
#(id, country) = form.getvalue('id', ''), form.getvalue('country', '')
#flag(id, country)
