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
{
  "Records": [
    {
      "eventVersion": "2.0",
      "eventSource": "aws:s3",
      "awsRegion": "us-east-1",
      "eventTime": "2016-05-15T20:43:51.132Z",
      "eventName": "ObjectCreated:Put",
      "userIdentity": {
        "principalId": "AWS:AIDAJCCEM52KP7ZYERRBQ"
      },
      "requestParameters": {
        "sourceIPAddress": "63.116.216.254"
      },
      "responseElements": {
        "x-amz-request-id": "D1E402BC414B6E20",
        "x-amz-id-2": "xxx+yyy+Qk5iw="
      },
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "mmcdata_json_dev",
        "bucket": {
          "name": "dev.nrgretail-api",
          "ownerIdentity": {
            "principalId": "A2HL0J1LRYJEUK"
          },
          "arn": "arn:aws:s3:::dev.nrgretail-api"
        },
        "object": {
          "key": "api/nrg_residential/web/test_2016-05-15_1.json",
          "size": 45,
          "eTag": "26f94b539c8fc40b3cc679ccd9b47110",
          "sequencer": "005738DF870CCEADBA"
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
            worker = settings.SQS_WORKER_FUNCTIONS[kwargs['worker_name']]
            queue_name = worker['queue_name']
            argfunc = worker['argfunc']
            func = worker['function']
            if not callable(func):
                func = import_string(func)
            logger.info('getting queue: {}'.format(queue_name))
            queue = sqs.get_queue(queue_name)
            queue.set_message_class(RawMessage)
        except Exception:
            logger.exception('Error connecting to queue')
            sys.exit(1)

        count = 0

        while True:
            try:
                count += 1
                if count % 100 == 0:
                    logger.info('waiting for message, count {}'.format(count))
                message = queue.read(wait_time_seconds=20)  # max 20...
                if not message:
                    continue
            except Exception:
                logger.exception('Error reading message from queue %s', queue)
                continue

            try:
                logger.info('parsing --> {}'.format(message.get_body()))
                data = json.loads(message.get_body())
            except ValueError:
                logger.exception('Error processing message %s', message)
                continue

            try:
                args = argfunc(data)
                func(*args)
                message.delete()
            except Exception:
                logger.exception('Error processing message %s',
                                 message.get_body())
                message.delete()

            if kwargs.get('test') is True:
                break
