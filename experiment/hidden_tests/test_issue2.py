"""Hidden acceptance tests for issue 2 (bug): RecursionError on deeply nested lists.

Taken from the upstream fix, commit 7d0d95a (tests/test_syntax/blocks/test_list_nesting.py).
Run from the root of a checkout:  python -m unittest discover -s <this dir> -p test_issue2.py -t <this dir>
"""
import textwrap
import unittest

import markdown


class TestIssue2ListNesting(unittest.TestCase):

    def test_deeply_nested_list_does_not_raise(self):
        result = markdown.markdown('- ' * 500 + 'x')
        self.assertLess(result.count('<ul>'), 500)
        self.assertIn('x', result)

    def test_deeply_nested_ordered_list_does_not_raise(self):
        result = markdown.markdown('1. ' * 500 + 'x')
        self.assertLess(result.count('<ol>'), 500)
        self.assertIn('x', result)

    def test_deeply_indented_list_does_not_raise(self):
        source = ''.join('  ' * i + '- x\n' for i in range(600))
        result = markdown.markdown(source)
        self.assertLess(result.count('<ul>'), 600)
        self.assertEqual(result.count('x'), 600)

    def test_nesting_below_the_limit_is_unchanged(self):
        source = textwrap.dedent("""\
            - x
                - y
                    - z
            """)
        expected = '<ul>\n<li>x<ul>\n<li>y<ul>\n<li>z</li>\n</ul>\n</li>\n</ul>\n</li>\n</ul>'
        self.assertEqual(markdown.markdown(source), expected)


if __name__ == '__main__':
    unittest.main()
