from dotenv import load_dotenv
load_dotenv()

from api import generate_cogview_image


def cogview_example(style="国画", content="孤舟蓑笠翁，独钓寒江雪"):
    image_prompt = f"你是一个绘画大师, 请用{style}风格绘制主题: <<{content}>>"
    image_url = generate_cogview_image(image_prompt)
    
    print("image_prompt:")
    print(image_prompt)
    print("image_url:")
    print(image_url)


if __name__ == "__main__":
    # 油画、水墨画、动漫
    cogview_example("油画", "孤舟蓑笠翁，独钓寒江雪")
    cogview_example("水墨画", "孤舟蓑笠翁，独钓寒江雪")
    cogview_example("动漫", "孤舟蓑笠翁，独钓寒江雪")

