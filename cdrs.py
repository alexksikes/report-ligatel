# Author: Alex Ksikes

from report import db_select
def run(countries, from_phone, to_phone, sep=','):
    q = '''select
        tbl_dids.did as from_phone,
        cdr.destination as to_phone,
        cdr.*
        
        from cdr 
        
        left join tbl_dids on tbl_dids.cplan_id = round(substring(cdr.sipaccount,3,8))
        
        where tbl_dids.did like '%%%s%%' and destination like '%%%s%%';''' %\
        (from_phone, to_phone)
    
    cursors, once = db_select(countries), True
    for i, cursor in enumerate(cursors):
        cursor.execute(q)
        for row in cursor:
            if once:
                print 'country' + sep + sep.join(map(format_name, row.keys()))
                once = False
            print countries[i] + sep + sep.join(map(format_name, row.values()))
        cursor.close()

import re
def format_name(st):
    return re.sub('[,\t]', ' ', str(st))

import sys
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: python cdrs country,...,country phone_from phone_to"
        print
        print "Example: python cdrs columbia,brazil 949 800"
    else:
        run(sys.argv[1].split(','), sys.argv[2], sys.argv[3], sep='\t')