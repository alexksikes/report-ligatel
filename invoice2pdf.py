# Here is the approach we use:
# We first we convert the invoice details to html using a template
# We then convert the html into a pdf using html2pdf
# The invoice pdf is then added to a single pdf
# We repeat for each invoice and then write the final pdf once
# It requires html2pdf.pl and pyPdf

import pyPdf, stringIO

class invoicePdf:
    template = {'columbia' : ''}
    tpl_fields = ['invoice_id', 'customer']
    logo = {'columbia' : ''}
    
    def __init__(self, country):
        self.pdf = ''
        
    def add(self, invoice):
        self.__add_to_pdf(
            self.__html_to_pdf(
                self.__invoice_to_html(invoice)))
    
    def write(self):
        pass
        
    def __invoice_to_html(self, invoice):
        # each country uses a different logo and template
        country = invoice['country']
        tpl, lg = template[country], logo[country]
        s = open(tpl).read()
        for f in tpl_fields:
            s += s.replace('@@@%s@@@' % f, invoice[f])
        return s
        
    def __html_to_pdf(self):
        pass
        
    def __add_to_pdf(self):
        pass

# Wraps html2pdf.pl using temporary files
class html2pdf:
    def __init__(self):
        pass

def run(invoice_details):
    invoice_pdf().add(invoice_details).write()

import sys
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: python invoice_to_pdf.py customer_name, address, ..."
        print
        print "Descriptions:"
        print "Make a single invoice as a pdf"
    else:
        run(sys.argv[1:])
