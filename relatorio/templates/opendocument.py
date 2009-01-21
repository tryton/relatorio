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
from genshi.filters import Transformer
from genshi.filters.transform import ENTER, EXIT
from genshi.core import Stream


from relatorio.templates.base import RelatorioStream
from relatorio.reporting import Report, MIMETemplateLoader
try:
    from relatorio.templates.chart import Template as ChartTemplate
except ImportError:
    ChartTemplate = type(None)

GENSHI_EXPR = re.compile(r'''
        (/)?                                 # is this a closing tag?
        (for|if|choose|when|otherwise|with)  # tag directive
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

RELATORIO_URI = 'http://relatorio.openhex.org/'
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


class ColumnCounter:
    """A class used to add the correct number of column definitions to a
    table containing an horizontal repetition"
    """
    def __init__(self):
        self.temp_counters = {}
        self.counters = {}

    def reset(self, loop_id):
        self.temp_counters[loop_id] = 0

    def inc(self, loop_id):
        self.temp_counters[loop_id] += 1

    def store(self, loop_id, table_name):
        self.counters[table_name] = max(self.temp_counters.pop(loop_id),
                                        self.counters.get(table_name, 0))


def wrap_nodes_between(first, last, new_parent):
    old_parent = first.getparent()
    for node in first.itersiblings():
        if node is last:
            break
        # appending a node to a new parent also
        # remove it from its previous parent
        new_parent.append(node)
    old_parent.replace(first, new_parent)
    old_parent.remove(last)


class Template(MarkupTemplate):

    def __init__(self, source, filepath=None, filename=None, loader=None,
                 encoding=None, lookup='strict', allow_exec=True):
        self.namespaces = {}
        self.inner_docs = []
        self.has_col_loop = False
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
        self.namespaces['relatorio'] = RELATORIO_URI

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
            closing, directive, attr, attr_val = \
                    GENSHI_EXPR.match(expr).groups()
            is_opening = closing != '/'

            warn_msg = None
            if not statement.text:
                warn_msg = "No statement text in '%s' for '%s'" \
                           % (self.filepath, expr)
            elif expr != statement.text and statement.tag == text_a:
                warn_msg = "url and text do not match in %s: %s != %s" \
                           % (self.filepath, expr,
                              statement.text.encode('utf-8'))
            if warn_msg:
                if directive is not None and not is_opening:
                    warn_msg += " corresponding to opening tag '%s'" \
                                % opened_tags[-1].text
                warnings.warn(warn_msg)

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
        table_namespace = self.namespaces['table']
        table_tag = '{%s}table' % table_namespace
        table_col_tag = '{%s}table-column' % table_namespace
        table_row_tag = '{%s}table-row' % table_namespace
        table_cell_tag = '{%s}table-cell' % table_namespace
        table_cov_cell_tag = '{%s}covered-table-cell' % table_namespace
        table_num_col_attr = '{%s}number-columns-repeated' % table_namespace
        table_name_attr = '{%s}name' % table_namespace
        table_rowspan_attr = '{%s}number-rows-spanned' % table_namespace

        office_name = '{%s}value' % self.namespaces['office']
        office_valuetype = '{%s}value-type' % self.namespaces['office']

        py_namespace = self.namespaces['py']
        py_attrs_attr = '{%s}attrs' % py_namespace
        genshi_replace = '{%s}replace' % py_namespace

        repeat_tag = '{%s}repeat' % self.namespaces['relatorio']

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
                        # c_ancestors.index(node) raise ValueError if node is
                        # not a child of c_ancestors
                        pass
                    o_ancestors.append(node)
                assert ancestor is not None, \
                       "No common ancestor found for opening and closing tag"
                outermost_o_ancestor = o_ancestors[-1]
                outermost_c_ancestor = c_ancestors[-1]

                # handle horizontal repetition (over columns)
                if directive == "for" and ancestor.tag == table_row_tag:
                    self.has_col_loop = True

                    # table (it is not necessarily the parent of ancestor)
                    table_node = ancestor.iterancestors(table_tag).next()
                    table_name = table_node.attrib[table_name_attr]

                    # add counting instructions
                    loop_id = id(opening)

                    # 1) add reset counter code on the row opening tag
                    #    (through a py:attrs attribute).
                    # Note that table_name is not needed in the first two
                    # operations, but a unique id within the table is required
                    # to support nested column repetition
                    attr_value = "__reset_col_count(%d)" % loop_id
                    ancestor.attrib[py_attrs_attr] = attr_value

                    # 2) add increment code (through a py:attrs attribute) on
                    #    the first cell node after the opening (cell node)
                    #    ancestor
                    enclosed_cell = outermost_o_ancestor.getnext()
                    assert enclosed_cell.tag == table_cell_tag
                    attr_value = "__inc_col_count(%d)" % loop_id
                    enclosed_cell.attrib[py_attrs_attr] = attr_value

                    # 3) add "store count" code as a py:replace node, as the
                    #    last child of the row
                    attr_value = "__store_col_count(%d, %r)" % (loop_id,
                                                                table_name)
                    replace_node = EtreeElement('{%s}replace' % py_namespace,
                                                attrib={'value': attr_value},
                                                nsmap=self.namespaces)
                    ancestor.append(replace_node)

                    # find the position in the row of the cells holding the
                    # <for> and </for> instructions
                    #XXX: count cells only instead of *
                    position_xpath_expr = 'count(preceding-sibling::*)'
                    opening_pos = \
                        int(outermost_o_ancestor.xpath(position_xpath_expr,
                                                   namespaces=self.namespaces))
                    closing_pos = \
                        int(outermost_c_ancestor.xpath(position_xpath_expr,
                                                   namespaces=self.namespaces))

                    # check whether or not the opening tag spans several rows
                    o_node_attrs = outermost_o_ancestor.attrib
                    if table_rowspan_attr in o_node_attrs:
                        rows_spanned = int(o_node_attrs[table_rowspan_attr])
                        # if so, we need to replace the corresponding cell on
                        # the next line (a covered-table-cell) by a duplicate
                        # py:for node, delete the covered-table-cell
                        # corresponding to the /for, and move all cells between
                        # them into the py:for node
                        row_node = outermost_o_ancestor.getparent()
                        assert row_node.tag == table_row_tag
                        next_rows = row_node.itersiblings(table_row_tag)
                        for row_idx in range(rows_spanned-1):
                            next_row_node = next_rows.next()
                            first = next_row_node[opening_pos]
                            last = next_row_node[closing_pos]
                            assert first.tag == table_cov_cell_tag
                            assert last.tag == table_cov_cell_tag

                            # execute moves (add a <py:for> node around
                            # the column definitions nodes)
                            tag = '{%s}%s' % (py_namespace, directive)
                            for_node = EtreeElement(tag,
                                                    attrib={attr: a_val},
                                                    nsmap=self.namespaces)
                            wrap_nodes_between(first, last, for_node)

                    # check if this table's headers were already processed
                    repeat_node = table_node.find(repeat_tag)
                    if repeat_node is not None:
                        prev_pos = (int(repeat_node.attrib['opening']),
                                    int(repeat_node.attrib['closing']))
                        if (opening_pos, closing_pos) != prev_pos:
                            raise Exception(
                                'Incoherent column repetition found! '
                                'If a table has several lines with repeated '
                                'columns, the repetition need to be on the '
                                'same columns across all lines.')
                    else:
                        # compute splits: we need to split any column header
                        # which is repeated so many times that it encompass
                        # any of the column headers that we need to repeat
                        to_split = []
                        idx = 0
                        childs = list(table_node.iterchildren(table_col_tag))
                        for tag in childs:
                            if table_num_col_attr in tag.attrib:
                                oldidx = idx
                                idx += int(tag.attrib[table_num_col_attr])
                                if oldidx < opening_pos < idx or \
                                   oldidx < closing_pos < idx:
                                    to_split.append(tag)
                            else:
                                idx += 1

                        # split tags
                        for tag in to_split:
                            tag_pos = table_node.index(tag)
                            num = int(tag.attrib.pop(table_num_col_attr))
                            new_tags = [deepcopy(tag) for _ in range(num)]
                            table_node[tag_pos:tag_pos+1] = new_tags

                        # compute moves and deletes: the column headers
                        # corresponding to the opening and closing tags
                        # need to be deleted. The column headers between them
                        # need to be moved to inside the "repeat" tag (which
                        # is to be created later).
                        coldefs = list(table_node.iterchildren(table_col_tag))
                        first = table_node[opening_pos]
                        last = table_node[closing_pos]

                        # execute moves (add a <relatorio:repeat> node around
                        # the column definitions nodes)
                        attribs = {
                           "opening": str(opening_pos),
                           "closing": str(closing_pos),
                           "table": table_name
                        }
                        repeat_node = EtreeElement(repeat_tag, attrib=attribs,
                                                   nsmap=self.namespaces)
                        wrap_nodes_between(first, last, repeat_node)

                # - we create a <py:xxx> node
                genshi_node = EtreeElement('{%s}%s' % (py_namespace,
                                                       directive),
                                           attrib={attr: a_val},
                                           nsmap=self.namespaces)

                # - we move all the nodes between the opening and closing
                #   statements to this new node (append also removes from old
                #   parent)
                # - we replace the opening statement by the <py:xxx> node
                # - we delete the closing statement (and its ancestors)
                wrap_nodes_between(outermost_o_ancestor, outermost_c_ancestor,
                                   genshi_node)
            else:
                # It's not a genshi statement it's a python expression
                r_node.attrib[genshi_replace] = expr
                parent = r_node.getparent().getparent()
                if parent is None or parent.tag != table_cell_tag:
                    continue

                # The grand-parent tag is a table cell we should set the
                # correct value and type for this cell.
                dico = "{'%s': %s, '%s': guess_type(%s)}"
                parent.attrib[py_attrs_attr] = dico % (office_name, expr,
                                                     office_valuetype, expr)
                parent.attrib.pop(office_valuetype, None)
                parent.attrib.pop(office_name, None)

    def _handle_images(self, tree):
        "replaces all draw:frame named 'image: ...' by a draw:image node"
        draw_name = '{%s}name' % self.namespaces['draw']
        draw_image = '{%s}image' % self.namespaces['draw']
        py_attrs = '{%s}attrs' % self.namespaces['py']
        xpath_expr = "//draw:frame[starts-with(@draw:name, 'image:')]"
        for draw in tree.xpath(xpath_expr, namespaces=self.namespaces):
            d_name = draw.attrib[draw_name]
            attr_expr = "make_href(%s, %r)" % (d_name[7:], d_name[7:])
            image_node = EtreeElement(draw_image,
                                      attrib={py_attrs: attr_expr},
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

        counter = ColumnCounter()
        kwargs['__reset_col_count'] = counter.reset
        kwargs['__inc_col_count'] = counter.inc
        kwargs['__store_col_count'] = counter.store

        stream = super(Template, self).generate(*args, **kwargs)
        if self.has_col_loop:
            transformation = DuplicateColumnHeaders(counter)
            col_filter = Transformer('//repeat[namespace-uri()="%s"]'
                                     % RELATORIO_URI)
            col_filter = col_filter.apply(transformation)
            stream = Stream(list(stream), self.serializer) | col_filter
        return RelatorioStream(stream, serializer)


class DuplicateColumnHeaders(object):
    def __init__(self, counter):
        self.counter = counter

    def __call__(self, stream):
        for mark, (kind, data, pos) in stream:
            # for each repeat tag found
            if mark is ENTER:
                # get the number of columns for that table
                attrs = data[1]
                table = attrs.get('table')
                col_count = self.counter.counters[table]

                # collect events (column header tags) to repeat
                events = []
                for submark, event in stream:
                    if submark is EXIT:
                        break
                    events.append(event)

                # repeat them
                for _ in range(col_count):
                    for event in events:
                        yield None, event
            else:
                yield mark, (kind, data, pos)


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
