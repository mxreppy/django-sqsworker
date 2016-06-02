#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-sqsworker
------------

Tests for `django-sqsworker` models module.
"""

from django.test import TestCase
from django.test import override_settings

from boto import connect_sqs
from moto import mock_sqs

from sqsworker.management.commands import sqsworker


def argfunc_example(data):
    return data.keys()


_keys_expected = [
    'a',
    'b'
]


def function_example(keys):
    assert keys == _keys_expected

    return True


class TestSqsworker(TestCase):
    def setUp(self):
        self.command = sqsworker.Command()

    @override_settings(
        SQS_WORKER_FUNCTIONS={
            'test_worker': {
                'queue_name': 'my_queue',
                'argfunc': 'tests.test_commands.argfunc_example',
                'function': 'tests.test_commands.function_example',
            }
        }
    )
    @mock_sqs
    def test_connect(self):
        conn = connect_sqs()
        conn.create_queue('my_queue')

        # tests coming
        # assert True is False, "testing"

    def tearDown(self):
        pass
