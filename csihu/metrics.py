from prometheus_async.aio.web import start_http_server

from csihu.settings import get_settings


class Metrics:
    def __init__(self):
        self.settings = get_settings()

    async def start(self):
        """Start an http server to expose metrics to Prometheus"""

        await start_http_server(port=self.settings.metrics.port)
