import requests
import json
import os

from langchain.tools import BaseTool
from langchain.agents import AgentType
from typing import Optional, Type
from pydantic import BaseModel, Field

cwb_token = os.getenv('CWB_TOKEN', None)

class WeatherDataInput(BaseModel):
    """Get weather data input parameters."""
    location_name: str = Field(...,
                               description="The cities in Taiwan, it must be one of following 臺北市, 新北市, 臺中市, 臺南市, 雲林縣, 南投縣, 屏東縣, 嘉義市, 嘉義縣")


class WeatherDataTool(BaseTool):
    name = "get_weather_data"
    description = "Get the weather data for Taiwan"

    def _run(self,  location_name: str):
        weather_data_results = get_weather_data(
            location_name)

        return weather_data_results

    def _arun(self, location_name: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = WeatherDataInput


def get_weather_data(location_name=None):

    if location_name is not None: query = {'locationName': location_name}
    response = requests.get("https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=CWA-03810A35-6474-4ADF-B90C-313A9FD73B24", params=query)

    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code
