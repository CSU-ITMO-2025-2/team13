from aio_pika import Message, connect_robust


class Publisher:
    def __init__(self, rabbitmq_url: str, prefetch_count: int = 10):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.prefetch_count = prefetch_count

    async def connect(self):
        if not self.connection or self.connection.is_closed:
            self.connection = await connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.prefetch_count)

    async def publish(self, queue_name: str, message: str):
        if not self.channel or self.channel.is_closed:
            await self.connect()

        await self.channel.default_exchange.publish(
            Message(body=message.encode()),
            routing_key=queue_name,
        )

    async def close(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
