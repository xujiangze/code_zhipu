import requests
import time
import os
from typing import Generator, List

import jwt

from data_types import TextMsg, ImageMsg, TextMsgList, MsgList, CharacterMeta

# 智谱开放平台API key，参考 https://open.bigmodel.cn/usercenter/apikeys
API_KEY: str = os.getenv("API_KEY", "")


class ApiKeyNotSet(ValueError):
    pass


def verify_api_key_not_empty():
    if not API_KEY:
        raise ApiKeyNotSet


def generate_token(apikey: str, exp_seconds: int) -> str:
    """
    生成智谱开放平台API的token
    # reference: https://open.bigmodel.cn/dev/api#nosdk
    :param apikey:
    :param exp_seconds:
    :return:
    """

    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)

    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


def get_characterglm_response(messages: TextMsgList, meta: CharacterMeta) -> Generator[str, None, None]:
    """ 通过http调用characterglm """
    # Reference: https://open.bigmodel.cn/dev/api#characterglm
    verify_api_key_not_empty()
    url = "https://open.bigmodel.cn/api/paas/v3/model-api/charglm-3/sse-invoke"
    resp = requests.post(
        url,
        headers={"Authorization": generate_token(API_KEY, 1800)},
        json=dict(
            model="charglm-3",
            meta=meta,
            prompt=messages,
            incremental=True)
    )
    resp.raise_for_status()
    
    # 解析响应（非官方实现）
    sep = b':'
    last_event = None
    for line in resp.iter_lines():
        if not line or line.startswith(sep):
            continue
        field, value = line.split(sep, maxsplit=1)
        if field == b'event':
            last_event = value
        elif field == b'data' and last_event == b'add':
            yield value.decode()


def get_characterglm_response_via_sdk(messages: TextMsgList, meta: CharacterMeta) -> Generator[str, None, None]:
    """ 通过旧版sdk调用characterglm """
    # 与get_characterglm_response等价
    # Reference: https://open.bigmodel.cn/dev/api#characterglm
    # 需要安装旧版sdk，zhipuai==1.0.7
    import zhipuai
    verify_api_key_not_empty()
    zhipuai.api_key = API_KEY
    response = zhipuai.model_api.sse_invoke(
        model="charglm-3",
        meta=meta,
        prompt=messages,
        incremental=True
    )
    for event in response.events():
        if event.event == 'add':
            yield event.data


def get_chatglm_response_via_sdk(messages: TextMsgList) -> Generator[str, None, None]:
    """ 通过sdk调用chatglm """
    # reference: https://open.bigmodel.cn/dev/api#glm-3-turbo  `GLM-3-Turbo`相关内容
    # 需要安装新版zhipuai
    from zhipuai import ZhipuAI
    verify_api_key_not_empty()
    client = ZhipuAI(api_key=API_KEY)  # 请填写您自己的APIKey
    response = client.chat.completions.create(
        model="glm-3-turbo",  # 填写需要调用的模型名称
        messages=messages,
        stream=True,
    )
    for chunk in response:
        yield chunk.choices[0].delta.content


def get_chatglm_response_content_sdk(messages: TextMsgList, stream=False) -> Generator[str, None, None]:
    """ 通过sdk调用chatglm """
    # reference: https://open.bigmodel.cn/dev/api#glm-3-turbo  `GLM-3-Turbo`相关内容
    # 需要安装新版zhipuai
    from zhipuai import ZhipuAI
    verify_api_key_not_empty()
    client = ZhipuAI(api_key=API_KEY)  # 请填写您自己的APIKey
    response = client.chat.completions.create(
        model="glm-3-turbo",  # 填写需要调用的模型名称
        messages=messages,
        stream=stream,
    )
    print(response)
    return response.choices[0].message.content


def deal_with_json_response(response: str) -> str:
    """ 处理json格式的响应 """
    resp_list = response.split("\n")
    resp_list = [line.strip() for line in resp_list]
    return "".join(resp_list[1:-1])


def generate_role_info(role_desc: str) -> str:
    """ 
    用chatglm根据描述生成角色的人设信息
    :param role_desc: 角色的描述文本
    :return: 生成的人设信息.json字符串.包含name和info字段
    """

    instruction = f"""
    从下列<<描述文本>>中，抽取人物的人设信息。若文本中不包含人设信息，请推测人物的姓名, 性别、年龄、身高、体重、职业、性格等，并生成一段人设信息。要求：
    1. 只生成人设信息，不要生成任何多余的内容。
    2. 人设信息不能包含敏感词，人物形象需得体。
    3. 尽量用短语描写，而不是完整的句子。
    4. 不要超过100字
    <<描述文本>>：
    {role_desc}
    
    <<返回格式:json字符, 包含如下字段>>
    name: 人物姓名
    info: 人物所有人设信息
    """
    response = get_chatglm_response_content_sdk(
        messages=[
            {
                "role": "user",
                "content": instruction.strip()
            }
        ],
        stream=False
    )
    return deal_with_json_response("".join(response))


def generate_role_appearance(role_profile: str) -> Generator[str, None, None]:
    """ 用chatglm生成角色的外貌描写 """

    instruction = f"""
请从下列文本中，抽取人物的外貌描写。若文本中不包含外貌描写，请你推测人物的性别、年龄，并生成一段外貌描写。要求：
1. 只生成外貌描写，不要生成任何多余的内容。
2. 外貌描写不能包含敏感词，人物形象需得体。
3. 尽量用短语描写，而不是完整的句子。
4. 不要超过50字

文本：
{role_profile}
"""
    return get_chatglm_response_via_sdk(
        messages=[
            {
                "role": "user",
                "content": instruction.strip()
            }
        ]
    )


def generate_chat_scene_prompt(messages: TextMsgList, meta: CharacterMeta) -> Generator[str, None, None]:
    """ 调用chatglm生成cogview的prompt，描写对话场景 """
    instruction = f"""
阅读下面的角色人设与对话，生成一段文字描写场景。

{meta['bot_name']}的人设：
{meta['bot_info']}
    """.strip()

    if meta["user_info"]:
        instruction += f"""

{meta["user_name"]}的人设：
{meta["user_info"]}
""".rstrip()

    if messages:
        instruction += "\n\n对话：" + '\n'.join(
            (meta['bot_name'] if msg['role'] == "assistant" else meta['user_name']) + '：' + msg['content'].strip() for
            msg in messages)

    instruction += """
    
要求如下：
1. 只生成场景描写，不要生成任何多余的内容
2. 描写不能包含敏感词，人物形象需得体
3. 尽量用短语描写，而不是完整的句子
4. 不要超过50字
""".rstrip()
    # print(instruction)

    return get_chatglm_response_via_sdk(
        messages=[
            {
                "role": "user",
                "content": instruction.strip()
            }
        ]
    )


def generate_cogview_image(prompt: str) -> str:
    """ 调用cogview生成图片，返回url """
    # reference: https://open.bigmodel.cn/dev/api#cogview
    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key=API_KEY)  # 请填写您自己的APIKey

    response = client.images.generations(
        model="cogview-3",  # 填写需要调用的模型名称
        prompt=prompt
    )
    return response.data[0].url


if __name__ == '__main__':
    role_description = """
    又名美猴王、齐天大圣。系东胜神州傲来国花果山灵石孕育迸裂见风而成之石猴。在花果山占山为王三五百载。
    后历经八九载，跋山涉水，在西牛贺洲灵台方寸山拜菩提祖师为师，习得七十二变化之本领。
    此后，孙悟空大闹天宫，自封为齐天大圣，被如来佛祖压制于五行山下，无法行动。 
    五百年后唐僧西天取经，路过五行山，揭去符咒，才救下孙悟空。
    孙悟空感激 涕零，经观世音菩萨点拨，拜唐僧为师，同往西天取经。取经路上，孙悟空降妖除怪，屡建奇功，然而两次三番被师傅唐僧误解、驱逐。
    终于师徒四人到达西天雷音寺，取得真经。孙悟空修得正果，加封斗战胜佛。
    孙悟空生性聪明、活泼，勇敢、忠诚，疾恶如仇，在中国文化中已经成为机智与勇敢的化身"""
    resp = generate_role_info(role_description)
    print(resp)
    ret = deal_with_json_response(resp)
    print(ret)
