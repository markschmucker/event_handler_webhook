"""
A flask server to handle webhooks from Discourse.
"""

from flask import Flask, render_template, flash, request
import logging
import json
from pprint import pprint, pformat
from client506 import create_client
from ses import send_simple_email
from pydiscourse.exceptions import (
    DiscourseClientError
)

recipients = ['markschmucker@yahoo.com',]

logger = logging.getLogger('quiz_webhook')
file_handler = logging.FileHandler('quiz_webhook.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

logger.info('running quiz web hook server.py')

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d4jjf2b6176a'


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.route('/topic_event', methods=['POST'])
def topic_event_handler():

    # Currently we're only interested in topic_created. Other webhooks are available,
    # for users, topics, and posts. (However not for user_added_to_group). See
    # https://meta.discourse.org/t/setting-up-webhooks/49045. See webhook page.

    headers = request.headers
    pprint(headers)

    event = request.headers['X-Discourse-Event']
    print 'event: ', event

    #if event == 'user_created':
    if True:

        # user = request.json['user']
        #
        # user_id = user['id']
        # email = user['email']
        # username = user['username']
        # msg = '%d %s %s' % (user_id, username, email)

        send_simple_email('markschmucker@yahoo.com', event, request.json)

        client = create_client(1)
        # send notification here

        return '', 200
    else:
        return '', 400


if __name__ == "__main__":
    # Digests use 8081, forms use 8082, tracking_pixel and resourse server use 8083,
    # not sure if either of those two on 8083 are running; run this on 8084 (it's open).
    app.run(host="0.0.0.0", port=8085, debug=True, threaded=True)
