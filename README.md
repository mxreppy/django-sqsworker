# django-sqsworker

_A simple django management command to connect to sqs_


## temporary documentation
**Incomplete**

**may not work yet**

quickie developer instuctions, as this is being postponed as of 06-02-2016 as an active working item

* check out this repo
* in environment of other project wishing to use this package
	* activate that venv
	* cd to `django-sqsworker` checkout, folder `django-sqsworker`
	* execute `python setup.py develop`
	* cd back to project
	* execute `pip install django-sqsworker==0.1.0`
	* follow the rest of the docs more or less, ask if you have questions

_may the sqs-force be with you..._

	
## rest of documentation

Version 0.1.0

May 30, 2016

Mikey Reppy, mgpr@abacalab.com

https://github.com/mxreppy/django-sqsworker

# SQS Worker

The `sqsworker` Django app maps SQS queues to Python functions. The configuration requires `settings.SQS_WORKER_FUNCTIONS` to be defined. `settings.SQS_WORKER_FUNCTIONS` is a dictionary. The root-level key indicates the name of a worker (e.g. `receive_payment`). The value should be a dictionary that defines:

* `queue_name` - The name of an SQS queue available via boto credentials (e.g. `'ReceivedPayment'`)
* `function` - A string to the module and function messages from that queue should trigger (e.g. `'pricing.workers.receive_payment'`)
* `argfunc` - A function for mapping the message data into arguments for the function (e.g. `lambda body: (body['Records'][0]['s3']['object']['key'], 4)`)
* (Optional) `queue_account` - the account number of the AWS account that owns the queue, needed if the receiver will run in another AWS account's resource space (e.g. `1122334455`)
* (Optional) `delete_on_failure` - Boolean.  If the worker is to delete a message from the queue if the processing failed (raised an Exception of any kind).  Default is `False`, to leave error messages on the queue.  

## Installation

1.   `pip install django-sqsworker`
2.   Add `sqsworker` to `INSTALLED_APPS`. 

## Usage

To run a worker, use:

	python manage.py sqsworker <WORKER_NAME>
	
This will start a process that long-polls SQS and runs a function for each result. It will delete messages that do not error out.  In this version, messages which generate errors will also be deleled with full exception logging.  A future version will allow specified redrive policies for bad messages.

## Queue Configuration

You'll need an AWS SQS queue per worker that's accessible via boto credentials. Any message that doesn't throw an error during processing will be deleted.

**Note:** You'll want to configure a redrive policy and a dead letter queue if your worker will not be able to handle all messages eventually.

## Example Configuration

The following setup is built to handle S3 update SQS events. `get_s3_key_and_bucket_name` will return a tuple of the S3 key and S3 bucket name.

Exceptions thrown in the `argfunc` and `function` are caught and will result in a message failing and being deleted. The error will be logged.

from **settings.py**:

	def get_s3_key_and_bucket_name(body):
	    return (body['Records'][0]['s3']['object']['key'],
	            body['Records'][0]['s3']['bucket']['name'])
	
	
	SQS_WORKER_FUNCTIONS = {
	    'worker1': {
	        'queue_name': 'MyQueueName',
	        'function': 'myapp.workers.process_queue_item',
	        'argfunc': get_s3_key_and_bucket_name,
	    },
	    'worker2': {
	        'queue_name': 'ADifferentQueue',
	        'function': 'myapp.workers.process_different_queue_item',
	        'argfunc': get_s3_key_and_bucket_name,
	    },
	}
	
## Elastic Beanstalk Supervisor Configuration

If you are deploying this worker using Elastic Beanstalk, there is a template in the app that's designed to work with `django-makeconf`.

To configure workers as part of your deployment, add `sqsworker` to `MAKECONF_EB_MODULES` to generate a supervisor configuration that includes a process for each worker defined in `settings.py`.

This will configure workers for each defined queue (from `settings.SQS_WORKER_FUNCTIONS`) that restart on code deploy.

## To Do

* Add `kwargfunc` to support keyword arguments in additional to the positional arguments supported by `argfunc`
* Support non-JSON message formats
* Automatically process / discard SQS test messages

## History/Contributors
* original by Ethan McCreadie ([github page](https://github.com/ethanmcc)) for a private corporate project May 2016
* updated for a second private corporate project by M. Reppy, May 2016
* packaged for public release 2016-05-30, M. Reppy

## Notes

* Package structure created with [cookiecutter](http://www.pydanny.com/how-to-create-installable-django-packages.html)

```
$ cookiecutter https://github.com/pydanny/cookiecutter-djangopackage.git
Cloning into 'cookiecutter-djangopackage'...
remote: Counting objects: 728, done.
remote: Total 728 (delta 0), reused 0 (delta 0), pack-reused 728
Receiving objects: 100% (728/728), 110.88 KiB | 0 bytes/s, done.
Resolving deltas: 100% (406/406), done.
Checking connectivity... done.
full_name [Your full name here]: Mikey Reppy
email [you@example.com]: mgpr@abacalab.com
github_username [yourname]: mxreppy
project_name [dj-package]: django-sqsworker
repo_name [dj-package]: django-sqsworker
app_name [djpackage]: sqsworker
project_short_description [Your project description goes here]: SQS receiver for django
models [Comma-separated list of models]: 
release_date [2016-05-30]: 
year [2016]: 
version [0.1.0]:
```