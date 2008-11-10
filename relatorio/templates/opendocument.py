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

import warnings
warnings.filterwarnings('always', module='relatorio.templates.opendocument')

import lxml.etree
import genshi
import genshi.output
from genshi.template import MarkupTemplate

from relatorio.templates.base import RelatorioStream
from relatorio.reporting import Report, MIMETemplateLoader

GENSHI_EXPR = re.compile(r'''((/)?(for|choose|otherwise|when|if|with)\s*(\s(\w+)=["'](.*)["']|$)|.*)''')
EXTENSIONS = {'image/png': 'png',
              'image/jpeg': 'jpg',
              'image/bmp': 'bmp',
              'image/gif': 'gif',
              'image/tiff': 'tif',
              'image/xbm': 'xbm',
             }

output_encode = genshi.output.encode
EtreeElement = lxml.etree.Element


class OOTemplateError(genshi.template.base.TemplateSyntaxError):
    "Error to raise when there is a SyntaxError in the genshi template"


class ImageHref:
    "A class used to add image in the odf zipfile"
    
    def __init__(self, zfile, context):
        self.zip = zfile
        self.context = context.copy()

    def __call__(self, expr, name):
        bitstream, mimetype = expr
        if isinstance(bitstream, Report):
            bitstream = bitstream(**self.context).render()
        bitstream.seek(0)
        file_content = bitstream.read()
        name = md5.new(file_content).hexdigest()
        path = 'Pictures/%s.%s' % (name, EXTENSIONS[mimetype])
        if path not in self.zip.namelist():
            self.zip.writestr(path, file_content)
        return {'{http://www.w3.org/1999/xlink}href': path}


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
        xpath_expr = "//text:a[starts-with(@xlink:href, 'relatorio://')]"\
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
        r_statements, genshi_dir = [], []
        xlink_href_attrib = '{%s}href' % self.namespaces['xlink']
        text_a = '{%s}a' % self.namespaces['text']
        placeholder = '{%s}placeholder' % self.namespaces['text']

        s_xpath = "//text:a[starts-with(@xlink:href, 'relatorio://')]" \
                  "| //text:placeholder"
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

            expr, closing, directive, _, attr, attr_val = \
                    GENSHI_EXPR.match(expr).groups()
            if directive is not None:
                genshi_dir.append((statement, closing))
            r_statements.append((statement, 
                                 (expr, closing, directive, attr, attr_val)))

        return r_statements, genshi_dir

    def _handle_relatorio_tags(self, tree):
        """
        Will treat all relatorio tag (py:if/for/choose/when/otherwise)
        tags
        """
        # Some tag name constants
        table_cell_tag = '{%s}table-cell' % self.namespaces['table']
        attrib_name = '{%s}attrs' % self.namespaces['py']
        office_name = '{%s}value' % self.namespaces['office']
        office_valuetype = '{%s}value-type' % self.namespaces['office']
        genshi_replace = '{%s}replace' % self.namespaces['py']

        r_statements, genshi_directives = self._relatorio_statements(tree)
        # We match the opening and closing directives together
        idx = 0
        genshi_pairs, inserted = [], []
        for statement, closing in genshi_directives:
            if closing is None:
                genshi_pairs.append([statement, None])
                inserted.append(idx)
                idx += 1
            else:
                genshi_pairs[inserted.pop()][1] = statement

        for r_node, parsed in r_statements:
            expr, c_dir, directive, attr, a_val = parsed

            if directive is not None:
                # If the node is a genshi directive statement:
                #    - we operate only on opening statement
                #    - we find the nearest ancestor of the closing and opening
                #      statement
                #    - we create a <py:xxx> node
                #    - we add all the node between the opening and closing
                #      statements to this new node
                #    - we replace the opening statement by the <py:for> node
                #    - we delete the closing statement

                if c_dir is not None:
                    # pass the closing statements
                    continue
                for pair in genshi_pairs:
                    if pair[0] == r_node:
                        opening, closing = pair
                        break

                o_ancestors = list(opening.iterancestors())
                c_ancestors = list(closing.iterancestors())
                for node in o_ancestors:
                    if node in c_ancestors:
                        ancestor = node
                        break

                genshi_node = EtreeElement('{%s}%s' % (self.namespaces['py'],
                                                       directive), 
                                           attrib={attr: a_val},
                                           nsmap=self.namespaces)
                can_append = False
                for node in ancestor.iterchildren():
                    if node in o_ancestors:
                        outermost_o_ancestor = node
                        can_append = True
                        continue
                    if node in c_ancestors:
                        outermost_c_ancestor = node
                        break
                    if can_append:
                        genshi_node.append(node)
                ancestor.replace(outermost_o_ancestor, genshi_node)
                ancestor.remove(outermost_c_ancestor)
            else:
                # It's not a genshi statement it's a python expression
                r_node.attrib[genshi_replace] = expr
                parent = r_node.getparent().getparent()
                if parent is None or parent.tag != table_cell_tag:
                    continue
                if parent.attrib.get(office_valuetype, 'string') != 'string':
                    # The grand-parent tag is a table cell we set the
                    # office:value attribute of this cell
                    dico = "{'%s': %s}" % (office_name, expr)
                    parent.attrib[attrib_name] = dico
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
