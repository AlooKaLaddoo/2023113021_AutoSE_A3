"""Hidden acceptance tests for issue 4 (feature): `~~strikethrough~~` extension.

Run from the root of a checkout (after `pip install -e .`):
    python -m unittest discover -s <this dir> -p test_issue4.py -t <this dir>
"""
import unittest

import markdown


def md(src, ext=('strikethrough',)):
    return markdown.markdown(src, extensions=list(ext))


class TestIssue4Strikethrough(unittest.TestCase):

    def test_basic(self):
        self.assertEqual(md('~~gone~~ text'), '<p><del>gone</del> text</p>')

    def test_inline_markup_inside(self):
        self.assertEqual(
            md('~~**bold** and *em* and [a](/b)~~'),
            '<p><del><strong>bold</strong> and <em>em</em> and <a href="/b">a</a></del></p>'
        )

    def test_single_and_unclosed_tildes_left_alone(self):
        self.assertEqual(md('a ~b~ c ~~d'), '<p>a ~b~ c ~~d</p>')

    def test_off_by_default_and_not_in_code(self):
        self.assertEqual(markdown.markdown('~~x~~'), '<p>~~x~~</p>')
        self.assertEqual(md('`~~x~~`'), '<p><code>~~x~~</code></p>')


if __name__ == '__main__':
    unittest.main()
