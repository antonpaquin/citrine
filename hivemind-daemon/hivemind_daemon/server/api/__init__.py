from .aio_server import AioServer
from .base import get_base_server
from .nn import get_nn_server
from .package import get_package_server


def get_server():
    server = AioServer()
    
    server.add_submodule('', get_base_server())
    server.add_submodule('', get_nn_server())
    server.add_submodule('/package', get_package_server())

    return server
