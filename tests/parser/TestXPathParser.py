# -*- coding: utf-8 -*-
import mock
import lumbermill.utils.DictUtils as DictUtils

from tests.ModuleBaseTestCase import ModuleBaseTestCase, MockLumberMill
from lumbermill.misc import Cache
from lumbermill.parser import XPathParser

class TestXPathParser(ModuleBaseTestCase):

    xml_string = """<?xml version="1.0" encoding="ISO-8859-1"?>

<bookstore>

<book category="COOKING">
  <title lang="en">Everyday Italian</title>
  <author>Giada De Laurentiis</author>
  <year>2005</year>
  <price>30.00</price>
</book>

<book category="CHILDREN">
  <title lang="en">Harry Potter</title>
  <author>J K. Rowling</author>
  <year>2005</year>
  <price>29.99</price>
</book>

<book category="WEB">
  <title lang="en">XQuery Kick Start</title>
  <author>James McGovern</author>
  <author>Per Bothner</author>
  <author>Kurt Cagle</author>
  <author>James Linn</author>
  <author>Vaidyanathan Nagarajan</author>
  <year>2003</year>
  <price>49.99</price>
</book>

<book category="WEB">
  <title lang="en">Learning XML</title>
  <author>Erik T. Ray</author>
  <year>2003</year>
  <price>39.95</price>
</book>

</bookstore>"""

    def setUp(self):
        super(TestXPathParser, self).setUp(XPathParser.XPathParser(MockLumberMill()))

    def testHandleData(self):
        self.test_object.configure({'source_field': 'agora_product_xml',
                                    'query': '//bookstore/book[@category="$(category)"]/title/text()'})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'agora_product_xml': self.xml_string,
                                               'category': 'COOKING'})
        for event in self.test_object.handleEvent(event):
            self.assertEquals(event['xpath_result'], ['Everyday Italian'])

    def testHandleDataWithTargetField(self):
        self.test_object.configure({'source_field': 'agora_product_xml',
                                    'target_field': 'book_title',
                                    'query': '//bookstore/book[@category="$(category)"]/title/text()'})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'agora_product_xml': self.xml_string,
                                               'category': 'COOKING'})
        for event in self.test_object.handleEvent(event):
            self.assertEquals(event['book_title'], ['Everyday Italian'])

    def testCache(self):
        cache = Cache.Cache(mock.Mock())
        cache.configure({})
        self.test_object.lumbermill.addModule('Cache', cache)
        self.test_object.configure({'source_field': 'agora_product_xml',
                                    'query': '//bookstore/book[@category="$(category)"]/title/text()',
                                    'cache': 'Cache',
                                    'cache_key': '$(category)'})
        self.checkConfiguration()
        event = DictUtils.getDefaultEventDict({'agora_product_xml': self.xml_string,
                                               'category': 'COOKING'})
        next(self.test_object.handleEvent(event))
        for event in self.test_object.handleEvent(event):
            self.assertEquals(event['xpath_result'], ['Everyday Italian'])
            self.assertTrue(event['lumbermill']['cache_hit'])
