# -*- coding: utf-8 -*-
import gc
import sys
import unittest
from markupsafe import Markup, escape, escape_silent
from markupsafe._compat import text_type


class MarkupTestCase(unittest.TestCase):

    def test_adding(self):
        # adding two strings should escape the unsafe one
        unsafe = '<script type="application/x-some-script">alert("foo");</script>'
        safe = Markup('<em>username</em>')
        assert unsafe + safe == text_type(escape(unsafe)) + text_type(safe)

    def test_string_interpolation(self):
        # string interpolations are safe to use too
        assert Markup('<em>%s</em>') % '<bad user>' == \
               '<em>&lt;bad user&gt;</em>'
        assert Markup('<em>%(username)s</em>') % {
            'username': '<bad user>'
        } == '<em>&lt;bad user&gt;</em>'

        assert Markup('%i') % 3.14 == '3'
        assert Markup('%.2f') % 3.14 == '3.14'

    def test_type_behavior(self):
        # an escaped object is markup too
        assert type(Markup('foo') + 'bar') is Markup

        # and it implements __html__ by returning itself
        x = Markup("foo")
        assert x.__html__() is x

    def test_html_interop(self):
        # it also knows how to treat __html__ objects
        class Foo(object):
            def __html__(self):
                return '<em>awesome</em>'
            def __unicode__(self):
                return 'awesome'
            __str__ = __unicode__
        assert Markup(Foo()) == '<em>awesome</em>'
        assert Markup('<strong>%s</strong>') % Foo() == \
               '<strong><em>awesome</em></strong>'

    def test_tuple_interpol(self):
        self.assertEqual(Markup('<em>%s:%s</em>') % (
            '<foo>',
            '<bar>',
        ), Markup(u'<em>&lt;foo&gt;:&lt;bar&gt;</em>'))

    def test_dict_interpol(self):
        self.assertEqual(Markup('<em>%(foo)s</em>') % {
            'foo': '<foo>',
        }, Markup(u'<em>&lt;foo&gt;</em>'))
        self.assertEqual(Markup('<em>%(foo)s:%(bar)s</em>') % {
            'foo': '<foo>',
            'bar': '<bar>',
        }, Markup(u'<em>&lt;foo&gt;:&lt;bar&gt;</em>'))

    def test_format_args(self):
        self.assertTrue(isinstance(Markup('{0}').format(1), Markup))
        self.assertEqual(Markup('<em>{0:X}:{1:1.2f}</em>').format(
            15,
            0.9999,
        ), Markup(u'<em>F:1.00</em>'))
        
        self.assertEqual(Markup('<em>{0}:{1}</em>').format(
            '<foo>',
            Markup('<bar>'),
        ), Markup(u'<em>&lt;foo&gt;:<bar></em>'))

        # positional argument specifiers can be ommited
        # in Python 2.7 and later
        if sys.version_info >= (2, 7):
            self.assertEqual(Markup('<em>{}:{}</em>').format(
                '<foo>',
                Markup('<bar>'),
            ), Markup(u'<em>&lt;foo&gt;:<bar></em>'))

    def test_format_kwargs(self):
        self.assertEqual(Markup('<em>{foo}:{bar}</em>').format(
            foo='<foo>',
            bar=Markup('<bar>'),
        ), Markup(u'<em>&lt;foo&gt;:<bar></em>'))

        class Bar(object):
            def __init__(self, bar):
                self.bar = bar

        self.assertEqual(Markup('<em>{foo[0][foo]}:{bar.bar}</em>').format(
            foo=[{'foo': '<foo>'}],
            bar=Bar(Markup('<bar>')),
        ), Markup(u'<em>&lt;foo&gt;:<bar></em>'))
        
    def test_escaping(self):
        # escaping and unescaping
        assert escape('"<>&\'') == '&#34;&lt;&gt;&amp;&#39;'
        assert Markup("<em>Foo &amp; Bar</em>").striptags() == "Foo & Bar"
        assert Markup("&lt;test&gt;").unescape() == "<test>"

    def test_all_set(self):
        import markupsafe as markup
        for item in markup.__all__:
            getattr(markup, item)

    def test_escape_silent(self):
        assert escape_silent(None) == Markup()
        assert escape(None) == Markup(None)
        assert escape_silent('<foo>') == Markup(u'&lt;foo&gt;')

    def test_splitting(self):
        self.assertEqual(Markup('a b').split(), [
            Markup('a'),
            Markup('b')
        ])
        self.assertEqual(Markup('a b').rsplit(), [
            Markup('a'),
            Markup('b')
        ])
        self.assertEqual(Markup('a\nb').splitlines(), [
            Markup('a'),
            Markup('b')
        ])

    def test_mul(self):
        self.assertEqual(Markup('a') * 3, Markup('aaa'))


class MarkupLeakTestCase(unittest.TestCase):

    def test_markup_leaks(self):
        counts = set()
        for count in range(20):
            for item in range(1000):
                escape("foo")
                escape("<foo>")
                escape(u"foo")
                escape(u"<foo>")
            counts.add(len(gc.get_objects()))
        assert len(counts) == 1, 'ouch, c extension seems to leak objects'


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MarkupTestCase))

    # this test only tests the c extension
    if not hasattr(escape, 'func_code'):
        suite.addTest(unittest.makeSuite(MarkupLeakTestCase))

    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')

# vim:sts=4:sw=4:et:
