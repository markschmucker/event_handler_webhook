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

        # msg = '%d %s %s' % (user_id, username, email)
        msg = '%s created a new Deal topic \"%s\" with tags %s. ' \
              'If it does not have a deal status tag or other required tags, please add them at %s.' % \
              (created_by, title, tags, url)

        send_simple_email('markschmucker@yahoo.com', event, msg)

        client = create_client(1)
        # how to create notification or post? pydiscourse has create_post where you can
        # give it a category id or topic id. So maybe create a topic Tags to Check in
        # category staff and create a new post there each time.
        # Or the review queue would be the right way.
        # I added flag() to client.py, but the way I reversed-engineered it wants a post_id,
        # but here I want to handle a topic event and I don't easily have the post id. It
        # might work though passing a post_id and setting flag_topic = True. If not, will
        # need to first get posts in topic id (there will only be one), then flag the post id.
        # No that didn't work- need to get post_id.

        # This might work- haven't committed, too tired. And now that I have the post id,
        # flagging the topic might work and be a little better.
        post = client.post(topic_id, 1)
        post_id = post['post_stream']['posts'][0]['id']
        print "flagging post id %d" % post_id
        client.flag(post_id, msg)

        return '', 200
    else:
        return '', 400


if __name__ == "__main__":
    # Digests use 8081, forms use 8082, tracking_pixel and resourse server use 8083,
    # not sure if either of those two on 8083 are running; run this on 8084 (it's open).
    app.run(host="0.0.0.0", port=8085, debug=True, threaded=True)
