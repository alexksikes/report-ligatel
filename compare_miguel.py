# Author: Alex Ksikes

# Conclusions:
# sometimes miguel has a different transaction type
# sometimes auto has a 'none' transaction type
# it seems a lot invoices (140) are missing from miguel
# these invoices usually have field values missing such transaction type
# since there was no actual transaction
# paid due different maybe because auto report is more up to date

def load(f):
    tbl = {}
    for l in open(f):
        r = l.split('\t')
        id, amounts, paid_due = r[1], r[7:13], r[13]
        try:
            id = int(id)
        except:
            print "WARNING skipping line: %s\t" % l
            continue
        tbl[id] = {'line':l, 'amounts':map(float, amounts), 'paid_due':paid_due.strip().lower()}
    return tbl

import sets
def run(miguel, auto):
    mi, au = load(miguel), load(auto)
    for i in sets.Set(au.keys()) and sets.Set(mi.keys()):
        print "COMMON-MIGUEL-" + str(i) + "\t" + mi[i]['line'],
        print "COMMON-AUTOMATIC-" + str(i) + "\t" + au[i]['line'],
    for i in sets.Set(au.keys()) - sets.Set(mi.keys()):
        print "MISSING-MIGUEL-" + str(i) + "\t" + au[i]['line'],
    for i in sets.Set(mi.keys()) - sets.Set(au.keys()):
        print "MISSING-AUTOMATIC-" + str(i) + "\t" + mi[i]['line'],
    for i in sets.Set(au.keys()) and sets.Set(mi.keys()):
        if len(sets.Set(au[i]['amounts']) - sets.Set(mi[i]['amounts'])):
            print "AMOUNTS-MIGUEL-" + str(i) + "\t" + mi[i]['line'],
            print "AMOUNTS-AUTOMATIC-" + str(i) + "\t" + au[i]['line'],
    for i in sets.Set(au.keys()) and sets.Set(mi.keys()):
        if len(sets.Set(au[i]['paid_due']) - sets.Set(mi[i]['paid_due'])):
            print "PAID-DUE-MIGUEL-" + str(i) + "\t" + mi[i]['line'],
            print "PAID-DUE-AUTOMATIC-" + str(i) + "\t" + au[i]['line'],
        
import sys
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: python compare_miguel.py mighel_report automatic_report"
        print
        print "Descriptions:"
        print "Compare the two reports."
    else:
        run(sys.argv[1], sys.argv[2])
