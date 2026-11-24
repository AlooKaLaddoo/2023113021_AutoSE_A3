"""Hidden acceptance tests for issue 1 (bug): toc crashes on a bare `{id}` attribute.

Tests 1-2 are the upstream tests from commit dc26ab5 (upstream issue #1705); 3-4 are ours.
Run from the root of a checkout:  python -m unittest discover -s <this dir> -p test_issue1.py -t <this dir>
"""
import unittest

import markdown


def md(src):
    return markdown.markdown(src, extensions=['toc', 'attr_list'])


class TestIssue1BareId(unittest.TestCase):
    maxDiff = None

    def test_bare_id_attribute(self):
        self.assertEqual(md('#d {id}'), '<h1 id="d">d</h1>')

    def test_bare_id_attribute_with_toc_marker(self):
        self.assertEqual(
            md('[TOC]\n\n# Heading One {id}'),
            '<div class="toc">\n<ul>\n<li><a href="#heading-one">Heading One</a></li>\n</ul>\n</div>\n'
            '<h1 id="heading-one">Heading One</h1>'
        )

    def test_explicit_id_still_kept(self):
        self.assertEqual(md('# Title {#my-id}'), '<h1 id="my-id">Title</h1>')

    def test_bare_ids_on_duplicate_headings_are_unique(self):
        self.assertEqual(md('# A {id}\n\n# A {id}'), '<h1 id="a">A</h1>\n<h1 id="a_1">A</h1>')


if __name__ == '__main__':
    unittest.main()
