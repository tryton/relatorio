from cStringIO import StringIO
from common import Invoice, repos, inv

repos.add_report(Invoice, 'application/pdf', 'basic.tex',
                 report_name='ConTeXt')
#PDF
pdf_report, _ = repos.reports[Invoice]['ConTeXt']
file('bonham_basic.pdf', 'w').write(pdf_report(inv).render().getvalue())

