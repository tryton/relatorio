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

import os
import re
import md5
import urllib
import zipfile
from cStringIO import StringIO

import lxml.etree
import genshi
import genshi.output
from genshi.template import MarkupTemplate

GENSHI_TAGS = re.compile(r'''relatorio://((/)?(for|choose|otherwise|when|if|with)( (\w+)=["'](.*)["']|)|.*)''')
EXTENSIONS = {'image/png': 'png',
              'image/jpeg': 'jpg',
              'image/bmp': 'bmp',
              'image/gif': 'gif',
              'image/tiff': 'tif',
              'image/xbm': 'xbm',
             }

_encode = genshi.output.encode
ETElement = lxml.etree.Element


class ImageHref:
    
    def __init__(self, zipfile):
        self.zip = zipfile

    def __call__(self, expr, name):
        bitstream, mimetype = expr
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
        super(Template, self).__init__(source, filepath, filename, loader,
                                       encoding, lookup, allow_exec)

    def _parse(self, source, encoding):
        inzip = zipfile.ZipFile(self.filepath)
        content = inzip.read('content.xml')
        styles = inzip.read('styles.xml')
        inzip.close()

        content = super(Template, self)._parse(self.add_directives(content),
                                               encoding)
        styles = super(Template, self)._parse(self.add_directives(styles),
                                              encoding)
        return [(genshi.core.PI, ('relatorio', 'styles.xml'), None)] +\
                styles +\
                [(genshi.core.PI, ('relatorio', 'content.xml'), None)] +\
                content

    def add_directives(self, content):
        tree = lxml.etree.parse(StringIO(content))
        root = tree.getroot()
        self.namespaces = root.nsmap.copy()
        self.namespaces['py'] = 'http://genshi.edgewall.org/'

        self._handle_text_a(tree)
        self._handle_images(tree)
        return StringIO(lxml.etree.tostring(tree))

    def _handle_text_a(self, tree):
        """
        Will treat all text:a tag (py:if/for/choose/when/otherwise)
        tags
        """
        # Some tag name constants
        table_cell_tag = '{%s}table-cell' % self.namespaces['table']
        attrib_name = '{%s}attrs' % self.namespaces['py']
        office_name = '{%s}value' % self.namespaces['office']
        office_valuetype = '{%s}value-type' % self.namespaces['office']
        genshi_name = '{%s}replace' % self.namespaces['py']
        xlink_href_attrib = '{%s}href' % self.namespaces['xlink']

        # First we create the list of all the text:a nodes.
        # If this node href matches the relatorio URL it is kept.
        # If this node href matches a genshi directive it is kept for further
        # processing.
        genshi_directives, text_a = [], []
        for statement in tree.xpath('//text:a', namespaces=self.namespaces):
            href = urllib.unquote(statement.attrib[xlink_href_attrib])
            match_obj = GENSHI_TAGS.match(href)
            if match_obj is None:
                continue
            expr, closing, directive, _, attr, attr_val = match_obj.groups()
            if directive is not None:
                genshi_directives.append((statement, href))
            text_a.append((statement, 
                           (expr, closing, directive, attr, attr_val)))

        # Then we match the opening and closing directives together
        idx = 0
        genshi_pairs, inserted = [], []
        for statement, href in genshi_directives:
            if not href.startswith('relatorio:///'):
                genshi_pairs.append([statement, None])
                inserted.append(idx)
                idx += 1
            else:
                genshi_pairs[inserted.pop()][1] = statement

        for a_node, parsed in text_a:
            expr, c_dir, directive, attr, a_val = parsed

            if directive is not None:
                # If the text:a is a genshi directive statement:
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
                    if pair[0] == a_node:
                        break
                opening, closing = pair

                o_ancestors = list(opening.iterancestors())
                c_ancestors = list(closing.iterancestors())
                for n in o_ancestors:
                    if n in c_ancestors:
                        ancestor = n
                        break

                genshi_node = ETElement('{%s}%s' % (self.namespaces['py'],
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
                a_node.attrib['{%s}replace' % self.namespaces['py']] = expr
                parent = a_node.getparent().getparent()
                if parent is None or parent.tag != table_cell_tag:
                    continue
                if parent.attrib.get(office_valuetype, 'string') != 'string':
                    # The grand-parent tag is a table cell we set the
                    # office:value attribute of this cell
                    dico = "{'%s': %s}" % (office_name, expr)
                    parent.attrib[attrib_name] = dico
                    parent.attrib.pop(office_name, None)

    def _handle_images(self, tree):
        for draw in tree.xpath('//draw:frame', namespaces=self.namespaces):
            d_name = draw.attrib['{%s}name' % self.namespaces['draw']]
            if d_name.startswith('image: '):
                attr_expr = "make_href(%s, %r)" % (d_name[7:], d_name[7:])
                attributes = {}
                attributes['{%s}attrs' % self.namespaces['py']] = attr_expr
                image_node = ETElement('{%s}image' % self.namespaces['draw'],
                                       attrib=attributes,
                                       nsmap=self.namespaces)
                draw.replace(draw[0], image_node)


    def generate(self, *args, **kwargs):
        serializer = OOSerializer(self.filepath)
        kwargs['make_href'] = ImageHref(serializer.outzip)
        generate_all = super(Template, self).generate(*args, **kwargs)

        return OOStream(generate_all, serializer)


class OOStream(genshi.core.Stream):

    def __init__(self, content_stream, serializer):
        self.events = content_stream
        self.serializer = serializer

    def render(self, method=None, encoding='utf-8', out=None, **kwargs):
        return self.serializer(self.events)

    def serialize(self, method, **kwargs):
        return self.render(method, **kwargs)

    def __or__(self, function):
        return OOStream(self.events | function, self.serializer)


class OOSerializer:

    def __init__(self, oo_path):
        self.inzip = zipfile.ZipFile(oo_path)
        self.new_oo = StringIO()
        self.outzip = zipfile.ZipFile(self.new_oo, 'w')
        self.xml_serializer = genshi.output.XMLSerializer()

    def __call__(self, stream):
        files = {'styles.xml': [], 'content.xml': []}
        for kind, data, pos in stream:
            if kind == genshi.core.PI and data[0] == 'relatorio':
                stream_for = data[1]
                continue
            files[stream_for].append((kind, data, pos))

        for f in self.inzip.infolist():
            if f.filename in files:
                stream = files[f.filename]
                self.outzip.writestr(f.filename, 
                                     _encode(self.xml_serializer(stream)))
            else:
                self.outzip.writestr(f, self.inzip.read(f.filename))
        self.inzip.close()
        self.outzip.close()

        return self.new_oo
