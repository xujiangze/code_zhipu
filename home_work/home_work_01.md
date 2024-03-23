# home_work_01
见代码: data_types_hw.py

## dataclasses

dataclasses 是 Python 3.7 引入的一个标准库，它提供了一种简洁的方式来自动生成特殊方法，
如 __init__()、__repr__()、__eq__() 等，用于定义数据类。在 Python 3.10 中，dataclasses 被进一步集成到 Python 的类型提示系统中。
使用 dataclasses 需要先导入它，然后使用 @dataclasses.dataclass 装饰器来装饰一个类。
这个装饰器会自动添加一些特殊方法到类中，使得类的实例可以像普通数据一样使用。

下面是一些 dataclasses 的基本用例：
```python
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int

# 创建一个实例
person = Person(name="Alice", age=30)

# 输出实例的字符串表示
print(person)
```
ps:  该案例对于jetbrain来说更有好一些. 可以直接通过点击的方式直接跳转到类定义.

## pydantic
pydantic 是一个 Python 库，用于数据解析和校验，它使用 Python 类型提示来验证数据。pydantic 的核心功能是提供一个 BaseModel 类，
用户可以继承这个类来创建自己的数据模型，并利用类型提示来指定数据类型和校验规则。

```python

from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: List[int] = []

# 创建一个实例
user = User(id=123, signup_ts='2022-01-01T12:22', friends=[456, 789])

# 打印实例
print(user)  # 输出: id=123 name='John Doe' signup_ts=datetime.datetime(2022, 1, 1, 12, 22) friends=[456, 789]

# 访问属性
print(user.id)  # 输出: 123

```
