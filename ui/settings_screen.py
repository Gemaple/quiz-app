"""
设置屏幕
AI解析配置、关于、数据管理
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
import db
from ai_helper import (
    AI_PRESETS, get_preset_api_key, save_preset_api_key,
    get_preset_model, save_preset_model, analyze_question
)
from kivy.clock import Clock
import threading


class Tab(MDFloatLayout, MDTabsBase):
    pass


class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_preset = None

    def on_enter(self):
        self.show_main()

    def show_main(self):
        """显示设置主界面"""
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

        title = MDLabel(text="设置", font_style="H5", size_hint_y=None, height=50)
        layout.add_widget(title)

        scroll = MDScrollView()
        content = MDBoxLayout(orientation='vertical', spacing=15, size_hint_y=None, padding=10)
        content.bind(minimum_height=content.setter('height'))

        # AI解析设置
        ai_card = MDCard(orientation="vertical", padding=15, spacing=10)
        ai_card.add_widget(MDLabel(text="🤖 AI 解析设置", font_style="Subtitle1"))
        ai_card.add_widget(MDLabel(
            text="配置多个 AI 服务，解析题目时可自由选择。点击下方按钮配置对应服务的 API Key。",
            theme_text_color="Secondary"
        ))

        colors = {
            "deepseek": (0.1, 0.5, 0.9, 1),
            "siliconflow": (0.2, 0.7, 0.3, 1),
            "doubao": (0.95, 0.6, 0.1, 1),
            "zhipu": (0.6, 0.3, 0.8, 1),
        }

        for key, preset in AI_PRESETS.items():
            has_key = "✓ 已配置" if get_preset_api_key(key) else "✗ 未配置"
            btn = MDFillRoundFlatButton(
                text=f"{preset['name']} - {has_key}",
                md_bg_color=colors.get(key, (0.5, 0.5, 0.5, 1)),
                size_hint_y=None,
                height=50
            )
            btn.bind(on_press=lambda x, k=key: self.show_preset_config(k))
            ai_card.add_widget(btn)

        content.add_widget(ai_card)

        # 数据管理
        data_card = MDCard(orientation="vertical", padding=15, spacing=10)
        data_card.add_widget(MDLabel(text="💾 数据管理", font_style="Subtitle1"))
        data_card.add_widget(MDLabel(
            text="手机和电脑数据互通方法：\n"
                 "1. 电脑端导出题库为 Excel\n"
                 "2. 将 Excel 文件传到手机\n"
                 "3. 手机端「题库管理」→「导入 Excel」\n"
                 "4. 做题记录同理可通过导出/导入同步",
            theme_text_color="Secondary"
        ))
        content.add_widget(data_card)

        # 关于
        about_card = MDCard(orientation="vertical", padding=15, spacing=10)
        about_card.add_widget(MDLabel(text="ℹ️ 关于", font_style="Subtitle1"))
        about_card.add_widget(MDLabel(text="答题助手 安卓版 v1.0.0"))
        about_card.add_widget(MDLabel(text="基于 Kivy + KivyMD 开发"))
        about_card.add_widget(MDLabel(text="支持：做题/学习/错题本/Excel导入/AI解析"))
        content.add_widget(about_card)

        scroll.add_widget(content)
        layout.add_widget(scroll)

        bottom = MDBoxLayout(size_hint_y=None, height=50)
        back_btn = MDFlatButton(text="返回首页")
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        bottom.add_widget(back_btn)
        layout.add_widget(bottom)

        self.add_widget(layout)

    def show_preset_config(self, preset_name):
        """显示预设配置界面"""
        self.current_preset = preset_name
        preset = AI_PRESETS[preset_name]

        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=10)

        top_bar = MDBoxLayout(size_hint_y=None, height=50)
        back_btn = MDFlatButton(text="返回设置")
        back_btn.bind(on_press=lambda x: self.show_main())
        top_bar.add_widget(back_btn)
        layout.add_widget(top_bar)

        title = MDLabel(text=f"{preset['name']} 配置", font_style="H6", size_hint_y=None, height=40)
        layout.add_widget(title)

        desc = MDLabel(text=preset['desc'], theme_text_color="Secondary", size_hint_y=None, height=30)
        layout.add_widget(desc)

        # API地址（只读）
        layout.add_widget(MDLabel(text="API 地址：", size_hint_y=None, height=30))
        api_base = MDTextField(text=preset['api_base'], disabled=True, size_hint_y=None, height=50)
        layout.add_widget(api_base)

        # API Key
        layout.add_widget(MDLabel(text="API Key：", size_hint_y=None, height=30))
        self.api_key_input = MDTextField(
            text=get_preset_api_key(preset_name),
            hint_text="请输入 API Key",
            password=True,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.api_key_input)

        # 模型名称
        layout.add_widget(MDLabel(text="模型名称：", size_hint_y=None, height=30))
        self.model_input = MDTextField(
            text=get_preset_model(preset_name),
            hint_text="模型名称",
            size_hint_y=None,
            height=50
        )
        if preset_name == "doubao":
            self.model_input.hint_text = "请输入接入点ID（ep-开头）"
        layout.add_widget(self.model_input)

        layout.add_widget(MDLabel())

        # 按钮
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        test_btn = MDFillRoundFlatButton(text="测试连接", md_bg_color=(0.1, 0.5, 0.9, 1))
        test_btn.bind(on_press=self.test_connection)
        btn_layout.add_widget(test_btn)
        save_btn = MDFillRoundFlatButton(text="保存", md_bg_color=(0.2, 0.7, 0.3, 1))
        save_btn.bind(on_press=self.save_preset)
        btn_layout.add_widget(save_btn)
        layout.add_widget(btn_layout)

        self.add_widget(layout)

    def save_preset(self, instance):
        """保存预设配置"""
        save_preset_api_key(self.current_preset, self.api_key_input.text.strip())
        save_preset_model(self.current_preset, self.model_input.text.strip())
        self.show_dialog("成功", f"{AI_PRESETS[self.current_preset]['name']} 配置已保存！")

    def test_connection(self, instance):
        """测试连接"""
        # 先保存
        save_preset_api_key(self.current_preset, self.api_key_input.text.strip())
        save_preset_model(self.current_preset, self.model_input.text.strip())

        if not get_preset_api_key(self.current_preset):
            self.show_dialog("提示", "请先填写 API Key！")
            return

        self.show_dialog("测试中", "正在测试连接，请稍候...")

        def worker():
            result = analyze_question("1+1等于几？", ["1", "2", "3", "4"], "single", self.current_preset)
            Clock.schedule_once(lambda dt: self.show_test_result(result))

        threading.Thread(target=worker, daemon=True).start()

    def show_test_result(self, result):
        self.show_dialog("测试结果", result[:500])

    def show_dialog(self, title, text):
        dialog = MDDialog(title=title, text=text, buttons=[
            MDFlatButton(text="确定", on_release=lambda x: dialog.dismiss())
        ])
        dialog.open()
