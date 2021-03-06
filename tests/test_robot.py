# -*- coding: utf-8 -*-
"""
    robo.tests.test_robot
    ~~~~~~~~~~~~~~~~~~~~~

    Robot tests.


    :copyright: (c) 2014 Shinya Ohyanagi, All rights reserved.
    :license: BSD, see LICENSE for more details.
"""
import os
import logging
from blinker import Signal
from unittest import TestCase
from robo.robot import PluginLoader, Robot


class TestPluginLoader(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loader = PluginLoader('tests.fixtures')
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'fixtures')
        cls.fixture_path = path

    def test_list_plugins(self):
        """ PluginLoader().list_plugins() should list plugins. """
        paths = self.loader.list_plugins(searchpath=[self.fixture_path])
        self.assertEqual(paths, ['bar', 'foo'])

    def test_load_foo(self):
        """ PluginLoader().load_plugin('foo') should load `foo` module. """
        plugin = self.loader.load_plugin('foo')
        self.assertEqual(plugin.__name__, 'tests.fixtures.foo')

    def test_load_bar(self):
        """ PluginLoader().load_plugin('bar') should load `bar` module. """
        plugin = self.loader.load_plugin('bar')
        self.assertEqual(plugin.__name__, 'tests.fixtures.bar')

    def test_load_fail(self):
        """ PluginLoader().load_plugin('nomoudle') should raise ImportError. """
        with self.assertRaises(ImportError):
            self.loader.load_plugin('nomodule')


class TestRobot(TestCase):
    @classmethod
    def setUpClass(cls):
        logger = logging.getLogger('robo')
        logger.level = logging.ERROR
        cls.robot = Robot('test', logger)

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'fixtures')
        handler_path = os.path.join(path, 'handlers')
        cls.robot.setup_handlers(handler_path, 'tests.fixtures.handlers')

        cls.robot.load_adapter('null', 'tests.fixtures.adapters')

    def test_should_contains_signal(self):
        """ Robot() should contains signal. """
        self.assertTrue(isinstance(self.robot.handler_signal, Signal))

    def test_should_parse_handler_class(self):
        """ Robot().parse_handler_methods() should parse given instance. """
        from tests.fixtures.handlers.foo import Foo
        ret = self.robot.parse_handler_methods(Foo())
        self.assertEqual(len(ret), 7)

    def test_should_setup_handlers(self):
        """ Robot().setup_handlers() should setup handlers. """
        self.assertEqual(self.robot.handlers[0]['method'], 'goodbye')
        self.assertEqual(self.robot.handlers[1]['method'], 'goodbye2')
        self.assertEqual(self.robot.handlers[2]['method'], 'goodbye3')
        self.assertEqual(self.robot.handlers[3]['method'], 'hello')
        self.assertEqual(self.robot.handlers[4]['method'], 'hi')

    def test_should_handlers_contains_handler_instance(self):
        """ Robot().handlers should contains instance. """
        from tests.fixtures.handlers.foo import Foo
        self.assertTrue(isinstance(self.robot.handlers[0]['instance'], Foo))

    def test_should_handlers_contains_handler_methods(self):
        """ Robot().handlers should contains handler method. """
        self.assertEqual(self.robot.handlers[0]['method'], 'goodbye')

    def test_should_handlers_contains_regex(self):
        """ Robot().handlers should contains regexs object. """
        self.assertEqual(self.robot.handlers[0]['regex'].pattern, '^goodbye')

    def test_should_handlers_contains_kwargs(self):
        """ Robot().handlers should contains kwargs. """
        self.assertEqual(self.robot.handlers[0]['kwargs'],
                         {'regex': '^goodbye', 'room': '^@random'})

    def test_shoudl_contains_handlers_docs(self):
        """ Robot().docs should contains handler's docs. """
        self.assertEqual(len(self.robot.docs), 7)

    def test_handlers_docs_contains_description_and_pattern(self):
        """ Robot().docs should contains description and pattern. """
        self.assertEqual(self.robot.docs[4]['description'], 'test hi')
        self.assertEqual(self.robot.docs[4]['pattern'], '^hi')

    def test_should_register_default_handlers(self):
        """ Robot().register_default_handlers() should register default packages. """
        self.robot.register_default_handlers()
        self.assertEqual(self.robot.handlers[7]['instance'].__module__,
                         'robo.handlers.echo')

    def test_subscriber_should_receive_unicode_text(self):
        """ Robot().handler_subscriber() should receive unicode message. """
        message = u'test hi \xe3\x81\x82\xe3\x81\x84\xe3\x81\x86'
        self.robot.handler_signal.send(message)
        self.assertEqual(self.robot.adapters['null'].responses[0], 'hi')
        self.robot.adapters['null'].responses = []

    def test_should_load_adapter(self):
        """ Robot().load_adapter() should setup adapters. """
        from tests.fixtures.adapters.null import Null
        self.assertTrue(isinstance(self.robot.adapters['null'], Null))

    def test_adapter_should_contains_signal(self):
        """ Robot().adapter should contains signal. """
        self.assertTrue(isinstance(self.robot.adapters['null'].signal, Signal))

    def test_robot_triggered(self):
        """ Robot should triggered when given message was started with robot name. """
        self.robot.handler_signal.send('test hi foo')
        self.assertEqual(self.robot.adapters['null'].responses[0], 'hi')
        self.robot.adapters['null'].responses = []

    def test_robot_not_triggered(self):
        """ Robot should not triggered when given message was not started with robot name. """
        self.robot.handler_signal.send('tests hi foo')
        self.assertEqual(self.robot.adapters['null'].responses, [])

    def test_handler_triggered_when_regex_matched(self):
        """ Handler should triggered when given message matched. """
        self.robot.handler_signal.send('test hi foo')
        self.assertEqual(self.robot.adapters['null'].responses[0], 'hi')
        self.robot.adapters['null'].responses = []

    def test_handler_not_triggered_when_regex_not_matched(self):
        """ Handler should not triggered when given message was not matched. """
        self.robot.handler_signal.send('test foo')
        self.assertEqual(self.robot.adapters['null'].responses, [])

    def test_handler_triggered_when_room_regex_matched(self):
        """ Handler should triggered when room is matched. """
        self.robot.handler_signal.send('test goodbye', room='@random')
        self.assertEqual(self.robot.adapters['null'].responses,
                         ['goodbye @random', 'goodbye all'])
        self.robot.adapters['null'].responses = []

    def test_handler_triggered_when_room_regex_was_not_described(self):
        """ Handler should triggered when room is matched. """
        self.robot.handler_signal.send('test goodbye', room='@test')
        self.assertEqual(self.robot.adapters['null'].responses, ['goodbye all'])
        self.robot.adapters['null'].responses = []

    def test_handler_triggered_when_missing_is_true(self):
        """ Handler should triggered when missing is True and other regex is not matched. """
        self.robot.handler_signal.send('test foobarbaz', room='missing')
        self.assertEqual(self.robot.adapters['null'].responses, ['missing1'])
        self.robot.adapters['null'].responses = []

    def test_handler_not_triggered_when_regex_was_matched(self):
        """ Handler should not triggered when regex was matched even if missing is true. """
        self.robot.handler_signal.send('test foo', room='missing')
        self.assertEqual(self.robot.adapters['null'].responses, ['missing2'])
        self.robot.adapters['null'].responses = []

    def test_hander_should_shutdown(self):
        """ Handelr should shutdown if handler contains shutdown method. """
        self.robot.shutdown()
        self.assertEqual(self.robot.handlers[0]['instance'].response,
                         'shutdown')

    def test_handler_should_contains_signal(self):
        """ Handelr should contains signal object if signal property exists. """
        self.assertIsNotNone(self.robot.handlers[0]['instance'].signal)

    def test_handler_should_contains_options(self):
        """ Handelr should contains options if options property exists. """
        logger = logging.getLogger('robo')
        logger.level = logging.ERROR
        options = {'foo': 'bar'}
        robot = Robot('test', logger, **options)

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'fixtures')
        handler_path = os.path.join(path, 'handlers')
        robot.setup_handlers(handler_path, 'tests.fixtures.handlers')
        robot.load_adapter('null', 'tests.fixtures.adapters')
        self.assertEqual(robot.handlers[0]['instance'].options, options)

    def test_adapter_should_triggered(self):
        """ Adapter should triggered when given message was matched. """
        self.robot.handler_signal.send('test hi foo')
        self.assertEqual(self.robot.adapters['null'].responses, ['hi'])
        self.robot.adapters['null'].responses = []

    def test_notofy_to_adapter_send_message(self):
        """ Robot().notify_to_adapter() should send message to adapter. """
        self.robot.notify_to_adapter('hello')
        self.assertEqual(self.robot.adapters['null'].responses, ['hello'])
        self.robot.adapters['null'].responses = []
