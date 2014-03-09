"""
iodized's grinder.

A simple daemon to convert iodized's json to salt states.

Currently supported commands are:
  salt_states: List all salt states
  salt_version: Print out salt's version

Usage:
  grinder (salt_states|salt_version)
  grinder --daemon
"""
import json
import inspect
import salt
from docopt import docopt
import pika
import logging

LOGO = """                 _           _
  __ _ _ __ _ __(_)_ __   __| | ___ _ __ _ __
 / _` | '__| '__| | '_ \ / _` |/ _ \ '__| '__|
| (_| | |  | |  | | | | | (_| |  __/ |  | |
 \__, |_|  |_|  |_|_| |_|\__,_|\___|_|  |_|
 |___/"""

log = logging.getLogger(__name__)


def get_salt_states():
    """
    Return a tuple of salt state and state parameters
    """
    l = salt.loader._create_loader({"extension_modules": ""},
                                   'modules',
                                   'module')
    return sorted([(k, inspect.getargspec(v).args) for k, v
                   in l.gen_functions().items()], key=lambda i: i[0])


def main():
    arguments = docopt(__doc__, version='grinder 0.0.1')
    if arguments["salt_states"]:
        for state, parameters in get_salt_states():
            print "%s: %s" % (state, parameters)
    elif arguments["salt_version"]:
        print "salt version is", salt.__version__
    elif arguments["--daemon"]:
        daemon()
    else:
        pass


class IRPC:
    @staticmethod
    def evens():
        return [2, 4, 6, 8]

    @staticmethod
    def odds():
        return [1, 3, 5, 7]


def callback(ch, method, properties, body):
    reply_to = properties.reply_to
    log.debug("Message received: %r, reply_to: %s", body, reply_to)

    # Parse the JSON
    try:
        body = json.loads(body)
    except ValueError:
        log.error("Not a valid JSON")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    if not type(body) == dict:
        log.warn("JSON is not a dict")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Check of this is known function call
    if "fn" in body:
        fn = body["fn"]
        if not hasattr(IRPC, fn):
            log.warn("Unknown function name %s", fn)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        else:
            pass
    else:
        log.warn("Not a function call")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    log.debug("Calling %s()", fn)

    f = getattr(IRPC, body["fn"])
    response_body = json.dumps(f())
    log.debug("Posting reply %s to %s", response_body, reply_to)

    ch.basic_publish(exchange='',
                     routing_key=reply_to,
                     body=response_body)

    ch.basic_ack(delivery_tag=method.delivery_tag)


def daemon():
    print LOGO
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('grinder').addHandler(console)

    exchange_name = "pepper"
    queue_name = "grinder"

    connection = pika.BlockingConnection(pika.ConnectionParameters(
                                         host='localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name, type='direct')
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange=exchange_name, queue=queue_name,
                       routing_key=queue_name)
    channel.basic_consume(callback, queue=queue_name, no_ack=False)

    log.info("grinder is ready to GRIND")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        log.info("grinder won't grind anymore.. bye")
