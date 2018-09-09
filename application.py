import os
import logging
# import pydevd
from flask import Flask, request, Response, render_template
from actingweb import config
from actingweb import aw_web_request
import on_aw
from actingweb.handlers import callbacks, properties, meta, root, trust, devtest, \
    subscription, resources, oauth, callback_oauth, bot, www, factory


app = Flask(__name__)

# The on_aw object we will use to do app-specific processing
OBJ_ON_AW = on_aw.OnAWDemo()


def get_config():
    myurl = os.getenv('APP_HOST_FQDN', "localhost")
    proto = os.getenv('APP_HOST_PROTOCOL', "https://")
    aw_type = "urn:actingweb:actingweb.org:actingwebdemo"
    bot_token = os.getenv('APP_BOT_TOKEN', "")
    bot_email = os.getenv('APP_BOT_EMAIL', "")
    bot_secret = os.getenv('APP_BOT_SECRET', "")
    bot_admin_room = os.getenv('APP_BOT_ADMIN_ROOM', "")
    oauth = {
        'client_id': os.getenv('APP_OAUTH_ID', ""),
        'client_secret': os.getenv('APP_OAUTH_KEY', ""),
        'redirect_uri': proto + myurl + "/oauth",
        'scope': "",
        'auth_uri': "https://api.actingweb.net/v1/authorize",
        'token_uri': "https://api.actingweb.net/v1/access_token",
        'response_type': "code",
        'grant_type': "authorization_code",
        'refresh_type': "refresh_token",
    }
    actors = {
        'myself': {
            'type': aw_type,
            'factory': proto + myurl + '/',
            'relationship': 'friend',  # associate, friend, partner, admin
        }
    }
    return config.Config(
        database='dynamodb',
        fqdn=myurl,
        proto=proto,
        aw_type=aw_type,
        desc="Actingwebdemo actor: ",
        version="2.1",
        devtest=True,
        actors=actors,
        force_email_prop_as_creator=False,
        unique_creator=False,
        www_auth="basic",
        ui=True,
        bot={
            "token": bot_token,
            "email": bot_email,
            "secret": bot_secret,
            "admin_room": bot_admin_room
        },
        oauth=oauth
    )


class Handler:

    def __init__(self, req):
        self.handler = None
        self.request = None
        self.response = None
        self.actor_id = None
        self.path = None
        self.method = req.method
        self.webobj = aw_web_request.AWWebObj(
            url=request.url,
            params=request.values,
            body=request.data,
            headers=request.headers
        )
        if not req or not req.path:
            return
        self.request = req
        if req.path == '/':
            self.handler = factory.RootFactoryHandler(
                self.webobj, get_config(), on_aw=OBJ_ON_AW)
        else:
            path = req.path.split('/')
            self.path = path
            f = path[1]
            if f == 'oauth':
                self.handler = callback_oauth.CallbackOauthHandler(
                    self.webobj, get_config(), on_aw=OBJ_ON_AW)
            elif f == 'bot':
                self.handler = bot.BotHandler(
                    webobj=self.webobj, config=get_config(), on_aw=OBJ_ON_AW)
            else:
                self.actor_id = f
                f = path[2]
                if f == 'meta':
                    # r'/<actor_id>/meta<:/?><path:(.*)>'
                    self.handler = meta.MetaHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'oauth':
                    # r'/<actor_id>/oauth<:/?><path:.*>'
                    self.handler = oauth.OauthHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'www':
                    # r'/<actor_id>/www<:/?><path:(.*)>'
                    self.handler = www.WwwHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'properties':
                    # r'/<actor_id>/properties<:/?><name:(.*)>'
                    self.handler = properties.PropertiesHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'trust':
                    # r'/<actor_id>/trust<:/?>'
                    # r'/<actor_id>/trust/<relationship><:/?>'
                    # r'/<actor_id>/trust/<relationship>/<peerid><:/?>'
                    if len(path) == 3:
                        self.handler = trust.TrustHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) == 4:
                        self.handler = trust.TrustRelationshipHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) >= 5:
                        self.handler = trust.TrustPeerHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'subscriptions':
                    # r'/<actor_id>/subscriptions<:/?>'
                    # r'/<actor_id>/subscriptions/<peerid><:/?>'
                    # r'/<actor_id>/subscriptions/<peerid>/<subid><:/?>'
                    # r'/<actor_id>/subscriptions/<peerid>/<subid>/<seqnr><:/?>'
                    if len(path) == 3:
                        self.handler = subscription.SubscriptionRootHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) == 4:
                        self.handler = subscription.SubscriptionRelationshipHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) == 5:
                        self.handler = subscription.SubscriptionHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) >= 6:
                        self.handler = subscription.SubscriptionDiffHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'callbacks':
                    # r'/<actor_id>/callbacks<:/?><name:(.*)>'
                    self.handler = callbacks.CallbacksHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'resources':
                    # r'/<actor_id>/resources<:/?><name:(.*)>'
                    self.handler = resources.ResourcesHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'devtest':
                    # r'/<actor_id>/devtest<:/?><path:(.*)>'
                    self.handler = devtest.DevtestHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                else:
                    self.handler = root.RootHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
        if not self.handler:
            logging.warning('Handler was not set with path: ' + req.url)

    def process(self, **kwargs):
        try:
            if self.method == 'POST':
                self.handler.post(**kwargs)
            elif self.method == 'GET':
                self.handler.get(**kwargs)
            elif self.method == 'DELETE':
                self.handler.delete(**kwargs)
        except AttributeError:
            return False
        return True

    def get_response(self):
        self.response = Response(
            response=self.webobj.response.body,
            status=self.webobj.response.status_message,
            headers=self.webobj.response.headers
        )
        self.response.status_code = self.webobj.response.status_code
        return self.response


# ('/', root_factory.RootFactory),
# webapp2.Route(r'/bot<:/?><path:(.*)>', bots.Bots),
# webapp2.Route(r'/oauth', callback_oauth.CallbackOauths),
# webapp2.Route(r'/<actor_id>/meta<:/?><path:(.*)>', actor_meta.ActorMeta),
# webapp2.Route(r'/<actor_id>/oauth<:/?><path:.*>', actor_oauth.ActorOauth),
# webapp2.Route(r'/<actor_id><:/?>', actor_root.ActorRoot),
# webapp2.Route(r'/<actor_id>/www<:/?><path:(.*)>', actor_www.ActorWWW),
# webapp2.Route(r'/<actor_id>/properties<:/?><name:(.*)>', actor_properties.ActorProperties),
# webapp2.Route(r'/<actor_id>/trust<:/?>', actor_trust.ActorTrust),
# webapp2.Route(r'/<actor_id>/trust/<relationship><:/?>', actor_trust.ActorTrustRelationships),
# webapp2.Route(r'/<actor_id>/trust/<relationship>/<peerid><:/?>', actor_trust.ActorTrustPeer),
# webapp2.Route(r'/<actor_id>/subscriptions<:/?>', actor_subscription.RootHandler),
# webapp2.Route(r'/<actor_id>/subscriptions/<peerid><:/?>', actor_subscription.RelationshipHandler),
# webapp2.Route(r'/<actor_id>/subscriptions/<peerid>/<subid><:/?>', actor_subscription.SubscriptionHandler),
# webapp2.Route(r'/<actor_id>/subscriptions/<peerid>/<subid>/<seqnr><:/?>', actor_subscription.DiffHandler),
# webapp2.Route(r'/<actor_id>/callbacks<:/?><name:(.*)>', actor_callbacks.ActorCallbacks),
# webapp2.Route(r'/<actor_id>/resources<:/?><name:(.*)>', actor_resources.ActorResources),
# webapp2.Route(r'/<actor_id>/devtest<:/?><path:(.*)>', devtests.Devtests),


@app.route('/', methods=['GET', 'POST'])
def app_root():
    h = Handler(request)
    if not h.process():
        return Response(status=404)
    if request.method == 'GET':
        return render_template('aw-root-factory.html', **h.webobj.response.template_values)
    return render_template('aw-root-created.html', **h.webobj.response.template_values)


@app.route('/bot', methods=['POST'])
def app_bot():
    h = Handler(request)
    if not h.process(path='/bot'):
        return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>', methods=['POST'])
def app_main_actor(actor_id):
    h = Handler(request)
    if not h.process(actor_id=actor_id):
        return Response(status=404)
    return h.get_response()


if __name__ == "__main__":
    # To debug in pycharm inside the Docker container, remember to uncomment import pydevd as well
    # (and add to requirements.txt)
    # pydevd.settrace('docker.for.mac.localhost', port=3001, stdoutToServer=True, stderrToServer=True)

    logging.debug('Starting up the ActingWeb Demo ...')
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=9000)
