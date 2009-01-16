###############################################################################
#
# Copyright (c) 2007, 2008 OpenHex SPRL. (http://openhex.com) All Rights
# Reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

__metaclass__ = type

import re
import md5
import urllib
import zipfile
from cStringIO import StringIO
from copy import deepcopy


import warnings
warnings.filterwarnings('always', module='relatorio.templates.opendocument')

import lxml.etree
import genshi
import genshi.output
from genshi.template import MarkupTemplate

from relatorio.templates.base import RelatorioStream
from relatorio.reporting import Report, MIMETemplateLoader
try:
    from relatorio.templates.chart import Template as ChartTemplate
except ImportError:
    ChartTemplate = type(None)

GENSHI_EXPR = re.compile(r'''
        (/)?                                 # is this a closing tag?
        (for|choose|otherwise|when|if|with)  # tag directive
        \s*
        (?:\s(\w+)=["'](.*)["']|$)           # match a single attr & its value
        |
        .*                                   # or anything else
        ''', re.VERBOSE)

EXTENSIONS = {'image/png': 'png',
              'image/jpeg': 'jpg',
              'image/bmp': 'bmp',
              'image/gif': 'gif',
              'image/tiff': 'tif',
              'image/xbm': 'xbm',
             }

output_encode = genshi.output.encode
EtreeElement = lxml.etree.Element

def guess_type(val):
    if isinstance(val, (str, unicode)):
        return 'string'
    elif isinstance(val, (int, float)):
        return 'float'

class OOTemplateError(genshi.template.base.TemplateSyntaxError):
    "Error to raise when there is a SyntaxError in the genshi template"


class ImageHref:
    "A class used to add images in the odf zipfile"

    def __init__(self, zfile, context):
        self.zip = zfile
        self.context = context.copy()

    def __call__(self, expr, name):
        #FIXME: name argument is unused
        bitstream, mimetype = expr
        if isinstance(bitstream, Report):
            bitstream = bitstream(**self.context).render()
        elif isinstance(bitstream, ChartTemplate):
            bitstream = bitstream.generate(**self.context).render()
        bitstream.seek(0)
        file_content = bitstream.read()
        name = md5.new(file_content).hexdigest()
        path = 'Pictures/%s.%s' % (name, EXTENSIONS[mimetype])
        if path not in self.zip.namelist():
            self.zip.writestr(path, file_content)
        return {'{http://www.w3.org/1999/xlink}href': path}

class TableColumnDef:
    """A class used to add the correct number of column definitions to a
    table containing an horizontal repetition"
    """
    def __init__(self, zfile, context):
        self.zip = zfile
        self.context = context.copy()

    def __call__(self, expr, name):
        #FIXME: name argument is unused
        return

class Template(MarkupTemplate):

    def __init__(self, source, filepath=None, filename=None, loader=None,
                 encoding=None, lookup='strict', allow_exec=True):
        self.namespaces = {}
        self.inner_docs = []
        super(Template, self).__init__(source, filepath, filename, loader,
                                       encoding, lookup, allow_exec)

    def _parse(self, source, encoding):
        """parses the odf file.

        It adds genshi directives and finds the inner docs.
        """
        zf = zipfile.ZipFile(self.filepath)
        content = zf.read('content.xml')
        styles = zf.read('styles.xml')

        template = super(Template, self)
        content = template._parse(self.insert_directives(content), encoding)
        styles = template._parse(self.insert_directives(styles), encoding)
        content_files = [('content.xml', content)]
        styles_files = [('styles.xml', styles)]

        while self.inner_docs:
            doc = self.inner_docs.pop()
            c_path, s_path = doc + '/content.xml', doc + '/styles.xml'
            content = zf.read(c_path)
            styles = zf.read(s_path)

            c_parsed = template._parse(self.insert_directives(zf.read(c_path)),
                                       encoding)
            s_parsed = template._parse(self.insert_directives(zf.read(s_path)),
                                       encoding)
            content_files.append((c_path, c_parsed))
            styles_files.append((s_path, s_parsed))

        zf.close()
        parsed = []
        for fpath, fparsed in content_files + styles_files:
            parsed.append((genshi.core.PI, ('relatorio', fpath), None))
            parsed += fparsed

        return parsed

    def insert_directives(self, content):
        """adds the genshi directives, handle the images and the innerdocs.
        """
        tree = lxml.etree.parse(StringIO(content))
        root = tree.getroot()
        self.namespaces = root.nsmap.copy()
        self.namespaces['py'] = 'http://genshi.edgewall.org/'

        self._invert_style(tree)
        self._handle_relatorio_tags(tree)
        self._handle_images(tree)
        self._handle_innerdocs(tree)
        return StringIO(lxml.etree.tostring(tree))

    def _invert_style(self, tree):
        "inverts the text:a and text:span"
        xpath_expr = "//text:a[starts-with(@xlink:href, 'relatorio://')]" \
                     "/text:span"
        for span in tree.xpath(xpath_expr, namespaces=self.namespaces):
            text_a = span.getparent()
            outer = text_a.getparent()
            text_a.text = span.text
            span.text = ''
            text_a.remove(span)
            outer.replace(text_a, span)
            span.append(text_a)

    def _relatorio_statements(self, tree):
        "finds the relatorio statements (text:a/text:placeholder)"
        # If this node href matches the relatorio URL it is kept.
        # If this node href matches a genshi directive it is kept for further
        # processing.
        xlink_href_attrib = '{%s}href' % self.namespaces['xlink']
        text_a = '{%s}a' % self.namespaces['text']
        placeholder = '{%s}placeholder' % self.namespaces['text']
        s_xpath = "//text:a[starts-with(@xlink:href, 'relatorio://')]" \
                  "| //text:placeholder"

        r_statements = []
        opened_tags = []
        # We map each opening tag with its closing tag
        closing_tags = {}
        for statement in tree.xpath(s_xpath, namespaces=self.namespaces):
            if statement.tag == placeholder:
                expr = statement.text[1:-1]
            elif statement.tag == text_a:
                expr = urllib.unquote(statement.attrib[xlink_href_attrib][12:])

            if not expr:
                raise OOTemplateError("No expression in the tag",
                                      self.filepath)
            elif not statement.text:
                warnings.warn('No statement text in %s' % self.filepath)
            elif expr != statement.text and statement.tag == text_a:
                warnings.warn('url and text do not match in %s: %s != %s'
                              % (self.filepath, expr,
                                 statement.text.encode('utf-8')))

            closing, directive, attr, attr_val = \
                    GENSHI_EXPR.match(expr).groups()
            is_opening = closing != '/'
            if directive is not None:
                # map closing tags with their opening tag
                if is_opening:
                    opened_tags.append(statement)
                else:
                    closing_tags[id(opened_tags.pop())] = statement
            # - we only need to return opening statements
            if is_opening:
                r_statements.append((statement,
                                     (expr, directive, attr, attr_val))
                                   )
        assert not opened_tags
        return r_statements, closing_tags

    def _handle_relatorio_tags(self, tree):
        """
        Will treat all relatorio tag (py:if/for/choose/when/otherwise)
        tags
        """
        # Some tag/attribute name constants
        table_cell_tag = '{%s}table-cell' % self.namespaces['table']
        table_row_tag = '{%s}table-row' % self.namespaces['table']
        num_col_attr = '{%s}number-columns-repeated' % self.namespaces['table']
        attrib_name = '{%s}attrs' % self.namespaces['py']
        office_name = '{%s}value' % self.namespaces['office']
        office_valuetype = '{%s}value-type' % self.namespaces['office']
        py_namespace = self.namespaces['py']
        genshi_replace = '{%s}replace' % py_namespace

        r_statements, closing_tags = self._relatorio_statements(tree)

        for r_node, parsed in r_statements:
            expr, directive, attr, a_val = parsed

            # If the node is a genshi directive statement:
            if directive is not None:
                opening = r_node
                closing = closing_tags[id(r_node)]

                # - we find the nearest common ancestor of the closing and
                #   opening statements
                o_ancestors = []
                c_ancestors = list(closing.iterancestors())
                ancestor = None
                for node in opening.iterancestors():
                    try:
                        idx = c_ancestors.index(node)
                        assert c_ancestors[idx] == node
                        # we only need ancestors up to the common one
                        del c_ancestors[idx:]
                        ancestor = node
                        break
                    except ValueError:
                        pass
                    o_ancestors.append(node)
                assert ancestor is not None, \
                       "No common ancestor found for opening and closing tag"

                # handle horizontal repetition (over columns)
                if False:
                #if directive == "for" and ancestor.tag == table_row_tag:
                    print "horizontal repetition", a_val
                    # find position of current cell in row
                    position_xpath_expr = \
                    'count(ancestor::table:table-cell/preceding-sibling::*)'
                    opening_pos = opening.xpath(position_xpath_expr,
                                                namespaces=self.namespaces)
                    closing_pos = closing.xpath(position_xpath_expr,
                                                namespaces=self.namespaces)
                    print "opening_pos", opening_pos
                    print "closing_pos", closing_pos

                    idx = 0
                    table_node = opening.xpath('ancestor::table:table[1]',
                                               namespaces=self.namespaces)[0]
                    #XXX: use getiterator('table:table-column') instead of xpath?
                    to_split = []
                    to_move = []
                    for tag in table_node.xpath('table:table-column',
                                                namespaces=self.namespaces):
                        if num_col_attr in tag.attrib:
                            oldidx = idx
                            idx += int(tag.attrib[num_col_attr])
                            print "oldidx", oldidx, "idx", idx
                            if oldidx < opening_pos < idx or \
                               oldidx < closing_pos < idx:
                                to_split.append(tag)
                                print "to_split", to_split
                        else:
                            idx += 1

                    # split tags
                    for tag in to_split:
                        tag_pos = table_node.index(tag)
                        print "tag_pos", tag_pos
                        num = int(tag.attrib[num_col_attr])
                        tag.attrib.pop(num_col_attr)
                        new_tags = [deepcopy(tag) for _ in range(num)]
                        table_node[tag_pos:tag_pos] = new_tags

                    # compute moves
                    if False:
                        if idx < opening_pos:
                            pass
                        elif opening_pos < idx < closing_pos:
                            to_move.append(tag)
                        else:
                            break
                        print idx
                    # move tags
                    #
                    # add a <py:for each="%s"> % a_val
#                    for_node = EtreeElement('{%s}%s' % (py_namespace, 'for'),
#                                            attrib={attr: a_val},
#                                            nsmap=self.namespaces)

                # - we create a <py:xxx> node
                genshi_node = EtreeElement('{%s}%s' % (py_namespace,
                                                       directive),
                                           attrib={attr: a_val},
                                           nsmap=self.namespaces)

                # - we add all the nodes between the opening and closing
                #   statements to this new node
                outermost_o_ancestor = o_ancestors[-1]
                outermost_c_ancestor = c_ancestors[-1]
                for node in outermost_o_ancestor.itersiblings():
                    if node is outermost_c_ancestor:
                        break
                    genshi_node.append(node)

                # - we replace the opening statement by the <py:xxx> node
                ancestor.replace(outermost_o_ancestor, genshi_node)

                # - we delete the closing statement (and its ancestors)
                ancestor.remove(outermost_c_ancestor)
            else:
                # It's not a genshi statement it's a python expression
                r_node.attrib[genshi_replace] = expr
                parent = r_node.getparent().getparent()
                if parent is None or parent.tag != table_cell_tag:
                    continue

                # The grand-parent tag is a table cell we should set the
                # correct value and type for this cell.
                dico = "{'%s': %s, '%s': guess_type(%s)}"
                parent.attrib[attrib_name] = dico % (office_name, expr,
                                                     office_valuetype, expr)
                parent.attrib.pop(office_valuetype, None)
                parent.attrib.pop(office_name, None)

    def _handle_images(self, tree):
        "replaces all draw:frame named 'image: ...' by a draw:image node"
        draw_name = '{%s}name' % self.namespaces['draw']
        draw_image = '{%s}image' % self.namespaces['draw']
        python_attrs = '{%s}attrs' % self.namespaces['py']
        xpath_expr = "//draw:frame[starts-with(@draw:name, 'image:')]"
        for draw in tree.xpath(xpath_expr, namespaces=self.namespaces):
            d_name = draw.attrib[draw_name]
            attr_expr = "make_href(%s, %r)" % (d_name[7:], d_name[7:])
            image_node = EtreeElement(draw_image,
                                      attrib={python_attrs: attr_expr},
                                      nsmap=self.namespaces)
            draw.replace(draw[0], image_node)

    def _handle_innerdocs(self, tree):
        "finds inner_docs and adds them to the processing stack."
        href_attrib = '{%s}href' % self.namespaces['xlink']
        xpath_expr = "//draw:object[starts-with(@xlink:href, './')" \
                     "and @xlink:show='embed']"
        for draw in tree.xpath(xpath_expr, namespaces=self.namespaces):
            self.inner_docs.append(draw.attrib[href_attrib][2:])

    def generate(self, *args, **kwargs):
        "creates the RelatorioStream."
        serializer = OOSerializer(self.filepath)
        kwargs['make_href'] = ImageHref(serializer.outzip, kwargs)
        kwargs['guess_type'] = guess_type
        generate_all = super(Template, self).generate(*args, **kwargs)

        return RelatorioStream(generate_all, serializer)


class OOSerializer:

    def __init__(self, oo_path):
        self.inzip = zipfile.ZipFile(oo_path)
        self.new_oo = StringIO()
        self.outzip = zipfile.ZipFile(self.new_oo, 'w')
        self.xml_serializer = genshi.output.XMLSerializer()

    def __call__(self, stream):
        files = {}
        for kind, data, pos in stream:
            if kind == genshi.core.PI and data[0] == 'relatorio':
                stream_for = data[1]
                continue
            files.setdefault(stream_for, []).append((kind, data, pos))

        for f_info in self.inzip.infolist():
            if f_info.filename.startswith('ObjectReplacements'):
                continue
            elif f_info.filename in files:
                stream = files[f_info.filename]
                self.outzip.writestr(f_info.filename,
                                     output_encode(self.xml_serializer(stream)))
            else:
                self.outzip.writestr(f_info, self.inzip.read(f_info.filename))
        self.inzip.close()
        self.outzip.close()

        return self.new_oo

MIMETemplateLoader.add_factory('oo.org', Template)
