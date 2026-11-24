"""Hidden acceptance tests for issue 5 (vague): toc ids for non-Latin headings.

The issue is vague on purpose. These tests encode the underlying need (meaningful, unique,
linkable ids for non-Latin headings) and guard the existing behaviour for ASCII headings.
Run from the root of a checkout:  python -m unittest discover -s <this dir> -p test_issue5.py -t <this dir>
"""
import re
import unittest

import markdown


def ids(html):
    return re.findall(r'<h\d id="([^"]*)"', html)


class TestIssue5NonLatinToc(unittest.TestCase):

    def test_non_latin_headings_get_meaningful_ids(self):
        html = markdown.markdown('# नमस्ते दुनिया\n\n# Привет мир', extensions=['toc'])
        for i in ids(html):
            self.assertTrue(i, 'id must not be empty')
            self.assertIsNone(re.fullmatch(r'_\d+', i), 'id %r carries no meaning' % i)

    def test_toc_links_match_heading_ids(self):
        html = markdown.markdown('[TOC]\n\n# नमस्ते दुनिया\n\n## Привет мир', extensions=['toc'])
        hrefs = re.findall(r'<a href="#([^"]*)"', html)
        self.assertEqual(hrefs, ids(html))

    def test_duplicate_non_latin_headings_are_unique(self):
        found = ids(markdown.markdown('# Привет\n\n# Привет', extensions=['toc']))
        self.assertEqual(len(found), 2)
        self.assertNotEqual(found[0], found[1])

    def test_ascii_ids_unchanged(self):
        self.assertEqual(
            markdown.markdown('# Hello World!\n\n# Žluťoučký kůň', extensions=['toc']),
            '<h1 id="hello-world">Hello World!</h1>\n<h1 id="zlutoucky-kun">Žluťoučký kůň</h1>'
        )


if __name__ == '__main__':
    unittest.main()
