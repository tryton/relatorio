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

__revision__ = "$Id: odt.py 21 2008-07-17 16:46:24Z nicoe $"
__metaclass__ = type

import os
import re
import md5
import zipfile
from cStringIO import StringIO

import lxml.etree
import genshi
import genshi.output
from genshi.template import MarkupTemplate

NS = {'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
      'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
      'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
      'xlink': 'http://www.w3.org/1999/xlink',
      'py': 'http://genshi.edgewall.org/',
      }
GENSHI_TAGS = re.compile(r'<(/)?(for|choose|otherwise|when|if|with)( (\w+)="(.*)"|)>')
EXTENSIONS = {'image/png': 'png',
              'image/jpeg': 'jpg',
              'image/bmp': 'bmp',
              'image/gif': 'gif',
              'image/tiff': 'tif',
              'image/xbm': 'xbm',
             }

_encode = genshi.output.encode


class ImageHref:
    
    def __init__(self, zipfile):
        self.zip = zipfile
        self.count = 0

    def __call__(self, expr, name):
        bitstream, mimetype = expr
        name = md5.new('%s-%s' % (name, self.count)).hexdigest()
        self.count += 1
        path = 'Pictures/%s.%s' % (name, EXTENSIONS[mimetype])
        bitstream.seek(0)
        self.zip.writestr(path, bitstream.read())
        return {'{%s}href' % NS['xlink']: path}


class Template(MarkupTemplate):

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

        self._handle_placeholders(tree)
        self._handle_images(tree)
        return StringIO(lxml.etree.tostring(tree))

    def _handle_placeholders(self, tree):
        """
        Will treat all placeholders tag (py:if/for/choose/when/otherwise)
        tags
        """
        # First we create the list of all the placeholders nodes.
        # If this is node matches a genshi directive it is put apart for
        # further processing.
        genshi_directives, placeholders = [], []
        for statement in tree.xpath('//text:placeholder', namespaces=NS):
            match_obj = GENSHI_TAGS.match(statement.text)
            if match_obj is not None:
                genshi_directives.append(statement)
            placeholders.append((statement, match_obj))

        # Then we match the opening and closing directives together
        idx = 0
        genshi_pairs, inserted = [], []
        for statement in genshi_directives:
            if not statement.text.startswith('</'):
                genshi_pairs.append([statement, None])
                inserted.append(idx)
                idx += 1
            else:
                genshi_pairs[inserted.pop()][1] = statement

        for p, match_obj in placeholders:
            if match_obj is not None:
                c_dir, directive, _, attr, a_val = match_obj.groups()
            else:
                c_dir, directive, _, attr, a_val = (None, p.text[1:-1], None,
                                                    None, None)

            if p in genshi_directives:
                # If the placeholder is a for statement:
                #    - we operate only on opening statement
                #    - we find the nearest ancestor of the closing and opening
                #      statement
                #    - we create a <py:for> node
                #    - we add all the node between the opening and closing
                #      statements to this new node
                #    - we replace the opening statement by the <py:for> node
                #    - we delete the closing statement

                if c_dir is not None:
                    continue
                for pair in genshi_pairs:
                    if pair[0] == p:
                        break
                opening, closing = pair

                o_ancestors = list(opening.iterancestors())
                c_ancestors = list(closing.iterancestors())
                for n in o_ancestors:
                    if n in c_ancestors:
                        ancestor = n
                        break

                genshi_node = lxml.etree.Element('{%s}%s' % (NS['py'],
                                                             directive),
                                                 attrib={attr: a_val},
                                                 nsmap=NS)
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
                p.attrib['{%s}replace' % NS['py']] = directive

    def _handle_images(self, tree):
        for draw in tree.xpath('//draw:frame', namespaces=NS):
            d_name = draw.attrib['{%s}name' % NS['draw']]
            if d_name.startswith('image: '):
                attr_expr = "make_href(%s, '%s')" % (d_name[7:], d_name[7:])
                attributes = {}
                attributes['{%s}attrs' % NS['py']] = attr_expr
                image_node = lxml.etree.Element('{%s}image' % NS['draw'],
                                                attrib=attributes,
                                                nsmap=NS)
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
