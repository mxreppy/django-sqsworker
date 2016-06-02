import json
import logging
import sys

import boto
from boto.sqs.message import RawMessage

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string


logger = logging.getLogger(__name__)

"""
Example S3 object message structure
{
  "Records": [
    {
      "eventVersion": "2.0",
      "eventSource": "aws:s3",
      "awsRegion": "us-east-1",
      "eventTime": "2016-05-15T20:43:51.132Z",
      "eventName": "ObjectCreated:Put",
      "userIdentity": {
        "principalId": "AWS:xxxxx"
      },
      "requestParameters": {
        "sourceIPAddress": "63.xx.xx.xx"
      },
      "responseElements": {
        "x-amz-request-id": "xxxx",
        "x-amz-id-2": "yyyyyy="
      },
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "stuff",
        "bucket": {
          "name": "nonsense",
          "ownerIdentity": {
            "principalId": "xxx__yyy"
          },
          "arn": "arn:aws:s3:::stuff"
        },
        "object": {
          "key": "file/web/test_2016-05-15_1.json",
          "size": 45,
          "eTag": "cxkdfjkdjf",
          "sequencer": "zzzjkdjfd"
        }
      }
    }
  ]
}
"""


class Command(BaseCommand):

    help = 'Run worker to poll SQS queue'

    def add_arguments(self, parser):
        parser.add_argument('worker_name', type=str)

    def handle(self, *args, **kwargs):
        try:
            logger.info(
                'sqsworker starting: {}'.format(kwargs['worker_name']))

            sqs = boto.connect_sqs()

            # setting must define a worker matching our invocation param
            worker = settings.SQS_WORKER_FUNCTIONS[kwargs['worker_name']]

            # these settings are required
            queue_name = worker['queue_name']
            argfunc = worker['argfunc']
            func = worker['function']

            # optional
            queue_account = worker.get('queue_account')
            delete_on_fail = worker.get('delete_on_failure', False)

            if not callable(func):
                func = import_string(func)
            logger.info('getting queue: {}'.format(queue_name))
            queue = sqs.get_queue(queue_name,
                                  owner_acct_id=queue_account)
            if queue:
                queue.set_message_class(RawMessage)
            else:
                logger.error('could not get queue for name %s account %s' %
                             (queue_name, queue_account))
                sys.exit(1)

        except Exception:
            logger.exception('Error connecting to queue')
            sys.exit(1)

        self.count = 0

        while True:
            self.process_message(argfunc, delete_on_fail, func, queue)

            if kwargs.get('test') is True:
                break

    def process_message(self, argfunc, delete_on_fail, func, queue):
        try:
            self.count += 1
            if self.count % 1000 == 0:
                logger.info('waiting for message, count {}'.format(self.count))
            message = queue.read(wait_time_seconds=20)  # max 20...
            if not message:
                return

        except Exception:
            logger.exception('Error reading message from queue %s', queue)
            return

        try:
            logger.info('parsing --> {}'.format(message.get_body()))
            data = json.loads(message.get_body())
        except ValueError:
            logger.exception('Error processing message %s', message)
            return

        try:
            args = argfunc(data)
            func(*args)
            message.delete()
        except Exception:
            logger.exception('Error processing message %s',
                             message.get_body())
            if delete_on_fail:
                logger.info('deleting message')
                message.delete()
