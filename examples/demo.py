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
                               'price': 0.4},
                      'quantity': 1,
                      'amount': 0.4},
                     {'item': {'name': 'Good customer',
                               'reference': 'BONM-001',
                               'price': -20},
                      'quantity': 1,
                      'amount': -20},
                    ],
              id='MZY-20080703',
              status='late',
              trombine=(file('bouteille.png', 'r'), 'image/png'))


_, basic_report = repos.reports[Invoice]['basic']
file('bonham_basic.odt', 'w').write(basic_report(inv).render().getvalue())
_, report = repos.reports[Invoice]['complicated']
file('bonham_complicated.odt', 'w').write(report(inv).render().getvalue())

# ODS
_, ods_report = repos.reports[Invoice]['pivot']
file('bonham_pivot.ods', 'w').write(ods_report(inv).render().getvalue())
