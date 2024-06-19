from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import configparser
from dotenv import load_dotenv

from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType
from langchain.agents import initialize_agent

from stock_price import StockPriceTool
from stock_peformace import StockPercentageChangeTool
from stock_peformace import StockGetBestPerformingTool

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
load_dotenv()

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET', None))

line_bot_api.push_message(os.getenv('DEV_UID', None), TextSendMessage(text='You can start !'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
 
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
 
    return 'OK'

Lmodel = os.getenv('MMODEL', None)

model = ChatOpenAI(model="gpt-3.5-turbo-0613")
tools = [StockPriceTool(), StockPercentageChangeTool(),
         StockGetBestPerformingTool()]
open_ai_agent = initialize_agent(tools, model, agent=AgentType.OPENAI_FUNCTIONS, verbose=False)

@handler.add(MessageEvent)
async def handle_message(event):
    tool_result = open_ai_agent.run(event.message.text)
    await line_bot_api.reply_message( event.reply_token, TextSendMessage(text=tool_result))
    

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)