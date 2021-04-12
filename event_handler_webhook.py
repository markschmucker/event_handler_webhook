"""
A flask server to handle webhooks from Discourse.
"""

from flask import Flask, render_template, flash, request
import logging
from client506 import create_client
from ses import send_simple_email
import re

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


def contains_wiring_info(s):
    """ Return True if s contains a wire-word and exactly 9 consecutive digits
    """
    s = s.lower()
    s += ' '  # sidestep any ending issues
    if 'wire' in s or 'wiring' in s or 'aba' in s or 'routing' in s:
        r = r'[^\d]\d{9}[^\d]'
        x = re.findall(r, s)
        return bool(x)
    return False


@app.route('/post_event', methods=['POST'])
def post_event_handler():

    # This handler handles new posts. If the post appears to contain wiring instructions,
    # flag the new topic for moderator review. Mods will add a staff notice warning about
    # wiring scams, if appropriate. This check does not need to be perfect- it can never
    # be perfect and it's easy enough for mods to ignore any false alarms.

    event_type = request.headers['X-Discourse-Event-Type']
    event = request.headers['X-Discourse-Event']
    print 'event: ', event
    print 'event_type', event_type

    # Any checks for category are best done in the webhook settings
    if event_type == 'post' and event == 'post_created':

        post = request.json['post']

        print 'post: '
        print post

        # Checks to make sure it's a normal public topic, not a PM or system message
        archetype = post.get('topic_archetype')
        user_id = post['user_id']

        print 'archetype: ', archetype

        if archetype != 'private_message' and user_id > 0:
            raw = post['raw']

            #raw = str(raw)  # trying to handle unicode issue
            #print 'raw: ', raw

            if contains_wiring_info(raw):

                print 'contains something about wires'

                slug = post['topic_slug']
                topic_id = post['topic_id']
                post_number = post['post_number']
                url = "https://forum.506investorgroup.com/t/%s/%d/%d" % (slug, topic_id, post_number)

                msg = 'New post may contain wiring instructions. Add staff notice if needed. Review here: %s.  ' % url

                print 'msg: ', msg

                send_simple_email('markschmucker@yahoo.com', event, msg)

                client = create_client(1)
                # post = client.post(topic_id, 1)
                # post_id = post['post_stream']['posts'][0]['id']
                post_id = post['id']

                print 'post_id', post_id

                # all working except not getting the right post_id.

                # Note the flag method is currently added to client.py, not a subclass client506.py.
                client.flag(post_id, msg)

        return '', 200
    else:
        return '', 400


@app.route('/user_event', methods=['POST'])
def user_event_handler():

    # This handler handles user events, so mods can check for full name on user_created
    # and hopefully on user_updated.

    # Ideally I could put arbitrary reviewables on the queue, but that's not possible.
    # Creating a reviewable of type "User" applies only to new users- mods can approve
    # the user or not- so that's not appropriate for this. The best I can do is when a
    # user changes his name or username, I can flag the New Members topic at
    # https://forum.506investorgroup.com/t/policy-actual-full-name-must-be-used-on-the-forum/7298,
    # and in the message include the user's new name and username.

    # The check for new users could be done in either of two ways:
    # 1. This webhook, with type = user_created.
    # 2. The built-in option must_approve_users.
    # I'm trying the second option because it's no work, and blocks the new user until
    # they are approved. However I may still need a webhook here in case the user changes
    # their name or username.

    # Wait until we've approved a few new users via the built-in method before implementing this?

    event_type = request.headers['X-Discourse-Event-Type']
    event = request.headers['X-Discourse-Event']
    print 'event: ', event
    print 'event_type', event_type

    # Any checks for category are best done in the webhook settings
    if event_type == 'user' and event in ('user_created', 'user_updated'):

        user = request.json['user']

        print 'user created: '
        print user

        # just guessing
        name = user['name']
        username = user['username']

        url = "https://forum.506investorgroup.com/u/%s/summary" % username

        msg = 'User created or updated. username: %s, name: %s. Review here: %s.  ' % (username, name, url)

        print 'msg: ', msg

        send_simple_email('markschmucker@yahoo.com', event, msg)

        client = create_client(1)

        # Must flag some post, so flag the full-name policy post (data-post-id from inspection)
        post_id = 50958

        # Note the flag method is currently added to client.py, not a subclass client506.py.
        client.flag(post_id, msg)

        return '', 200
    else:
        return '', 400



if __name__ == "__main__":
    # Digests use 8081, forms use 8082, tracking_pixel and resourse server use 8083,
    # not sure if either of those two on 8083 are running; run this on 8084 (it's open).
    app.run(host="0.0.0.0", port=8085, debug=True, threaded=True)
