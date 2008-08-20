import operator
from cStringIO import StringIO
import relatorio

class Invoice(dict):

    @property
    def total(self):
        return sum(l['amount'] for l in self['lines'])

    @property
    def vat(self):
        return self.total * 0.21


repos = relatorio.ReportRepository()
repos.add_report(Invoice, 'application/vnd.oasis.opendocument.text',
                 'basic.odt', report_name='basic')
repos.add_report(Invoice, 'application/vnd.oasis.opendocument.text',
                 'invoice.odt', report_name='complicated')
repos.add_report(Invoice, 'application/vnd.oasis.opendocument.spreadsheet',
                 'pivot.ods', report_name='pivot')
repos.add_report(Invoice, 'application/vnd.oasis.opendocument.presentation',
                 'presentation.odp', report_name='presentation')
repos.add_report(Invoice, 'application/pdf', 'basic.tex',
                 report_name='ConTeXt')
repos.add_report(Invoice, 'image/png', 'pie_chart', report_name='pie')
repos.add_report(Invoice, 'image/png', 'vbar_chart', report_name='vbar')
repos.add_report(Invoice, 'image/png', 'hbar_chart', report_name='hbar')

inv = Invoice(customer={'name': 'John Bonham',
                        'address': {'street': 'Smirnov street',
                                    'zip': 1000,
                                    'city': 'Montreux'}},
              lines=[{'item': {'name': 'Vodka 70cl',
                               'reference': 'VDKA-001',
                               'price': 10.34},
                      'quantity': 7,
                      'amount': 7*10.34},
                     {'item': {'name': 'Cognac 70cl',
                               'reference': 'CGNC-067',
                               'price': 13.46},
                      'quantity': 12,
                      'amount': 12*13.46},
                     {'item': {'name': 'Sparkling water 25cl',
                               'reference': 'WATR-007',
                               'price': 4},
                      'quantity': 1,
                      'amount': 4},
                     {'item': {'name': 'Good customer',
                               'reference': 'BONM-001',
                               'price': -20},
                      'quantity': 1,
                      'amount': -20},
                    ],
              id='MZY-20080703',
              status='late',
              trombine=(file('bouteille.png', 'r'), 'image/png'))


# ODT
basic_report, _ = repos.reports[Invoice]['basic']
file('bonham_basic.odt', 'w').write(basic_report(inv).render().getvalue())
report, _ = repos.reports[Invoice]['complicated']
file('bonham_complicated.odt', 'w').write(report(inv).render().getvalue())

# ODS
ods_report, _ = repos.reports[Invoice]['pivot']
file('bonham_pivot.ods', 'w').write(ods_report(inv).render().getvalue())

# ODP
odp_report, _ = repos.reports[Invoice]['presentation']
file('bonham_presentation.odp', 'w').write(odp_report(inv).render().getvalue())

#PDF
#pdf_report, _ = repos.reports[Invoice]['ConTeXt']
#file('bonham_basic.pdf', 'w').write(pdf_report(inv).render().getvalue())

#Image
pie_report, _ = repos.reports[Invoice]['pie']
file('pie.png', 'w').write(pie_report(inv).render().getvalue())
hbar_report, _ = repos.reports[Invoice]['hbar']
file('hbar.png', 'w').write(hbar_report(inv).render().getvalue())
vbar_report, _ = repos.reports[Invoice]['vbar']
file('vbar.png', 'w').write(vbar_report(inv).render().getvalue())

