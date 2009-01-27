from os.path import abspath
from relatorio import Report

# test data
from common import inv

#PDF
if __name__ == '__main__':
    print "generating output_basic.pdf... ",
    report = Report(abspath('basic.tex'), 'application/pdf')
    content = report(o=inv).render().getvalue()
    file('output_basic.pdf', 'wb').write(content)
    print "done"

