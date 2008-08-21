from cStringIO import StringIO
from common import Invoice, repos, inv
import demo_chart

repos.add_report(Invoice, 'application/vnd.oasis.opendocument.text',
                 'basic.odt', report_name='basic')
repos.add_report(Invoice, 'application/vnd.oasis.opendocument.text',
                 'invoice.odt', report_name='complicated')
repos.add_report(Invoice, 'application/vnd.oasis.opendocument.spreadsheet',
                 'pivot.ods', report_name='pivot')
repos.add_report(Invoice, 'application/vnd.oasis.opendocument.presentation',
                 'presentation.odp', report_name='presentation')

if __name__ == '__main__':
    # Add a chart to the invoice
    inv['chart'] = repos.reports[Invoice]['pie']

    # ODT
    basic_report, _ = repos.reports[Invoice]['basic']
    file('bonham_basic.odt', 'w').write(basic_report(o=inv).render().getvalue())
    report, _ = repos.reports[Invoice]['complicated']
    file('bonham_complicated.odt', 'w').write(report(o=inv).render().getvalue())

    # ODS
    ods_report, _ = repos.reports[Invoice]['pivot']
    file('bonham_pivot.ods', 'w').write(ods_report(o=inv).render().getvalue())

    # ODP
    odp_report, _ = repos.reports[Invoice]['presentation']
    file('bonham_presentation.odp', 'w').write(odp_report(o=inv).render().getvalue())
