import gradio as gr
import openai


def change_api_key(api_key):
    key = api_key.strip()
    openai.api_key = key
    print(f"change openai.api_key:{openai.api_key}")


with gr.Blocks(theme=gr.themes.Monochrome()) as demo:
    with gr.Tab("配置"):
        box_api = gr.Textbox(value=openai.api_key, placeholder="请输入你的OpenAI API Key，或者去utils.py中永久修改",
                             label="openai api key", interactive=True)

        box_api.change(fn=change_api_key, inputs=[box_api])
        with gr.Row():
            gr.Textbox(placeholder="请输入你的名字", label="名字", interactive=True, scale=4)
            gr.Dropdown(choices=["混沌之心", "虚空之力"], label="初始技能", interactive=True, scale=8)
            gr.Button(value="随机", interactive=True, scale=1)

    with gr.Tab("开始人生"):
        gr.Chatbot(show_label=False, render_markdown=False)
        with gr.Row():
            gr.Button("下一轮冒险")

        with gr.Row():
            gr.Dropdown(choices=["无"], label="交谈选项", interactive=True, scale=8)
            gr.Dropdown(choices=[], label="技能", interactive=True, scale=4)
            gr.Button("确认", scale=1)

    with gr.Tab("世界管理"):
        gr.Dropdown(choices=[], label="历史人物")

PORT = 8894


def auto_opentab_delay():
    import threading, webbrowser, time
    print(f"（亮色主题）: http://localhost:{PORT}")
    print(f"（暗色主题）: http://localhost:{PORT}/?__theme=dark")

    def opentab():
        time.sleep(2)  # 打开浏览器
        webbrowser.open_new_tab(f"http://localhost:{PORT}/?__theme=dark")

    threading.Thread(target=opentab, name="open-browser", daemon=True).start()


auto_opentab_delay()

demo.launch(server_name="0.0.0.0", server_port=PORT, debug=True)
