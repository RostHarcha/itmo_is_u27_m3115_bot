import json
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

class Queue:
    def __init__(self, id: int, start: datetime, queue: list) -> None:
        self.id = id
        self.start = start
        self.queue = queue
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "start": self.start.isoformat(),
            "queue": self.queue
        }
    
    def __str__(self) -> str:
        text = f'Очередь {self.start} ({self.id}):\n\n'
        for i, member in enumerate(self.queue):
            text += f'{i + 1}. {member}\n'
        return text

class Queues:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.queues = self.get_all()
    
    def get_all(self) -> list[Queue]:
        with open(self.filename, 'r', encoding='utf-8') as file:
            queues = json.load(file)
        return [Queue(
                queue.get('id'),
                datetime.fromisoformat(queue.get('start')),
                queue.get('queue')
            ) for queue in queues.get('queues', [])]
    
    async def dump(self):
        queues = {"queues": [queue.to_dict() for queue in self.queues]}
        with open(self.filename, 'w', encoding='utf-8') as file:
            json.dump(queues, file)
    
    async def create(self, start: datetime) -> Queue | None:
        if len(self.queues) >= 10:
            return None
        id = 0
        for q in self.queues:
            if q.start == start:
                id += 1
        queue = Queue(id, start, [])
        self.queues.append(queue)
        await self.dump()
        return queue
    
    async def clean(self):
        for queue in self.queues:
            delta = datetime.now() - queue.start
            if delta >= timedelta(minutes=10):
                if delta >= timedelta(hours=3) or len(queue.queue) == 0:
                    self.queues.remove(queue)
        await self.dump()

join_queue_filter = filters.create(lambda _, __, query: query.data.startswith('join_queue_'))
leave_queue_filter = filters.create(lambda _, __, query: query.data.startswith('leave_queue_'))
queue_keyboard = lambda start, id: InlineKeyboardMarkup(
            [[InlineKeyboardButton('Встать в конец', f'join_queue_{start}_{id}')],
            [InlineKeyboardButton('Покинуть', f'leave_queue_{start}_{id}')]]
        )

@Client.on_message(filters.command('q'))
async def queue(client: Client, message: Message):
    queues = Queues('queue.json')
    await queues.clean()
    new_queue = await queues.create(message.date)
    if new_queue is None:
        await message.reply('Превышено доступное количество очередей!')
        return
    
    await message.reply(
        new_queue.__str__(),
        reply_markup=queue_keyboard(new_queue.start, new_queue.id)
    )

@Client.on_callback_query(join_queue_filter)
async def join_queue(client: Client, query: CallbackQuery):
    start, id = query.data.removeprefix('join_queue_').split('_')
    start = datetime.fromisoformat(start)
    id = int(id)
    queues = Queues('queue.json')
    await queues.clean()
    for queue in queues.queues:
        if queue.start == start and queue.id == id:
            if query.from_user.username in queue.queue:
                break
            queue.queue.append(query.from_user.username)
            break
    await queues.dump()
    await query.message.edit_text(queue.__str__(), reply_markup=queue_keyboard(start, id))
    
@Client.on_callback_query(leave_queue_filter)
async def leave_queue(client: Client, query: CallbackQuery):
    start, id = query.data.removeprefix('leave_queue_').split('_')
    start = datetime.fromisoformat(start)
    id = int(id)
    queues = Queues('queue.json')
    await queues.clean()
    for queue in queues.queues:
        if queue.start == start and queue.id == id:
            queue.queue.remove(query.from_user.username)
            break
    await queues.dump()
    await query.message.edit_text(queue.__str__(), reply_markup=queue_keyboard(start, id))
