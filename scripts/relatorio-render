#!/usr/bin/env python
import json
import mimetypes
import os
from argparse import ArgumentParser, FileType

from relatorio import Report


def main(input_, data, output=None):
    input_ = os.path.abspath(input_)
    mimetype, _ = mimetypes.guess_type(input_)
    report = Report(input_, mimetype)
    content = report(**data).render().getvalue()
    if output:
        with open(output, 'wb') as fp:
            fp.write(content)


def run():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', required=True)
    parser.add_argument('-o', '--output', dest='output')
    parser.add_argument('-d', '--data', dest='data', type=FileType('r'),
        help="JSON file with data to render")

    args = parser.parse_args()
    if args.data:
        data = json.load(args.data)
    else:
        data = {}
    main(args.input, data, args.output)


if __name__ == '__main__':
    run()
