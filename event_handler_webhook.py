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

    # See https://meta.discourse.org/t/setting-up-webhooks/49045
    # See also https://forum.506investorgroup.com/admin/api/web_hooks

    # This handler handles new topics and flags the new topic for moderator review.
    # Mods will verify it has the right tags, is in the right category, etc.

    event_type = request.headers['X-Discourse-Event-Type']
    event = request.headers['X-Discourse-Event']
    print 'event: ', event

    # Any checks for category are best done in the webhook settings
    if event_type == 'topic' and event == 'topic_created':

        topic = request.json['topic']

        # Checks to make sure it's a normal public topic, not a PM or system message
        created_by = topic['created_by']['username']
        archetype = topic['archetype']
        user_id = topic['user_id']

        # Just the first check should be sufficient. User ID > 0 excludes system and discobot.
        if str(archetype) == 'regular' and user_id > 0:
            tags = topic.get('tags', [])
            topic_id = topic['id']
            title = topic['title']
            slug = topic['slug']
            # Could edit the webhook to deliver only Deals category
            # category_id = topic['category_id']
            url = "https://forum.506investorgroup.com/t/%s/%d" % (slug, topic_id)

            msg = '**[How to Review a New Topic](https://forum.506investorgroup.com/t/moderators-reviewing-each-new-topic/18317)**  ' \
                  '@%s created a new topic: \"%s\".  ' \
                  'Review here: %s.  ' % \
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


@app.route('/post_event', methods=['POST'])
def post_event_handler():

    # This handler handles new posts. If the post appears to contain wiring instructions,
    # flag the new topic for moderator review. Mods will add a staff notice warning about
    # wiring scams, if appropriate. This check does not need to be perfect- it can never
    # be perfect and it's easy enough for mods to ignore any false alarms.

    event_type = request.headers['X-Discourse-Event-Type']
    event = request.headers['X-Discourse-Event']
    print 'event: ', event

    # Any checks for category are best done in the webhook settings
    if event_type == 'post' and event == 'post_created':

        post = request.json['post']

        # Checks to make sure it's a normal public topic, not a PM or system message
        created_by = post['username']
        post_type = post['post_type']  # 1 is "regular". Does that exclude PMs? Need to test.

        if post_type == 1:
            cooked = post['cooked']



            # tags = topic.get('tags', [])
            # topic_id = topic['id']
            # title = topic['title']
            # slug = topic['slug']
            # # Could edit the webhook to deliver only Deals category
            # # category_id = topic['category_id']
            # url = "https://forum.506investorgroup.com/t/%s/%d" % (slug, topic_id)
            #
            # msg = '**[How to Review a New Topic](https://forum.506investorgroup.com/t/moderators-reviewing-each-new-topic/18317)**  ' \
            #       '@%s created a new topic: \"%s\".  ' \
            #       'Review here: %s.  ' % \
            #       (created_by, title, url)

            msg = 'Interpret this'

            send_simple_email('markschmucker@yahoo.com', event, msg)

            # client = create_client(1)
            # post = client.post(topic_id, 1)
            # post_id = post['post_stream']['posts'][0]['id']
            #
            # # Note the flag method is currently added to client.py, not a subclass client506.py.
            # client.flag(post_id, msg)

        return '', 200
    else:
        return '', 400


if __name__ == "__main__":
    # Digests use 8081, forms use 8082, tracking_pixel and resourse server use 8083,
    # not sure if either of those two on 8083 are running; run this on 8084 (it's open).
    app.run(host="0.0.0.0", port=8085, debug=True, threaded=True)
