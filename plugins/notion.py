from datetime import datetime
import requests
import json

from pyrogram import Client
from pyrogram.enums import ParseMode

import config

async def update_deadlines(app: Client):
    text = '[Актуальные дедлайны:](https://chiseled-poinsettia-873.notion.site/M3115-0343625c66d94066acaf10c49d0d5163)\n\n'
    text += Parser(config.NOTION_SECRET).markdown()
    msg = await app.get_messages(-1001785520098, 33)
    await msg.edit_text(text, ParseMode.MARKDOWN, disable_web_page_preview=True)

class Task:
    def __init__(self, url: str, task: str, deadline: datetime, subject: str) -> None:
        self.url = url
        self.task = task
        self.deadline = deadline
        self.subject = subject
    
    def __str__(self) -> str:
        deadline = self.deadline.strftime('%d.%m.%Y') if self.deadline else "?"
        subject = self.subject if self.subject else "?"
        task = self.task if self.task else "?"
        return f'{deadline} {subject} {task}'
    
    def markdown(self) -> str:
        deadline = self.deadline.strftime('%d.%m.%Y') if self.deadline else "?"
        subject = self.subject if self.subject else "?"
        task = self.task if self.task else "?"
        return f'[{deadline}]({self.url}) - {subject} - {task}'
        
class Parser:
    def __init__(self, secret: str) -> None:
        self.headers = {
            'Authorization': f'Bearer {secret}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28',
        }
        self.payload = json.dumps({
            'filter': {
                'or': [
                    {
                        'property': 'Скоро?',
                        'status': {
                            'equals': 'Скоро'
                        }
                    },
                    {
                        'property': 'Скоро?',
                        'status': {
                            'equals': 'Не скоро'
                        }
                    }
                ]
            },
            'sorts': [
                {
                    'property': 'Дедлайн',
                    'direction': 'ascending',
                }
            ]
        })
    
    def results(self) -> list:
        res = []
        r = requests.post(
            'https://api.notion.com/v1/databases/2e64c5c0d9404c43a75dd29d5538f62e/query',
            headers=self.headers,
            data=self.payload,
        )
        if r.status_code == 200:
            res = r.json().get('results', [])
        return res
    
    def get_tasks(self) -> list[Task]:
        tasks = []
        for result in self.results():
            try:
                url = result.get('public_url')
            except:
                url = None
            try:
                task = result.get('properties').get('Работа').get('title')[0].get('text').get('content')
            except:
                task = None
            try:
                deadline = result.get('properties').get('Дедлайн').get('date').get('start')
                deadline = datetime.fromisoformat(deadline)
            except:
                deadline = None
            try:
                subject = result.get('properties').get('Предмет').get('select').get('name')
            except:
                subject = None
            tasks.append(Task(url, task, deadline, subject))
        return tasks
    
    def markdown(self) -> str:
        s = ''
        for task in self.get_tasks():
            s += task.markdown() + '\n'
        return s
