from typing import Any, Callable, Awaitable

from ..library import Embed, Colour, Context, Message, deps, logging

class EventHandler:
    event: Callable[..., Any] | None = None
    coro_event: Callable[..., Awaitable[Any]] | None = None

    def __init__(self, event = None, coro_event = None):
        self.event = event
        self.coro_event = coro_event

    async def invokeHandler(self, *args, **kwargs):
        if self.event:
            self.event(*args, **kwargs)
        if self.coro_event:
            await self.coro_event(*args, **kwargs)
    
    @classmethod
    def copy(cls, event: 'EventHandler | None'):
        if event:
            return cls(event.event, event.coro_event)
        else:
            return cls(None, None)

class Search:
    def __init__(self, label: str, items: dict[str, Any], member_id: int, complete_handler: EventHandler | None = None, error_handler: EventHandler | None = None):
        self.complete_handler = EventHandler.copy(complete_handler)
        self.error_handler = EventHandler.copy(error_handler)
        self.label = label
        self.items = items
        self.member_id = member_id
    
    async def send_label(self, ctx: Context):
        await ctx.send(embed=Embed(
            title=self.label,
            description="\n".join((str(i + 1) + '. ' + item) for i, item in enumerate(self.items.keys()))
        ))
    
    async def on_message_handler(self, message: Message):
        try:
            if message.author.id != self.member_id:
                return
            
            if message.content.startswith(deps.PREFIX):
                return

            if not message.content.isdigit():
                embed=Embed(
                    title='Неверные данные',
                    description='Ожидалось целое число',
                    colour=Colour.red()
                )
                await self.error_handler.invokeHandler(message, embed)
                return
            
            choice = int((int(message.content) ** 2) ** 0.5)
            if choice > len(self.items):
                embed=Embed(
                    title='Неверные данные',
                    description='Ожидалось целое число до ' + str(len(self.items)),
                    colour=Colour.red()
                )
                await self.error_handler.invokeHandler(message, embed)
                return
            
            await self.complete_handler.invokeHandler(message, self.items.get(list(self.items.keys())[choice - 1]))
        except Exception as e:
            await self.error_handler.invokeHandler(message, Embed(
                title='Неизвестная ошибка',
                description='Проверьте доступность прав бота',
                colour=Colour.red()
            ))
            logging.error(e)    
