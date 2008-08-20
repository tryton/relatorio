from cStringIO import StringIO
from common import Invoice, repos, inv

repos.add_report(Invoice, 'image/png', 'pie_chart', report_name='pie')
repos.add_report(Invoice, 'image/png', 'vbar_chart', report_name='vbar')
repos.add_report(Invoice, 'image/png', 'hbar_chart', report_name='hbar')
repos.add_report(Invoice, 'image/png', 'line_chart', report_name='line')

#Image
pie_report, _ = repos.reports[Invoice]['pie']
file('pie.png', 'w').write(pie_report(inv).render().getvalue())
hbar_report, _ = repos.reports[Invoice]['hbar']
file('hbar.png', 'w').write(hbar_report(inv).render().getvalue())
vbar_report, _ = repos.reports[Invoice]['vbar']
file('vbar.png', 'w').write(vbar_report(inv).render().getvalue())
line_report, _ = repos.reports[Invoice]['line']
file('line.png', 'w').write(line_report(inv).render().getvalue())
