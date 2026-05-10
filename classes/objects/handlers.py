from typing import Any, Callable, Awaitable, List

from ..library import Embed, Colour, Context, Message, deps, logging, asyncio

class EventHandler:
    events: List[Callable[..., Any]] | None = None
    coro_events: List[Callable[..., Awaitable[Any]]] | None = None

    def __init__(self, event = None, coro_event = None):
        self.events = [event] if not isinstance(event, list) and event is not None else event if event else None
        self.coro_events = [coro_event] if not isinstance(coro_event, list) and coro_event is not None else coro_event if coro_event else None

    async def invokeHandler(self, *args, **kwargs):
        if self.events:
            for event in self.events:
                event(*args, **kwargs)
        if self.coro_events:
            for coro_event in self.coro_events:
                await coro_event(*args, **kwargs)
    
    def add_event(self, event):
        if not self.events:
            self.events = [event]
        else:
            self.events.append(event)

    def add_coro_event(self, event):
        if not self.coro_events:
            self.coro_events = [event]
        else:
            self.coro_events.append(event)
    
    @classmethod
    def copy(cls, event: 'EventHandler | None'):
        if event:
            return cls(event.events, event.coro_events)
        else:
            return cls(None, None)

class Search:
    def _desctruct(self, _1, _2, _3):
        self.member_id = -1

    def __init__(self, label: str, items: dict[str, Any], member_id: int, complete_handler: EventHandler | None = None, error_handler: EventHandler | None = None):
        self.complete_handler = EventHandler.copy(complete_handler)
        self.error_handler = EventHandler.copy(error_handler)
        self.label = label
        self.items = items
        self.member_id = member_id
        self.complete_handler.add_event(self._desctruct)
        self.error_handler.add_event(self._desctruct)
    
    async def send_label(self, ctx: Context):
        m = await ctx.send(embed=Embed(
            title=self.label,
            description="\n".join((str(i + 1) + '. ' + item) for i, item in enumerate(self.items.keys()))
        ))
        await self.taimer(m)

    async def taimer(self, message):
        await asyncio.sleep(30)
        if self.member_id != -1:
            await self.error_handler.invokeHandler(message, Embed(
                title='Время вышло',
                description='Операция была остановлена',
                colour=Colour.red()
            ), self.member_id)
    
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
                await self.error_handler.invokeHandler(message, embed, self.member_id)
                return
            
            choice = int((int(message.content) ** 2) ** 0.5)
            if choice > len(self.items):
                embed=Embed(
                    title='Неверные данные',
                    description='Ожидалось целое число до ' + str(len(self.items)),
                    colour=Colour.red()
                )
                await self.error_handler.invokeHandler(message, embed, self.member_id)
                return
            
            await self.complete_handler.invokeHandler(message, self.items.get(list(self.items.keys())[choice - 1]), self.member_id)
        except Exception as e:
            await self.error_handler.invokeHandler(message, Embed(
                title='Неизвестная ошибка',
                description='Проверьте доступность прав бота',
                colour=Colour.red()
            ), self.member_id)
            logging.error(e)    
