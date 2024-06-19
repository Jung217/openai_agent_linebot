from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import re
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
from langchain.tools import DuckDuckGoSearchRun

from stock_price import StockPriceTool
from stock_peformace import StockPercentageChangeTool
from stock_peformace import StockGetBestPerformingTool

from poi import TravelPOITool
from ticket import TravelTicketTool
from weather import WeatherDataTool
from product import ProductTool
#from rag import RAG
import openai
from langchain import hub
from langchain.agents import AgentExecutor
#from langchain.agents import create_react_agent
from langchain.agents.react.agent import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults


app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
load_dotenv()

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET', None))

line_bot_api.push_message(os.getenv('DEV_UID', None), TextSendMessage(text='You can start !'))

model = ChatOpenAI(model="gpt-3.5-turbo")
tools = [StockPriceTool(), StockPercentageChangeTool(), StockGetBestPerformingTool(), TravelPOITool(), TravelTicketTool(), WeatherDataTool(), ProductTool(), DuckDuckGoSearchRun()]

open_ai_agent = initialize_agent(tools, model, agent=AgentType.OPENAI_FUNCTIONS, verbose=False)

@app.route("/callback", methods=['POST'])
async def callback():
    signature = request.headers['X-Line-Signature']

    bodyT = request.get_data(as_text=True)
    body = request.get_data()
    app.logger.info("Request body: " + bodyT)

    try:
        handler.handle(bodyT, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent)
def handle_message(event):
    message = event.message.text
    if re.match("提示",message):
        remessage = "預設使用繁體中文回答\n太久未啟動需先喚醒。\n用'@問題'可用最基礎的RAG回答\n其他有股票、天氣、旅遊、購物等\n\nThank you  :)"
        line_bot_api.reply_message(event.reply_token,TextSendMessage(remessage)) 
    elif '@' in message:
        openai.api_key = os.environ["OPENAI_API_KEY"]
        prompt = hub.pull("hwchase17/react")
        llm = ChatOpenAI(model="gpt-3.5-turbo")
        tools = [TavilySearchResults(max_results=2)]
        agent = create_react_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        user_input = input("Enter your question: ")
        response = agent_executor.invoke({"input": user_input + "，#zh-TW"})
        user_input1 = response['output'] + " 將任何輸入翻譯成繁體中文"
        response1 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input1}
            ]
        )
        line_bot_api.reply_message(event.reply_token,TextSendMessage(response1['choices'][0]['message']['content']))
    else:
        tool_result = open_ai_agent.run(message)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(tool_result)) 

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)