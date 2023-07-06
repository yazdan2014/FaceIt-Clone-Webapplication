from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack

from accounts import routing as account_routing

application = ProtocolTypeRouter({
    'websocket':
        SessionMiddlewareStack(AuthMiddlewareStack(
            URLRouter(
                account_routing.websocket_urlpatterns,

            )
        ))
})
