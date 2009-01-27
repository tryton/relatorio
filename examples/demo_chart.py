from os.path import abspath
from relatorio import Report

# test data
from common import inv

if __name__ == '__main__':
    pie_report = Report(abspath('pie_chart'), 'image/png')
    file('pie.png', 'wb').write(pie_report(o=inv).render().getvalue())
    hbar_report = Report(abspath('hbar_chart'), 'image/svg')
    file('hbar.svg', 'wb').write(hbar_report(o=inv).render().getvalue())
    vbar_report = Report(abspath('vbar_chart'), 'image/svg')
    file('vbar.svg', 'wb').write(vbar_report(o=inv).render().getvalue())
    line_report = Report(abspath('line_chart'), 'image/png')
    file('line.png', 'wb').write(line_report(o=inv).render().getvalue())
