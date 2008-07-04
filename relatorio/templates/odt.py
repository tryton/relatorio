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

__revision__ = "$Id: odt.py 4 2008-07-04 18:13:58Z nicoe $"
__metaclass__ = type

import os
import re
import zipfile
from cStringIO import StringIO

import lxml.etree
from genshi.template import Template as GenshiTemplate, MarkupTemplate

NS = {'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
      'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
      'py': 'http://genshi.edgewall.org/',
      }
GENSHI_TAGS = re.compile(r'<(/)?(for|choose|otherwise|when|if|with)( (\w+)="(.*)"|)>')


class Template(GenshiTemplate):

    def __init__(self, source, filepath=None, filename=None, loader=None,
                 encoding=None, lookup='strict', allow_exec=True):
        inzip = zipfile.ZipFile(filepath)
        content = inzip.read('content.xml')
        inzip.close()
        self.content_template = MarkupTemplate(self.add_directives(content))
        super(Template, self).__init__(source, filepath, filename, loader,
                                       encoding, lookup, allow_exec)

    def _parse(self, source, encoding):
        pass

    def _prepare(self, stream):
        return []

    def add_directives(self, content):
        tree = lxml.etree.parse(StringIO(content))
        root = tree.getroot()

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
        return lxml.etree.tostring(tree)

    def generate(self, *args, **kwargs):
        content = str(self.content_template.generate(*args, **kwargs))
        new_oo = StringIO()
        inzip = zipfile.ZipFile(self.filepath)
        outzip = zipfile.ZipFile(new_oo, 'w')

        for f in inzip.infolist():
            if f.filename == 'content.xml':
                s = StringIO()
                s.write(str(content))
                outzip.writestr('content.xml', s.getvalue())
            else:
                outzip.writestr(f, inzip.read(f.filename))
        inzip.close()
        outzip.close()

        return new_oo

