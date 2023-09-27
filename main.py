import re
import os
import openai
import pandas as pd
import random
from utils import *


json_prompt = '''你必须基于这些经历，以json形式返回这一岁的数值变动，这一岁的能力变动，以及这一岁获取的物品。
数值变动包含4个维度，智力、体力、运气和生命值，智力体力运气的范围是0-10，单次变动最大为2，生命值初始值是100，每过1岁会正常-1，会因为受伤或者意外减少，或者因为特殊事件增加，单次变动数额不受限制
能力变动包含新增能力和失去的能力，每种能力又有4个维度，分别是能力名、能力性质（主动/被动）、能力描述、能力限制
物品则包含物品名和物品描述
以下是一个json示例:
    {
    "stat_changes": {
        "intelligence": 2,
        "strength": -3,
        "luck": 3,
        "life": -10
    },
    "ability_changes": {
        "gained": [
            {
                "ability_name": "黑暗之波",
                "is_active": true,
                "ability_description": "你可以发动黑暗之波攻击，产生巨大的毁灭性力量。",
                "ability_limitations": "每天只能使用一次，使用后需要休息以恢复体力。"
            }
        ],
        "lost": []
    },
    "items_gained": [
        {
            "item_name": "外神之心",
            "item_description": "这是从被击败的外神身上取下的核心，据说可以增强使用者的魔法能力。"
        }
    ]
}'''
num_prompt = '''你必须基于这些经历，以json形式返回这一岁的数值变动。
数值变动包含4个维度，智力、体力、运气和生命值，智力体力运气的范围是0-10，单次变动最大为2，生命值初始值是100，每过1岁会正常-1，会因为受伤或者意外减少，或者因为特殊事件增加，单次变动数额不受限制
以下是一个示例的返回json：
{
    "intelligence": 2,
    "strength": -3,
    "luck": 3,
    "life": -10
}'''
ability_prompt = '''你必须基于这些经历，以json形式返回这一岁的能力变动
能力变动包含新增能力和失去的能力，每种能力又有4个维度，分别是能力名、能力性质（主动/被动）、能力描述、能力限制
以下是一个示例的返回json:
{
    "gained": [
        {
            "ability_name": "黑暗之波",
            "is_active": true,
            "ability_description": "你可以发动黑暗之波攻击，产生巨大的毁灭性力量。",
            "ability_limitations": "每天只能使用一次，使用后需要休息以恢复体力。"
        }
    ],
    "lost": []
}
你需要一步一步仔细思考，深呼吸，复述已有的能力，确保生成的新能力绝对不能和已有的能力类似'''



def show_ability(ability_list):
    '''
    把生成的能力展示给用户
    :param ability_list: 能力列表
    :return:
    '''
    ability_num = 1
    for ability in ability_list :
        print ( f'{ability_num}号能力：' )
        ability_num += 1
        for key, value in ability.items () :
            if key in ['ability_name', 'ability_description', 'ability_limitations'] :
                print ( value )


def generate_random_ability(random_word_list, get_from_local_csv=True):
    if get_from_local_csv:
        ability_list = read_abilities(2)
        show_ability ( ability_list )
        return ability_list

    ability_generation_prompt = '''你是一个能力生成器，你的作用是基于随机词，为当前角色生成一个能力，描述限制在30字以内。你要以类似这样的json格式返回，这是一个输出示例：
    {
    "ability_name": "黑暗之波",
    "is_active": true,
    "ability_description": "你可以发动黑暗之波攻击，产生巨大的毁灭性力量。",
    "ability_limitations": "会对你的运气造成一定程度损害。"
}'''
    random_ability_generator = llm(ability_generation_prompt)
    ability_list = []
    for random_word in random_word_list:
        # 向服务器发送消息
        ability_result = random_ability_generator.single_generate ( user_query=random_word )
        ability_raw = decode_chr(ability_result['content'])
#        # 调试用写死消息
#         ability_raw = '''    {
#     "ability_name": "黑暗之波",
#     "is_active": true,
#     "ability_description": "你可以发动黑暗之波攻击，产生巨大的毁灭性力量。",
#     "ability_limitations": "会对你的运气造成一定程度损害。"
# }'''
        ability = extract_json(text=ability_raw,essential_parameters=['ability_name','ability_description'])
        ability_list.append(ability)

    show_ability(ability_list)
    return ability_list


def generate_random_stat(total: int = 5) -> dict :
    stat_names = ["intelligence", "strength", "luck"]

    # 为每个属性分配一个介于0和2之间的随机数
    random_stats = [random.randint(0, min(10, total)) for _ in stat_names]

    # 调整随机数的总和，使其等于输入的总数
    while sum(random_stats) != total:
        diff = total - sum(random_stats)
        if diff > 0:  # 需要增加总和
            # 选取一个属性值少于10的属性来增加
            valid_indices = [i for i, stat in enumerate(random_stats) if stat < 10]
            if valid_indices:  # 列表不为空
                random_index = random.choice(valid_indices)
                random_stats[random_index] += 1
        else:  # 需要减少总和
            # 选取一个属性值大于0的属性来减少
            valid_indices = [i for i, stat in enumerate(random_stats) if stat > 0]
            if valid_indices:  # 列表不为空
                random_index = random.choice(valid_indices)
                random_stats[random_index] -= 1

    # 创建一个字典，将属性名称与它们的数值关联起来
    stat_dict = {name: value for name, value in zip(stat_names, random_stats)}
    # 初始生命设置为100
    stat_dict['life'] = 100

    return stat_dict


def life_initialization():
    player_name = input('输入玩家名\n')
    if not player_name:
        player_name = 'Billy'
    # 从数据库内读取随机项来创建世界观，这里我暂时写死一个
    world_view = {
        "name" : "Eldoria",
        "geography" : {
            "continent" : "Varathia",
            "climate" : "mild",
            "features" : ["forests", "mountains", "rivers", "ocean"]
        },
        "races" : [
            {
                "name" : "Humans",
                "culture" : "feudal",
                "religion" : "polytheistic"
            },
            {
                "name" : "Elves",
                "culture" : "matriarchal",
                "religion" : "animistic"
            },
            {
                "name" : "Dwarves",
                "culture" : "clan-based",
                "religion" : "ancestor worship"
            }
        ],
        "history" : {
            "ancient" : "Age of Dragons",
            "middle" : "Elven Dominion",
            "recent" : "Human Expansion"
        },
        "politics" : {
            "majorPowers" : ["Kingdom of Aloria", "Elven Republic of Lorien", "Dwarven Clans of Moria"],
            "conflicts" : ["Border dispute between Aloria and Lorien",
                           "Underground war between Moria and the Underdark"]
        },
        "magic" : {
            "prevalence" : "common",
            "source" : "arcane and divine"
        },
        "technology" : "medieval",
        "religion" : {
            "deities" : ["Solaris, goddess of the sun", "Lunaris, god of the moon"],
            "afterlifeBelief" : "reincarnation"
        },
        "threats" : ["Dragons", "Orcs", "Underdark Creatures"]
    }
    # 从数据库内读取随机词，基于2个随机词来生成2个随机能力
    random_word_list = get_random_word(word_num=2)
    ability_list = generate_random_ability(random_word_list)
    # 用户选择世界观与能力
    initial_ability = ability_list[int(input(f'选择你希望携带的初始能力（输入序号选择）：'))-1]
    # 用户输入属性值（这里我先随机了）
    stat_dict = generate_random_stat(3)
    # print(initial_ability,stat_dict)
    return world_view,initial_ability,stat_dict,player_name


def select_ability(player_ability_list):
    '''
    展示能力给用户，让用户选择能力
    :param player_ability_list:玩家具有的能力
    :return:activated_ability:玩家选择激活的能力名
    '''
    activated_ability = []
    try:
        show_ability(player_ability_list)
        # 让用户选择能力激活
        chosen_index = int(input('请输入数字序号，选择激活玩家目前的已有能力（被动能力默认激活）'))-1
        if chosen_index >= 0 and chosen_index < len(player_ability_list):
            activated_ability.append(player_ability_list[chosen_index])
        else:
            activated_ability.append(player_ability_list[0])
    except (ValueError, IndexError):
        activated_ability = player_ability_list[0]

    for ability in player_ability_list:
        if ability['is_active'] == False:
            activated_ability.append(ability)




    return activated_ability


def select_keyword(keyword_lst):
    # 把生成的关键词展示给用户
    keyword_lst_num = 1
    for keyword in keyword_lst :
        print ( f'{keyword_lst_num}号关键词：{keyword}' )
        keyword_lst_num += 1

    # 让用户选择下一岁的关键词
    chosen_index = int ( input ( '请输入数字序号，选择下一岁的事件与什么有关' ) )-1
    if chosen_index >= 0 and chosen_index < len ( keyword_lst ) :
        activated_keyword = keyword_lst[chosen_index]
    else :
        activated_keyword = keyword_lst[0]

    return activated_keyword


def generate_life_system_prompts(world_view, activated_ability, stat_dict, player_name):
    life_generate_prompt = f'''你现在要模拟{player_name}的人生，并描述玩家在这一岁经历的一个重大事件本身'''
    world_view_prompt = f'''这是本次人生的世界观，你生成的故事必须严格遵循该世界观：{world_view}'''
    stat_prompt = f'''你生成的人生经历必须和玩家的属性高度相符，分数范围为0-10，数值越高证明对应能力越强，0分意味着最差，10分意味着最强，以下是玩家的当前属性值：{stat_dict}'''
    life_system_prompts_dic = {
        'life_generate_prompt' : life_generate_prompt,
        # 'world_view_prompt':world_view_prompt,
        'stat_prompt' : stat_prompt,
        # 'json_prompt':json_prompt,
    }
    if activated_ability:
        ability_prompt = f'''本岁的人生经历里，{player_name}一定会主动使用如下能力：```{activated_ability}```'''
        life_system_prompts_dic['ability_prompt'] = ability_prompt

    return life_system_prompts_dic


def generate_age_prompts(player_name, age, stat_dict, key_word):
    described_stat_dict = describe_stat( stat_dict )
    age_prompt = f'''一步一步仔细思考，深呼吸，用玄幻小说的风格撰写下列经历：{player_name}今年{age}岁了，
    {player_name}智力{described_stat_dict['intelligence']}，力量{described_stat_dict['strength']}，运气{described_stat_dict['luck']}，你必须基于{player_name}本次发动的能力及其负面效果，详细描述{player_name}在这一岁的某个重大事件本身，你的叙述只包含这一岁发生的事情，不包含任何对未来的影响或语言，这个重大事件必须和以下要素有关：{key_word}，并必须先正面后负面，或者先抑后扬'''
    return age_prompt


def generate_age_event(player_name, age, player_stat_dict, key_word,life_system_prompts_dic):
    age_prompt = generate_age_prompts ( player_name, age, player_stat_dict, key_word )
    # 构建并发送消息
    life_messages = []
    life_messages.extend ( messaglize_prompt ( life_system_prompts_dic ) )
    life_messages.append ( {"role" : "user", "content" : age_prompt} )
    # 为了调试写死消息
    #         raw_age_event = {
    #   "role": "assistant",
    #   "content": "\u5c0f\u660e\u572801\u5c81\u65f6\uff0c\u7ecf\u5386\u4e86\u4e00\u6b21\u91cd\u5927\u7684\u4e8b\u4ef6\u4e0e\u9053\u679c\u6709\u5173\u3002\u9053\u679c\u662f\u4e00\u79cd\u795e\u79d8\u7684\u81ea\u7136\u529b\u91cf\uff0c\u5b83\u5b58\u5728\u4e8e\u6574\u4e2aEldoria\u4e16\u754c\u4e2d\u7684\u4e07\u7269\u4e4b\u95f4\uff0c\u6bcf\u4e2a\u4eba\u90fd\u6709\u53ef\u80fd\u4e0e\u4e4b\u4ea7\u751f\u8054\u7cfb\u3002\n\n\u5728\u67d0\u4e2a\u9633\u5149\u660e\u5a9a\u7684\u65e9\u6668\uff0c\u5c0f\u660e\u88ab\u5468\u56f4\u73af\u5883\u4e2d\u878d\u5408\u7740\u9053\u679c\u6c14\u606f\u6240\u5438\u5f15\uff0c\u4ed6\u8ddf\u968f\u7740\u8fd9\u9053\u6c14\u606f\u8d70\u8fdb\u4e86\u4e00\u7247\u68ee\u6797\u3002\u5728\u68ee\u6797\u6df1\u5904\uff0c\u4ed6\u53d1\u73b0\u4e00\u68f5\u5de8\u5927\u7684\u53e4\u6811\uff0c\u6811\u5e72\u6563\u53d1\u7740\u4ee4\u4eba\u5fc3\u9189\u795e\u8ff7\u7684\u9053\u679c\u80fd\u91cf\u3002\n\n\u5c0f\u660e\u88ab\u5438\u5f15\u4f4f\uff0c\u8f7b\u8f7b\u89e6\u6478\u7740\u6811\u5e72\u3002\u7a81\u7136\uff0c\u4e00\u80a1\u5f3a\u5927\u7684\u80fd\u91cf\u6d8c\u5165\u4ed6\u5fc3\u7075\u6df1\u5904\u3002\u4ed6\u611f\u53d7\u5230\u81ea\u5df1\u4e0e\u5927\u81ea\u7136\u7684\u8054\u7cfb\uff0c\u601d\u7ef4\u6e05\u6670\u5982\u6c34\uff0c\u529b\u91cf\u5145\u76c8\u5982\u5c71\u3002\n\n\u8fd9\u6b21\u63a5\u89e6\u9053\u679c\u7684\u7ecf\u5386\u8ba9\u5c0f\u660e\u7684\u667a\u529b\u3001\u529b\u91cf\u548c\u8fd0\u6c14\u5f97\u5230\u4e86\u6781\u5927\u7684\u63d0\u5347\u3002\u4ed6\u7684\u667a\u529b\u53d8\u5f97\u66f4\u52a0\u654f\u9510\uff0c\u601d\u7ef4\u53d8\u5f97\u66f4\u52a0\u7075\u6d3b\uff0c\u4ed6\u80fd\u591f\u66f4\u597d\u5730\u7406\u89e3\u548c\u5229\u7528\u77e5\u8bc6\u3002\u4ed6\u7684\u529b\u91cf\u4e5f\u53d8\u5f97\u66f4\u52a0\u5f3a\u5927\uff0c\u808c\u8089\u9aa8\u9abc\u5145\u6ee1\u4e86\u80fd\u91cf\uff0c\u8ba9\u4ed6\u5728\u4f53\u529b\u4e0a\u6709\u4e86\u8d28\u7684\u98de\u8dc3\u3002\u800c\u8fd0\u6c14\u4e5f\u56e0\u6b64\u53d8\u5f97\u66f4\u52a0\u987a\u9042\uff0c\u5404\u79cd\u673a\u7f18\u5de7\u5408\u4f3c\u4e4e\u90fd\u5728\u4ed6\u8eab\u8fb9\u51fa\u73b0\u3002\n\n\u8fd9\u6b21\u4e0e\u9053\u679c\u7684\u4ea4\u4e92\u5bf9\u5c0f\u660e\u7684\u6570\u503c\u4ea7\u751f\u4e86\u663e\u8457\u7684\u5f71\u54cd\u3002\u4ed6\u7684\u667a\u529b\u5f97\u5230\u4e86+2\u7684\u589e\u52a0\uff0c\u8ba9\u4ed6\u5728\u5b66\u4e60\u548c\u601d\u8003\u65b9\u9762\u66f4\u52a0\u51fa\u8272\u3002\u4ed6\u7684\u529b\u91cf\u4e5f\u5f97\u5230\u4e86+2\u7684\u63d0\u5347\uff0c\u8ba9\u4ed6\u5728\u4f53\u80fd\u65b9\u9762\u8fdc\u8d85\u540c\u9f84\u4eba\u3002\u800c\u8fd0\u6c14\u66f4\u662f\u5f97\u5230\u4e86+3\u7684\u63d0\u5347\uff0c\u8ba9\u4ed6\u65f6\u523b\u5145\u6ee1\u7740\u597d\u8fd0\u548c\u673a\u9047\u3002\n\n\u7136\u800c\uff0c\u63a5\u89e6\u9053\u679c\u4e5f\u6709\u5176\u4ee3\u4ef7\u3002\u8fd9\u79cd\u80fd\u91cf\u7684\u6d41\u5165\u5e76\u4e0d\u662f\u6beb\u65e0\u4ee3\u4ef7\u7684\uff0c\u5b83\u5bf9\u5c0f\u660e\u7684\u751f\u547d\u9020\u6210\u4e86\u4e00\u5b9a\u7684\u635f\u8017\u3002\u5c0f\u660e\u7684\u751f\u547d\u503c\u4e0b\u964d\u4e8610\u70b9\uff0c\u4f46\u8fd9\u4e2a\u4ee3\u4ef7\u76f8\u6bd4\u4e8e\u83b7\u5f97\u7684\u667a\u529b\u3001\u529b\u91cf\u548c\u8fd0\u6c14\u7684\u63d0\u5347\u6765\u8bf4\u662f\u503c\u5f97\u7684\u3002\n\n\u9664\u4e86\u6570\u503c\u7684\u53d8\u52a8\uff0c\u5c0f\u660e\u8fd8\u4ece\u8fd9\u6b21\u7ecf\u5386\u4e2d\u83b7\u5f97\u4e86\u4e00\u4e2a\u7279\u6b8a\u80fd\u529b\uff0c\u5373\u9ed1\u6697\u4e4b\u6ce2\u3002\u4ed6\u80fd\u53d1\u52a8\u9ed1\u6697\u4e4b\u6ce2\u653b\u51fb\uff0c\u91ca\u653e\u51fa\u5de8\u5927\u7684\u6bc1\u706d\u6027\u529b\u91cf\u3002\u7136\u800c\uff0c\u9ed1\u6697\u4e4b\u6ce2\u7684\u4f7f\u7528\u4f1a\u5bf9\u4ed6\u7684\u8fd0\u6c14\u9020\u6210\u4e00\u5b9a\u7a0b\u5ea6\u7684\u635f\u5bb3\u3002\u5c0f\u660e\u9700\u8981\u660e\u667a\u5730\u8fd0\u7528\u8fd9\u4e2a\u80fd\u529b\uff0c\u4ee5\u514d\u9020\u6210\u4e0d\u53ef\u9006\u8f6c\u7684\u540e\u679c\u3002\n\n\u6b64\u5916\uff0c\u5c0f\u660e\u4e5f\u627e\u5230\u4e86\u4e00\u4ef6\u73cd\u8d35\u7684\u7269\u54c1\uff0c\u5916\u795e\u4e4b\u5fc3\u3002\u8fd9\u4e2a\u5916\u795e\u4e4b\u5fc3\u662f\u4ece\u88ab\u51fb\u8d25\u7684\u5916\u795e\u8eab\u4e0a\u53d6\u4e0b\u7684\u6838\u5fc3\uff0c\u636e\u8bf4\u53ef\u4ee5\u589e\u5f3a\u4f7f\u7528\u8005\u7684\u9b54\u6cd5\u80fd\u529b\u3002\u8fd9\u4e2a\u7269\u54c1\u5c06\u6210\u4e3a\u5c0f\u660e\u672a\u6765\u6210\u957f\u7684\u4e00\u4e2a\u5173\u952e\u56e0\u7d20\u3002\n\n\u5c0f\u660e\u572801\u5c81\u65f6\u7684\u4eba\u751f\u7ecf\u5386\u5145\u6ee1\u4e86\u795e\u79d8\u548c\u53d8\u5316\u3002\u63a5\u89e6\u9053\u679c\u8ba9\u4ed6\u5f97\u5230\u4e86\u667a\u529b\u3001\u529b\u91cf\u548c\u8fd0\u6c14\u7684\u63d0\u5347\uff0c\u4f46\u4e5f\u4ed8\u51fa\u4e86\u751f\u547d\u503c\u7684\u4ee3\u4ef7\u3002\u9ed1\u6697\u4e4b\u6ce2\u7684\u80fd\u529b\u548c\u5916\u795e\u4e4b\u5fc3\u7684\u7269\u54c1\u5c06\u6210\u4e3a\u4ed6\u672a\u6765\u5192\u9669\u7684\u5a01\u529b\u6765\u6e90\u3002\u5c0f\u660e\u7684\u672a\u6765\u5728Eldoria\u4e16\u754c\u4e2d\u6ce8\u5b9a\u662f\u5145\u6ee1\u6311\u6218\u4e0e\u673a\u9047\u7684\u3002"
    # }
    # # 检查返回值
    # print(raw_age_event)
    age_event_delta_lst = []
    # 上色
    # 定义颜色代码
    BLACK_ON_WHITE = '\033[30;47m'
    RESET = '\033[0m'  # 重置颜色到默认颜色
    # 从这里开始，输出带颜色的文本
    print ( BLACK_ON_WHITE )
    life_generator = llm ()
    # 流式传输人生经历
    print ( "本次人生事件：\n" )
    for age_event_delta in life_generator.stream_generate ( life_messages ) :
        age_event_delta_lst.append ( age_event_delta )
        print ( age_event_delta, end='' )
    age_event = ''.join ( age_event_delta_lst )
    # print(age_event)
    print ( RESET )
    return age_event


def update_player_stat(stat_dict, changes_dict):
    # 遍历状态改变字典中的每一个键值对
    for key, value in changes_dict.items():
        # 如果这个键在旧的状态字典中存在，就将改变的值加到它上面
        if key in stat_dict:
            stat_dict[key] += value

    # 返回新的状态JSON
    return stat_dict


def update_player_abilities(player_ability_list, ability_changes):
    # 遍历“gained”中的所有能力
    for gained_ability in ability_changes['gained'] :
        # 提取当前能力的名称
        gained_ability_name = gained_ability['ability_name']

        # 检查该能力的名称是否已经存在于player_ability_list中
        ability_exists = any ( ability['ability_name'] == gained_ability_name for ability in player_ability_list )

        # 如果该能力的名称不存在于player_ability_list中，则添加它
        if not ability_exists :
            player_ability_list.append ( gained_ability )

    # 遍历player_ability_list中的每个字典
    for ability in player_ability_list :
        # 检查字典中的ability_name字段是否存在于lost_ability列表中
        if ability['ability_name'] in [lost_ability['ability_name'] for lost_ability in ability_changes['lost']] :
            # 如果不存在，则将该字典添加到新列表中
            player_ability_list.remove(ability)



    return player_ability_list


class experience_based_changer(llm):
    def __init__(self, system_prompt) :
        super ().__init__ ( system_prompt )

    def extract(self):
        self.event_dic = extract_json(self.single_generate_content)
        return self.event_dic

    def change_by_age(self,age_event):
        self.age_prompt_for_changer = f"这是用户这一岁的经历：```{age_event}```"
        pass

def death_event():
    print('你死了，这里是还没写的死亡事件')
    return

def main():
    # 游戏初始化，生成初始能力、角色数值、玩家名（、世界观）
    world_view,initial_ability,player_stat_dict,player_name = life_initialization ()
    player_ability_list = [initial_ability]
    life = player_stat_dict['life']
    age = 0
    while True:
        age += 1
        # 选择激活的能力
        key_word = select_keyword(get_random_word(word_num=2))
        activated_ability = select_ability ( player_ability_list )
        life_system_prompts_dic = generate_life_system_prompts( world_view, activated_ability, player_stat_dict, player_name )

        # 生成本岁事件
        age_event = generate_age_event(player_name, age, player_stat_dict, key_word,life_system_prompts_dic)

        print('数值变化计算中')
        # 把经历打包给数值和技能Agent，让他基于经历产生数值
        num_changer = experience_based_changer(system_prompt=num_prompt)
        num_changer.single_generate(age_event)
        # 用数值和技能Agent的返回值修改玩家数值和技能
        num_changer.extract()
        # 更新玩家数值、能力
        player_stat_dict = update_player_stat(player_stat_dict, num_changer.event_dic)
        print(f"本次数值变化：\n{num_changer.event_dic}")
        print(f'当前数值：{player_stat_dict}')

        if life<0:
            death_event()
            break


        print('能力变化生成中')
        ability_changer = experience_based_changer(system_prompt=ability_prompt)
        ability_antiduplicate_prompt = f'''一步一步仔细思考，深呼吸，复述玩家目前已有的能力，并在生成技能时，确保你所生成的技能不和玩家已有的技能同类，这些是玩家已有的技能：```{player_ability_list}```，这是用户这一岁的经历：```{age_event}```'''
        ability_changer.single_generate ( ability_antiduplicate_prompt)
        # item_changer = experience_based_changer(system_prompt=json_prompt)
        # item_changer.single_generate ( age_event )
        ability_changer.extract ()
        print(f"本次能力变化：\n{ability_changer.event_dic}")
        player_ability_list = update_player_abilities(player_ability_list, ability_changer.event_dic)








if __name__ == '__main__':
    main()
    # print(generate_random_stat())
    # json_dic = extract_json_from_text(json_prompt,essential_parameters=["player_name","age","major_event","stat_changes","ability_changes","items_gained"])
    # print(type(json_dic))
    # print(json_dic)
