"""Hidden acceptance tests for issue 3 (feature, reused from A2 task T2): piped wikilinks `[[Target|Label]]`.

Run from the root of a run copy:  python -m unittest discover -s <this dir> -p test_issue3.py -t <this dir>
"""
import unittest

import markdown
from markdown.extensions.wikilinks import WikiLinkExtension


class TestIssue3PipedWikiLinks(unittest.TestCase):

    def test_piped_label(self):
        self.assertEqual(
            markdown.markdown('See [[Target Page|click here!]] now.', extensions=['wikilinks']),
            '<p>See <a class="wikilink" href="/Target_Page/">click here!</a> now.</p>'
        )

    def test_config_build_url_and_meta_still_apply(self):
        calls = []

        def my_url(label, base, end):
            calls.append(label)
            return '{}{}{}'.format(base, label.lower().replace(' ', '-'), end)

        html = markdown.markdown(
            '[[Some Page|the label]]',
            extensions=[WikiLinkExtension(base_url='/wiki/', end_url='.html', html_class='wl', build_url=my_url)]
        )
        self.assertEqual(html, '<p><a class="wl" href="/wiki/some-page.html">the label</a></p>')
        self.assertEqual(calls, ['Some Page'])  # build_url receives the target, not the label

        html = markdown.markdown(
            'wiki_base_url: http://example.com/\nwiki_end_url: .htm\nwiki_html_class:\n\n[[Some Page|Label]]',
            extensions=['meta', 'wikilinks']
        )
        self.assertEqual(html, '<p><a href="http://example.com/Some_Page.htm">Label</a></p>')

    def test_whitespace_and_empty_label(self):
        self.assertEqual(
            markdown.markdown('[[ Target Page | My Label ]]', extensions=['wikilinks']),
            '<p><a class="wikilink" href="/Target_Page/">My Label</a></p>'
        )
        self.assertEqual(
            markdown.markdown('[[Target Page|]] and [[Target Page| ]]', extensions=['wikilinks']),
            '<p><a class="wikilink" href="/Target_Page/">Target Page</a> and '
            '<a class="wikilink" href="/Target_Page/">Target Page</a></p>'
        )

    def test_mixed_with_plain_links_and_code(self):
        # Plain wikilinks keep working next to piped ones; code spans and disabled extension are untouched.
        self.assertEqual(
            markdown.markdown('[[Plain Link]], [[Other Page|other]] and `[[A|B]]`', extensions=['wikilinks']),
            '<p><a class="wikilink" href="/Plain_Link/">Plain Link</a>, '
            '<a class="wikilink" href="/Other_Page/">other</a> and <code>[[A|B]]</code></p>'
        )
        self.assertEqual(
            markdown.markdown('[[A|B]]'),
            '<p>[[A|B]]</p>'
        )


if __name__ == '__main__':
    unittest.main()
