import os
import sys

import aiohttp

from fastapi import Request, FastAPI, HTTPException

from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType
from langchain.agents import initialize_agent

from stock_price import StockPriceTool
from stock_peformace import StockPercentageChangeTool
from stock_peformace import StockGetBestPerformingTool

from linebot import (
    AsyncLineBotApi, WebhookParser
)
from linebot.aiohttp_async_http_client import AiohttpAsyncHttpClient
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from dotenv import load_dotenv
load_dotenv()

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

app = FastAPI()
session = aiohttp.ClientSession()
async_http_client = AiohttpAsyncHttpClient(session)
line_bot_api = AsyncLineBotApi(channel_access_token, async_http_client)
parser = WebhookParser(channel_secret)

model = ChatOpenAI(model="gpt-3.5-turbo-0613")
tools = [StockPriceTool(), StockPercentageChangeTool(),
         StockGetBestPerformingTool()]
open_ai_agent = initialize_agent(tools,
                                 model,
                                 agent=AgentType.OPENAI_FUNCTIONS,
                                 verbose=False)


@app.post("/callback")
async def handle_callback(request: Request):
    signature = request.headers['X-Line-Signature']

    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        tool_result = open_ai_agent.run(event.message.text)

        await line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=tool_result)
        )

    return 'OK'
#@handler.add(MessageEvent)
#def handle_message(event):
#    message = event.message.text

    #remessage = ""
    #line_bot_api.reply_message(event.reply_token,TextSendMessage(remessage))        
    #line_bot_api.reply_message(event.reply_token,TextSendMessage(chat_completion.choices[0].message.content))
