from os.path import abspath, join, dirname
from relatorio import Report

# test data
from common import inv

ODT_MIME = 'application/vnd.oasis.opendocument.text'
ODS_MIME = 'application/vnd.oasis.opendocument.spreadsheet'
ODP_MIME = 'application/vnd.oasis.opendocument.presentation'

if __name__ == '__main__':
    # ODT
    print "generating output_basic.odt... ",
    report = Report(abspath(join(dirname(__file__), 'basic.odt')), ODT_MIME)
    content = report(o=inv).render().getvalue()
    file(join(dirname(__file__), 'output_basic.odt'), 'wb').write(content)
    print "done"

    # we could also use an opendocument template directly
#    from relatorio.templates import opendocument
#    template = opendocument.Template(source=None, filepath='basic.odt')
#    content = template.generate(o=inv).render().getvalue()
#    file('output_basic.odt', 'wb').write(content)

    print "generating output_complicated.odt... ",
    # Add a chart to the invoice
    inv['chart'] = (Report(abspath(join(dirname(__file__), 'pie_chart')),
        'image/png'), 'image/png')
    report = Report(abspath(join(dirname(__file__), 'complicated.odt')),
            ODT_MIME)
    content = report(o=inv).render().getvalue()
    file(join(dirname(__file__), 'output_complicated.odt'), 'wb').write(content)
    print "done"

    print "generating output_columns.odt... ",
    report = Report(abspath(join(dirname(__file__), 'columns.odt')), ODT_MIME)
    lst = [[], ['i'], ['a', 'b'], [1, 2, 3], ['I', 'II', 'III', 'IV']]
    titles = ['first', 'second', 'third', 'fourth']
    content = report(titles=titles, lst=lst).render().getvalue()
    file(join(dirname(__file__), 'output_columns.odt'), 'wb').write(content)
    print "done"

    # ODS
    print "generating output_pivot.ods... ",
    report = Report(abspath(join(dirname(__file__), 'pivot.ods')), ODS_MIME)
    content = report(o=inv).render().getvalue()
    file(join(dirname(__file__), 'output_pivot.ods'), 'wb').write(content)
    print "done"

    print "generating output_sheets.ods... ",
    report = Report(abspath(join(dirname(__file__), 'demo_sheets.ods')),
            ODS_MIME)
    content = report(lst=lst).render().getvalue()
    file(join(dirname(__file__), 'output_sheets.ods'), 'wb').write(content)
    print "done"

    # ODP
    print "generating output_presentation.odp... ",
    report = Report(abspath(join(dirname(__file__), 'presentation.odp')),
            ODP_MIME)
    content = report(o=inv).render().getvalue()
    file(join(dirname(__file__), 'output_presentation.odp'), 'wb').write(content)
    print "done"

