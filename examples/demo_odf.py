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
repos.add_report(None, 'application/vnd.oasis.opendocument.text',
                 'columns.odt', report_name='column')

if __name__ == '__main__':
    # Add a chart to the invoice
    inv['chart'] = repos.classes[Invoice].ids['pie']

    # ODT
    print "generating output_basic.odt... ",
    basic_report, _ = repos.classes[Invoice].ids['basic']
    data = basic_report(o=inv).render().getvalue()
    file('output_basic.odt', 'wb').write(data)
    print "done"

    print "generating output_complicated.odt... ",
    report, _ = repos.classes[Invoice].ids['complicated']
    data = report(o=inv).render().getvalue()
    file('output_complicated.odt', 'wb').write(data)
    print "done"

    print "generating output_columns.odt... ",
    column_report, _ = repos.classes[None].ids['column']
    lst = [[], ['i'], ['a', 'b'], [1, 2, 3], ['I', 'II', 'III', 'IV']]
    titles = ['first', 'second', 'third', 'fourth']
    data = column_report(titles=titles, lst=lst).render().getvalue()
    file('output_columns.odt', 'wb').write(data)
    print "done"

    # ODS
    print "generating output_pivot.ods... ",
    ods_report, _ = repos.classes[Invoice].ids['pivot']
    data = ods_report(o=inv).render().getvalue()
    file('output_pivot.ods', 'wb').write(data)
    print "done"

    # ODP
    print "generating output_presentation.odp... ",
    odp_report, _ = repos.classes[Invoice].ids['presentation']
    data = odp_report(o=inv).render().getvalue()
    file('output_presentation.odp', 'wb').write(data)
    print "done"

