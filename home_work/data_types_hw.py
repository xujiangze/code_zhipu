"""
相关数据类型的定义
"""
from typing import Literal, TypedDict, List, Union, Optional, TYPE_CHECKING
import dataclasses

import pydantic

# pydantic 是一个 Python 库，用于数据解析和校验，它使用 Python 类型提示来验证数据。
# pydantic 的核心功能是提供一个 BaseModel 类，用户可以继承这个类来创建自己的数据模型，并利用类型提示来指定数据类型和校验规则


if TYPE_CHECKING:
    import streamlit.elements.image


class TextMsg(pydantic.BaseModel):
    """文本消息"""

    # 在类属性标注的下一行用三引号注释，vscode中
    role: Literal["user", "assistant"]
    """消息来源"""
    content: str
    """消息内容"""


class ImageMsg(pydantic.BaseModel):
    """图片消息"""
    role: Literal["image"]
    image: "streamlit.elements.image.ImageOrImageList"
    """图片内容"""
    caption: Optional[Union[str, List[str]]]
    """说明文字"""


# 定义一个类型别名，它是一个列表，列表中的元素是TextMsg或ImageMsg
Msg = Union[TextMsg, ImageMsg]

# 定义一个类型别名，它是一个列表，列表中的元素是TextMsg
TextMsgList = List[TextMsg]

# 定义一个类型别名，它是一个列表，列表中的元素是Msg
MsgList = List[Msg]


class CharacterMeta(pydantic.BaseModel):
    """角色扮演设定，它是CharacterGLM API所需的参数"""
    user_info: str
    """用户人设"""
    bot_info: str
    """角色人设"""
    bot_name: str
    """bot扮演的角色的名字"""
    user_name: str
    """用户的名字"""


def filter_text_msg(messages: MsgList) -> TextMsgList:
    """
    过滤出文本消息
    :param messages:
    :return:
    """
    return [m for m in messages if m["role"] != "image"]


# dataclasses 是 Python 3.7 引入的一个标准库，它提供了一种简洁的方式来自动生成特殊方法，
# 如 __init__()、__repr__()、__eq__() 等，用于定义数据类。
@dataclasses.dataclass
class Person:
    name: str
    age: int


class User(pydantic.BaseModel):
    id: int
    name: str = "john Doe"
    friends: List[int] = []


if __name__ == "__main__":
    # 尝试在VSCode等IDE中自己敲一遍下面的代码，观察IDE能提供哪些代码提示
    # 其中提供了检查TextMsg(role="abc", content="xxx") 会出错
    text_msg = TextMsg(role="user", content="xxx")
    text_msg.content = 42
    # text_msg["content"] = "42"  # 如果使用 baseModel就只有属性这种
    print(type(text_msg))
    print(text_msg)

    # 作业1.
    # 测试Person. (不会自动生成json格式,而是生成的是基础类格式)
    person_1 = Person(name="jan", age=123)
    print(person_1)
    # 可手动转换为字典
    print(person_1.__dict__)
    # 好处,是用这种方式可以在jetbrain点进去直接到类的声明, 对于jetbrain来说,

    user = User(id=123, name="join")
    print(user)
    print(user.name)
    print(user.__dict__)
    print(user.json())  # 支持json
    # 支持解析
    user_dict = {'id': 123, 'friends': [456, 789]}
    user = User.parse_obj(user_dict)
    print(user)
