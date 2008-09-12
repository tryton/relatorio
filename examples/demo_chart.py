from cStringIO import StringIO
from common import Invoice, repos, inv

repos.add_report(Invoice, 'image/png', 'pie_chart', report_name='pie')
repos.add_report(Invoice, 'image/svg', 'vbar_chart', report_name='vbar')
repos.add_report(Invoice, 'image/svg', 'hbar_chart', report_name='hbar')
repos.add_report(Invoice, 'image/png', 'line_chart', report_name='line')

if __name__ == '__main__':
    pie_report, _ = repos.reports[Invoice]['pie']
    file('pie.png', 'wb').write(pie_report(o=inv).render().getvalue())
    hbar_report, _ = repos.reports[Invoice]['hbar']
    file('hbar.svg', 'wb').write(hbar_report(o=inv).render().getvalue())
    vbar_report, _ = repos.reports[Invoice]['vbar']
    file('vbar.svg', 'wb').write(vbar_report(o=inv).render().getvalue())
    line_report, _ = repos.reports[Invoice]['line']
    file('line.png', 'wb').write(line_report(o=inv).render().getvalue())
