import os
import openai
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool

# 工具化未完成
class RAG(BaseTool):
    openai.api_key = os.environ["OPENAI_API_KEY"]
    #os.environ["TAVILY_API_KEY"]
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
    #print(response1['choices'][0]['message']['content'])
    