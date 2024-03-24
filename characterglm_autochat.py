"""
一个简单的demo，调用CharacterGLM实现角色扮演，调用CogView生成图片，调用ChatGLM生成CogView所需的prompt。

依赖：
pyjwt
requests
streamlit
zhipuai
python-dotenv

运行方式：
```bash
streamlit run characterglm_api_demo_streamlit.py
```
"""
import os
import itertools
from typing import Iterator, Optional

import streamlit as st
from dotenv import load_dotenv

# 通过.env文件设置环境变量
# reference: https://github.com/theskumar/python-dotenv
load_dotenv()

import api
from api import generate_chat_scene_prompt, generate_role_appearance, get_characterglm_response, generate_cogview_image
from data_types import TextMsg, ImageMsg, TextMsgList, MsgList, filter_text_msg

st.set_page_config(page_title="CharacterGLM API Demo", page_icon="🤖", layout="wide")
debug = os.getenv("DEBUG", "yes").lower() in ("1", "yes", "y", "true", "t", "on")


class Tools(object):
    @staticmethod
    def update_api_key(key: Optional[str] = None):
        if debug:
            print(f'update_api_key. st.session_state["API_KEY"] = {st.session_state["API_KEY"]}, key = {key}')
        key = key or st.session_state["API_KEY"]
        if key:
            api.API_KEY = key

    @staticmethod
    def output_stream_response(response_stream: Iterator[str], placeholder):
        content = ""
        for content in itertools.accumulate(response_stream):
            placeholder.markdown(content)
        return content


class SessionHelper(object):
    @staticmethod
    def init_session_state():
        # 初始化
        if "history" not in st.session_state:
            st.session_state["history"] = []
        if "meta" not in st.session_state:
            st.session_state["meta"] = {
                "user_info": "",
                "bot_info": "",
                "bot_name": "",
                "user_name": "",
                "image_style": "",
            }

    @staticmethod
    def init_session_history():
        st.session_state["history"] = []

    @staticmethod
    def verify_meta() -> bool:
        # 检查`角色名`和`角色人设`是否空，若为空，则弹出提醒
        if st.session_state["meta"]["bot_name"] == "" or st.session_state["meta"]["bot_info"] == "":
            st.error("角色名和角色人设不能为空")
            return False
        else:
            return True

    @staticmethod
    def clean_meta():
        """
        清空人设
        :return:
        """
        st.session_state["meta"] = {
            "user_info": "",
            "bot_info": "",
            "bot_name": "",
            "user_name": ""
        }
        st.rerun()

    @staticmethod
    def clean_history():
        """
        清空对话历史
        :return:
        """
        st.session_state["history"] = []
        st.rerun()

    @staticmethod
    def show_api_key():
        print(f"API_KEY = {api.API_KEY}")

    @staticmethod
    def show_meta():
        print(f"meta = {st.session_state['meta']}")

    @staticmethod
    def show_history():
        print(f"history = {st.session_state['history']}")


class ViewDrawer(object):
    @staticmethod
    def draw_character_info():
        """
        绘制bot角色信息输入框
        :return:
        """
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.text_input(label="角色名", key="bot_name",
                              on_change=lambda: st.session_state["meta"].update(bot_name=st.session_state["bot_name"]),
                              help="模型所扮演的角色的名字，不可以为空")
                st.text_area(label="角色人设", key="bot_info",
                             on_change=lambda: st.session_state["meta"].update(bot_info=st.session_state["bot_info"]),
                             help="角色的详细人设信息，不可以为空")
                st.selectbox(label="生成风格",
                             options=["二次元风格", "写实风格", "童话", "玄幻", "修真", "蒸汽朋克", "哥特式"],
                             key="image_style",
                             on_change=lambda: st.session_state["meta"].update(
                                 image_style=st.session_state["image_style"]))

            with col2:
                st.text_input(label="用户名", value="用户", key="user_name",
                              on_change=lambda: st.session_state["meta"].update(
                                  user_name=st.session_state["user_name"]),
                              help="用户的名字，默认为用户")
                st.text_area(label="用户人设", value="", key="user_info",
                             on_change=lambda: st.session_state["meta"].update(user_info=st.session_state["user_info"]),
                             help="用户的详细人设信息，可以为空")

    @staticmethod
    def draw_help_buttons():
        button_labels = {
            "clear_meta": "清空人设",
            "clear_history": "清空对话历史",
            "gen_picture": "生成图片",
        }
        if debug:
            button_labels.update({
                "show_api_key": "查看API_KEY",
                "show_meta": "查看meta",
                "show_history": "查看历史"
            })

        # 在同一行排列按钮
        with st.container():
            n_button = len(button_labels)
            cols = st.columns(n_button)
            button_key_to_col = dict(zip(button_labels.keys(), cols))

            # 清空人设
            with button_key_to_col["clear_meta"]:
                st.button(button_labels["clear_meta"], key="clear_meta", on_click=SessionHelper.clean_meta)

            # 清空对话历史
            with button_key_to_col["clear_history"]:
                st.button(button_labels["clear_history"], key="clear_history", on_click=SessionHelper.clean_history)

            # 生成图片
            with button_key_to_col["gen_picture"]:
                gen_picture = st.button(button_labels["gen_picture"], key="gen_picture")

            if debug:
                # 查看API_KEY
                with button_key_to_col["show_api_key"]:
                    st.button(button_labels["show_api_key"], key="show_api_key", on_click=SessionHelper.show_api_key)

                # 查看meta
                with button_key_to_col["show_meta"]:
                    st.button(button_labels["show_meta"], key="show_meta", on_click=SessionHelper.show_meta)

                # 查看历史
                with button_key_to_col["show_history"]:
                    st.button(button_labels["show_history"], key="show_history", on_click=SessionHelper.show_history)

        return gen_picture

    @staticmethod
    def draw_history():
        # 展示对话历史
        for msg in st.session_state["history"]:
            if msg["role"] == "user":
                with st.chat_message(name="user", avatar="user"):
                    st.markdown(msg["content"])
            elif msg["role"] == "assistant":
                with st.chat_message(name="assistant", avatar="assistant"):
                    st.markdown(msg["content"])
            elif msg["role"] == "image":
                with st.chat_message(name="assistant", avatar="assistant"):
                    st.image(msg["image"], caption=msg.get("caption", None))
            else:
                raise Exception("Invalid role")

    @staticmethod
    def draw_empty_chat_message():
        with st.chat_message(name="user", avatar="user"):
            input_placeholder = st.empty()
        with st.chat_message(name="assistant", avatar="assistant"):
            message_placeholder = st.empty()

        return input_placeholder, message_placeholder

    @staticmethod
    def draw_chat_input():
        query = st.chat_input("开始对话吧")  # 获取用户输入
        return query

    @staticmethod
    def draw_new_image():
        """生成一张图片，并展示在页面上"""
        if not SessionHelper.verify_meta():
            return
        text_messages = filter_text_msg(st.session_state["history"])
        if text_messages:
            # 若有对话历史，则结合角色人设和对话历史生成图片
            image_prompt = "".join(
                generate_chat_scene_prompt(
                    text_messages[-10:],
                    meta=st.session_state["meta"]
                )
            )
        else:
            # 若没有对话历史，则根据角色人设生成图片
            image_prompt = "".join(generate_role_appearance(st.session_state["meta"]["bot_info"]))

        if not image_prompt:
            st.error("调用chatglm生成Cogview prompt出错")
            return

        image_style = st.session_state["meta"].get("image_style", "二次元风格")
        image_prompt = f'生成风格: {image_style}。' + image_prompt.strip()

        print(f"image_prompt = {image_prompt}")
        n_retry = 3
        st.markdown("正在生成图片，请稍等...")
        for i in range(n_retry):
            try:
                img_url = generate_cogview_image(image_prompt)
            except Exception as e:
                if i < n_retry - 1:
                    st.error("遇到了一点小问题，重试中...")
                else:
                    st.error("又失败啦，点击【生成图片】按钮可再次重试")
                    return
            else:
                break
        img_msg = ImageMsg({"role": "image", "image": img_url, "caption": image_prompt})
        # 若history的末尾有图片消息，则替换它，（重新生成）
        # 否则，append（新增）
        while st.session_state["history"] and st.session_state["history"][-1]["role"] == "image":
            st.session_state["history"].pop()
        st.session_state["history"].append(img_msg)
        st.rerun()


def init_session():
    # 设置API KEY
    api_key = st.sidebar.text_input("API_KEY", value=os.getenv("API_KEY", ""), key="API_KEY", type="password",
                                    on_change=Tools.update_api_key)
    Tools.update_api_key(api_key)

    # 初始化
    SessionHelper.init_session_state()


def init_drawer_setting():
    # 绘制角色信息输入框
    ViewDrawer.draw_character_info()
    # 绘制帮助按钮
    gen_picture = ViewDrawer.draw_help_buttons()
    return gen_picture


def init_drawer_history():
    # 展示对话历史
    ViewDrawer.draw_history()


def init_draw_user_input():
    input_placeholder, message_placeholder = ViewDrawer.draw_empty_chat_message()
    query = ViewDrawer.draw_chat_input()  # 获取用户输入
    if not query:
        return
    else:
        if not SessionHelper.verify_meta():
            return

        if not api.API_KEY:
            st.error("未设置API_KEY")

        # 展示用户输入
        input_placeholder.markdown(query)
        st.session_state["history"].append(TextMsg({"role": "user", "content": query}))

        # 获取回复
        response_stream = get_characterglm_response(filter_text_msg(st.session_state["history"]),
                                                    meta=st.session_state["meta"])
        bot_response = Tools.output_stream_response(response_stream, message_placeholder)

        if not bot_response:
            message_placeholder.markdown("生成出错")
            st.session_state["history"].pop()
        else:
            st.session_state["history"].append(TextMsg({"role": "assistant", "content": bot_response}))


def main():
    # 初始化session信息
    init_session()

    # 绘制设定框
    gen_picture = init_drawer_setting()

    # 绘制历史
    init_drawer_history()

    # 绘制新图片, 以防卡主放历史后面
    if gen_picture:
        ViewDrawer.draw_new_image()

    # 绘制用户输入框
    init_draw_user_input()


main()
