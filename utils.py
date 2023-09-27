# coding=utf-8
"""
@author B1lli
@date 2023年09月18日 19:14:51
@File:utils.py
"""
import re
import os
import csv
import json
import openai
import pandas as pd
import random
from typing import List, Optional, Dict

openai.api_key = input('填入自己的apikey，修改utils内的该行以写死')
# 字符转码函数
def decode_chr(s):
    if type(s) != str:print(f'本次decode_chr类型非str，为{type(s)}')
    s = str(s)
    s = s.replace('\\\\','\\')
    pattern = re.compile(r'(\\u[0-9a-fA-F]{4}|\n)')
    result = ''
    pos = 0
    while True:
        match = pattern.search(s, pos)
        if match is None:
            break
        result += s[pos:match.start()]
        if match.group() == '\n':
            result += '\n'
        else:
            result += chr(int(match.group()[2:], 16))
        pos = match.end()
    result += s[pos:]
    return result




def get_random_word(random_source_csv=None, word_num=1, column_name=None):
    if not random_source_csv:
        random_source_csv = 'random_words.csv'
    df = pd.read_csv(random_source_csv)

    if column_name:
        if column_name in df.columns:
            return random.sample(list(df[column_name].dropna()), word_num)
        else:
            raise ValueError(f"列名 {column_name} 在词库里没找到")
    else:
        column = random.choice(df.columns.tolist())
        return random.sample(list(df[column].dropna()), word_num)




def check_parameters(json_object: Dict, parameters: List[str]) -> List[str]:
    """
    检查 JSON 对象是否缺少给定的参数。

    Args:
        json_object (Dict): JSON 对象。
        parameters (List[str]): 参数列表。

    Returns:
        List[str]: 缺少的参数列表。
    """
    return [param for param in parameters if param not in json_object]


def extract_json(text: str, essential_parameters: Optional[List[str]] = None,
                 optional_parameters: Optional[List[str]] = None) -> Dict:
    """
    从给定的文本中提取第一个 JSON 对象，并检查是否缺少必要的参数或可选的参数。

    Args:
        text (str): 输入的文本。
        essential_parameters (List[str], optional): 必要的参数的列表。默认为空。
        optional_parameters (List[str], optional): 可选的参数的列表。默认为空。

    Returns:
        Dict: 如果找到了 JSON 对象，返回这个 JSON 对象；
              如果 JSON 对象包含所有必要的参数，会在其末尾添加 "lack_essential_parameter" 键，
              值为缺失的必要参数列表；
              如果 JSON 对象包含所有可选的参数，会在其末尾添加 "lack_optional_parameter" 键，
              值为缺失的可选参数列表，如果没有缺失的可选参数，值为 None；
              如果没有找到 JSON 对象，返回空字典。
    """
    if not essential_parameters: essential_parameters = []
    if not optional_parameters: optional_parameters = []

    # 找到 JSON 字符串的开始和结束位置
    try:
        start = text.index('{')
        end = text.rindex('}') + 1
        # 提取 JSON 字符串
        json_text = text[start:end]
        # 替换 "True" 和 "False" 为 "true" 和 "false"
        json_text = json_text.replace("True", "true").replace("False", "false")
    except ValueError as e:
        print(f"未找到 JSON 对象: {e}")
        # print(f'本岁的人生经历：{text}')
        return {}

    try:
        json_object = json.loads(json_text)

        # 检查缺失的必要参数
        missing_essential_parameters = check_parameters(json_object, essential_parameters)
        if missing_essential_parameters:
            json_object["lack_essential_parameter"] = missing_essential_parameters

        # 检查缺失的可选参数
        missing_optional_parameters = check_parameters(json_object, optional_parameters)
        if missing_optional_parameters:
            json_object["lack_optional_parameter"] = missing_optional_parameters
        else:
            json_object["lack_optional_parameter"] = None

        return json_object

    except json.JSONDecodeError as e:
        print(f"解析错误: {e}")
        print(f'原文为：{json_text}')
    finally:
        pass

    return {}



def describe_stat(abilities):
    description = {
        0 : "极差",
        1 : "差",
        2 : "略差",
        3 : "正常水平",
        4 : "略超常人",
        5 : "超常",
        6 : "明显超人",
        7 : "极度超人",
        8 : "近乎半神",
        9 : "半神",
        10 : "神话"
    }
    return {
        ability: description.get(value, "极差") if value < 0 else description.get(value, "超越神话")
        for ability, value in abilities.items() if ability != 'life'
    }


def messaglize_prompt(life_system_prompts_dic) :
    """
    这个函数的目的是把我们的系统prompt，变成大语言模型api所要求的message。
    将一个包含prompts的字典转变为一个Large Language Model (LLM)可以理解的消息请求格式。

    输入的字典（life_system_prompts_dic）应该是按照插入顺序排序的，其中键是提示的名称，值是提示的内容。

    函数会为每个提示创建一个新的字典，其中包含键 "role"（值为 "system"）和键 "content"（值为提示的内容）。所有这些新创建的字典都会被添加到一个列表中，然后返回这个列表。

    Parameters:
    life_system_prompts_dic (dict): A dictionary where keys are the names of prompts and values are the prompts themselves.

    Returns:
    list: A list of dictionaries, where each dictionary has a 'role' key (with value 'system') and a 'content' key (with the content of the prompt).
    """

    # 初始化一个空列表用于存储结果
    result = []

    # 从life_system_prompts_dic中获取键值对
    for key in life_system_prompts_dic :
        # 获取对应的字符串
        prompt = life_system_prompts_dic[key]

        # 创建一个新的字典，用于存储'role'和'content'键值对
        new_dict = {}
        new_dict['role'] = 'system'
        new_dict['content'] = prompt

        # 将新创建的字典添加到结果列表中
        result.append ( new_dict )

    # 返回结果列表
    return result


def read_abilities(num_abilities, csv_filename='./ability.csv') :
    abilities = []
    with open ( csv_filename, 'r', encoding='utf-8' ) as csvfile :
        reader = csv.DictReader ( csvfile )
        for row in reader :
            ability = {
                "ability_name" : row["ability_name"],
                "is_active" : row["is_active"] == "True",
                "ability_rank" : row["ability_rank"],
                "ability_description" : row["ability_description"],
                "ability_limitations" : row["ability_limitations"],
                "world_view" : row["world_view"]
            }
            abilities.append ( ability )

    random.shuffle ( abilities )  # 随机打乱abilities列表顺序
    return abilities[:num_abilities]


class llm():
    def __init__(self,system_prompt=None,model='gpt-3.5-turbo-0613'):
        self.system_prompt = system_prompt
        self.model = model

    def single_generate(self, user_query, decode=True):
        '''
        单次生成回复，用于种种只需要单轮上下文的调用场景
        :param user_query: content
        :return: content
        '''
        messages = [
            {"role" : "system", "content" : self.system_prompt},
            {"role" : "user", "content" : user_query}
        ]
        response = openai.ChatCompletion.create (
            model=self.model,
            messages=messages,
        )
        self.single_generate_content = response["choices"][0]["message"]['content']
        if decode :
            self.single_generate_content = decode_chr ( self.single_generate_content )
            return self.single_generate_content
        return self.single_generate_content

    def custom_generate(self,messages,decode=True):
        '''
        自定义生成，需要组装好message上下文传进去，返回给你的也是message
        :param messages:message
        :return:message
        '''
        response = openai.ChatCompletion.create (
            model=self.model,
            messages=messages,
        )
        if decode:
            response["choices"][0]["message"]['content'] = decode_chr(response["choices"][0]["message"]['content'])
            return response["choices"][0]["message"]
        return response["choices"][0]["message"]

    def stream_generate(self, messages, decode=True) :
        '''
        流式传输
        :param messages: message
        :param decode: bool，是否返回解码文字
        :return: 流式传输的content
        '''
        completion = openai.ChatCompletion.create (
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True
        )

        if decode :
            return self._stream_generate_decoded ( completion )
        else :
            return self._stream_generate_raw ( completion )

    def _stream_generate_decoded(self, completion) :
        for chunk in completion :
            try :
                if chunk.choices[0].delta :
                    yield decode_chr ( chunk.choices[0].delta.content )
            except Exception as e :
                print ( e )
                continue

    def _stream_generate_raw(self, completion) :
        for chunk in completion :
            try :
                if chunk.choices[0].delta :
                    yield chunk.choices[0].delta.content
            except Exception as e :
                print ( e )
                continue


if __name__ == '__main__':
    print(1)