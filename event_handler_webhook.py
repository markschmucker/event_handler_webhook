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

logger = logging.getLogger('event_webhook')
file_handler = logging.FileHandler('event_webhook.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

logger.info('running event web hook server.py')

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


    event_type = request.headers['X-Discourse-Event-Type']
    event = request.headers['X-Discourse-Event']
    print 'event: ', event

    # Any checks for category are best done in the webhook settings
    if event_type == 'topic' and event == 'topic_created':

        topic = request.json['topic']
        tags = topic['tags']
        topic_id = topic['id']
        title = topic['title']
        slug = topic['slug']
        # I will edit the webhook to deliver only Deals category, so I don't have to look up
        # the category by id.
        # category_id = topic['category_id']
        created_by = topic['created_by']['username']
        url = "https://forum.506investorgroup.com/t/%s/%d" % (slug, topic_id)

        msg = '**[How to Review a New Topic](https://forum.506investorgroup.com/t/moderators-reviewing-each-new-topic/18317)**  \s\s' \
              '@%s created a new topic: \"%s\".  \s\s' \
              'Review here: %s.  \s\s' % \
              (created_by, title, url)

        send_simple_email('markschmucker@yahoo.com', event, msg)

        client = create_client(1)
        post = client.post(topic_id, 1)
        post_id = post['post_stream']['posts'][0]['id']

        # Note the flag method is currently added to client.py, not a subclass client506.py.
        client.flag(post_id, msg)

        return '', 200
    else:
        return '', 400


if __name__ == "__main__":
    # Digests use 8081, forms use 8082, tracking_pixel and resourse server use 8083,
    # not sure if either of those two on 8083 are running; run this on 8084 (it's open).
    app.run(host="0.0.0.0", port=8085, debug=True, threaded=True)
