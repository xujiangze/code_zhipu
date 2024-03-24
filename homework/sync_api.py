import aiohttp
import asyncio
import os
from typing import AsyncGenerator, Dict, TextIO, Optional
from data_types import TextMsgList, CharacterMeta
import jwt
import time

# 智谱开放平台API key，参考 https://open.bigmodel.cn/usercenter/apikeys
API_KEY: str = os.getenv("API_KEY", "")


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


class ApiKeyNotSet(ValueError):
    pass


def verify_api_key_not_empty():
    if not API_KEY:
        raise ApiKeyNotSet


async def get_characterglm_response(messages: TextMsgList, meta: CharacterMeta) -> AsyncGenerator[str, None]:
    """ 通过http调用characterglm (异步版本) """
    verify_api_key_not_empty()
    url = "https://open.bigmodel.cn/api/paas/v3/model-api/charglm-3/sse-invoke"
    headers = {
        "Authorization": generate_token(API_KEY, 1800)
    }
    data = {
        "model": "charglm-3",
        "meta": meta,
        "prompt": messages,
        "incremental": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            resp.raise_for_status()
            async for line in resp.content:
                line = line.decode()
                if not line or line.startswith(':'):
                    continue
                ret = line.split(':')
                if len(ret) != 2:
                    continue
                field = ret[0]
                value = ret[1]
                if field == 'event':
                    last_event = value.strip()
                elif field == 'data' and last_event == 'add':
                    yield value.strip()


async def characterglm_example():
    # 创建TextMsgList和CharacterMeta实例
    character_meta = {
        "user_info": "",
        "bot_info": "小白，性别女，17岁，平溪孤儿院的孩子。小白患有先天的白血病，头发为银白色。小白身高158cm，体重43kg。小白的名字是孤儿院院长给起的名字，因为小白是在漫天大雪白茫茫的一片土地上被捡到的。小白经常穿一身破旧的红裙子，只是为了让自己的气色看上去红润一些。小白初中毕业，没有上高中，学历水平比较低。小白在孤儿院相处最好的一个人是阿南，小白喊阿南哥哥。阿南对小白很好。",
        "user_name": "用户",
        "bot_name": "小白"
    }
    messages = [
        {"role": "assistant", "content": "哥哥，我会死吗？"},
        {"role": "user", "content": "（微信）怎么会呢？医生说你的病情已经好转了"}
    ]

    async for response in get_characterglm_response(messages, character_meta):
        print(response)


if __name__ == '__main__':
    # 运行异步主函数
    asyncio.run(characterglm_example())
