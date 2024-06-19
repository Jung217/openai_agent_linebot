from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import configparser
from dotenv import load_dotenv


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

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
load_dotenv()

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET', None))
parser = WebhookParser(handler)

line_bot_api.push_message(os.getenv('DEV_UID', None), TextSendMessage(text='You can start !'))

model = ChatOpenAI(model="gpt-3.5-turbo-0613")
tools = [StockPriceTool(), StockPercentageChangeTool(),
         StockGetBestPerformingTool()]
open_ai_agent = initialize_agent(tools,
                                 model,
                                 agent=AgentType.OPENAI_FUNCTIONS,
                                 verbose=False)

@app.route("/callback", methods=['POST'])
async def callback():
    signature = request.headers['X-Line-Signature']

    signature = request.headers['X-Line-Signature']

    body = await request.body()
    body = body.decode()

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

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

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)