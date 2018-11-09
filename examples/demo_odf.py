from __future__ import print_function
from os.path import abspath, join, dirname
from relatorio import Report
from relatorio.templates import opendocument

# test data
from common import inv

ODT_MIME = 'application/vnd.oasis.opendocument.text'
ODS_MIME = 'application/vnd.oasis.opendocument.spreadsheet'
ODP_MIME = 'application/vnd.oasis.opendocument.presentation'

if __name__ == '__main__':
    pwd = dirname(__file__)
    # ODT
    print("generating output_basic.odt... ", end='')
    report = Report(abspath(join(dirname(__file__), 'basic.odt')), ODT_MIME)
    content = report(o=inv).render().getvalue()
    open(join(pwd, 'output_basic.odt'), 'wb').write(content)
    print("done")

    # we could also use an opendocument template directly
    print("generating output_template_basic.odt... ", end='')
    template = opendocument.Template(source='',
        filepath=abspath(join(pwd, 'basic.odt')))
    content = template.generate(o=inv).render().getvalue()
    open(join(pwd, 'output_template_basic.odt'), 'wb').write(content)
    print("done")

    print("generating output_complicated.odt... ", end='')
    # Add a chart to the invoice
    inv['chart'] = (
        Report(abspath(join(pwd, 'pie_chart')), 'image/png'), 'image/png')
    report = Report(abspath(join(pwd, 'complicated.odt')), ODT_MIME)
    try:
        content = report(o=inv).render().getvalue()
    except NotImplementedError:
        print("skipped")
    else:
        open(join(pwd, 'output_complicated.odt'), 'wb').write(content)
        print("done")

    print("generating output_columns.odt... ", end='')
    report = Report(abspath(join(pwd, 'columns.odt')), ODT_MIME)
    lst = [[], ['i'], ['a', 'b'], [1, 2, 3], ['I', 'II', 'III', 'IV']]
    titles = ['first', 'second', 'third', 'fourth']
    content = report(titles=titles, lst=lst).render().getvalue()
    open(join(pwd, 'output_columns.odt'), 'wb').write(content)
    print("done")

    # ODS
    print("generating output_pivot.ods... ", end='')
    report = Report(abspath(join(pwd, 'pivot.ods')), ODS_MIME)
    content = report(o=inv).render().getvalue()
    open(join(pwd, 'output_pivot.ods'), 'wb').write(content)
    print("done")

    print("generating output_sheets.ods... ", end='')
    report = Report(abspath(join(pwd, 'demo_sheets.ods')), ODS_MIME)
    content = report(lst=lst).render().getvalue()
    open(join(pwd, 'output_sheets.ods'), 'wb').write(content)
    print("done")

    # ODP
    print("generating output_presentation.odp... ", end='')
    report = Report(abspath(join(pwd, 'presentation.odp')), ODP_MIME)
    content = report(o=inv).render().getvalue()
    open(join(pwd, 'output_presentation.odp'), 'wb').write(content)
    print("done")

    # Big document
    print("generating output_big.odt... ", end='')
    report = Report(abspath(join(pwd, 'big.odt')), ODT_MIME)
    content = report().render(out=open(join(pwd, 'output_big.odt'), 'wb'))
    print("done")
