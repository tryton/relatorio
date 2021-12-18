
from os.path import abspath, dirname, join

# test data
from common import inv

from relatorio import Report

# PDF
if __name__ == '__main__':
    print("generating output_basic.pdf... ", end='')
    report = Report(abspath(join(dirname(__file__), 'basic.tex')),
        'application/pdf')
    content = report(o=inv).render().getvalue()
    open(join(dirname(__file__), 'output_basic.pdf'), 'wb').write(content)
    print("done")
