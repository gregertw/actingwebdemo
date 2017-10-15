import webapp2
from jinja2 import Environment, PackageLoader, select_autoescape

from aw_handlers import root_factory, actor_root, actor_www, actor_properties, actor_meta, bot


app = webapp2.WSGIApplication([
    ('/', root_factory.root_factory),
    webapp2.Route(r'/bot<:/?><path:(.*)>', bot.bot),
    (r'/(.*)/meta/?(.*)', actor_meta.actor_meta),
    webapp2.Route(r'/<id><:/?>', actor_root.actor_root),
    webapp2.Route(r'/<id>/www<:/?><path:(.*)>', actor_www.actor_www),
    webapp2.Route(r'/<id>/properties<:/?><name:(.*)>', actor_properties.actor_properties),
], debug=True)


def set_config():
    if not app.registry.get('config'):
        # Import the class lazily.
        config = webapp2.import_string('actingweb.config')
        config = config.config(
            database='dynamodb',
            fqdn="ad112387.ngrok.io",
            proto="http://")
        # Register the instance in the registry.
        app.registry['config'] = config
    return


def set_template_env():
    if not app.registry.get('template'):
        # Import the class lazily.
        webapp2.import_string('jinja2.Environment')
        # Register the instance in the registry.
        app.registry['template'] = Environment(
            loader=PackageLoader('application', 'templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
    return


def main():
    from paste import httpserver
    httpserver.serve(app, host='0.0.0.0', port='5000')


if __name__ == '__main__':
    set_config()
    set_template_env()
    main()
