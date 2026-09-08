"""
学习模式屏幕
浏览题目、查看答案解析、添加笔记、AI解析
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
import db
from ai_helper import analyze_question, AI_PRESETS, get_preset_api_key


class ReviewScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = []
        self.current_index = 0
        self.ai_thread = None

    def on_enter(self):
        self.load_questions()
        self.show_browser()

    def load_questions(self):
        """加载所有题目"""
        self.questions = db.get_all_questions()

    def show_browser(self):
        """显示题目浏览界面"""
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

        # 顶部筛选
        filter_bar = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        self.subject_spinner = Spinner(text="全部科目", values=self.get_subject_list())
        self.subject_spinner.bind(text=self.on_filter_change)
        filter_bar.add_widget(self.subject_spinner)
        self.type_spinner = Spinner(text="全部题型", values=["全部题型", "单选题", "多选题", "判断题", "案例分析题"])
        self.type_spinner.bind(text=self.on_filter_change)
        filter_bar.add_widget(self.type_spinner)
        layout.add_widget(filter_bar)

        # 题目列表
        scroll = MDScrollView()
        self.question_list = MDList()
        self.refresh_list()
        scroll.add_widget(self.question_list)
        layout.add_widget(scroll)

        # 底部
        bottom = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        back_btn = MDFlatButton(text="返回首页")
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        bottom.add_widget(back_btn)
        self.count_label = MDLabel(text=f"共 {len(self.filtered_questions)} 题", halign="right")
        bottom.add_widget(self.count_label)
        layout.add_widget(bottom)

        self.add_widget(layout)

    def get_subject_list(self):
        """获取科目列表"""
        result = ["全部科目"]
        tree = db.get_subject_tree()
        for top, children in tree:
            result.append(top["name"])
            for child in children:
                result.append("  └ " + child["name"])
        return result

    def on_filter_change(self, instance, value):
        self.refresh_list()

    def refresh_list(self):
        """刷新题目列表"""
        self.question_list.clear_widgets()
        type_map = {"全部题型": None, "单选题": "single", "多选题": "multiple", "判断题": "judge", "案例分析题": "case"}
        q_type = type_map.get(self.type_spinner.text, None)

        # 科目筛选
        subject_name = self.subject_spinner.text.replace("  └ ", "")
        subject_id = None
        if subject_name != "全部科目":
            for s in db.get_subjects():
                if s["name"] == subject_name:
                    subject_id = s["id"]
                    break

        self.filtered_questions = db.get_all_questions(q_type, subject_id)

        type_names = {"single": "单选", "multiple": "多选", "judge": "判断", "case": "案例"}
        for i, q in enumerate(self.filtered_questions):
            item = OneLineListItem(
                text=f"[{type_names.get(q['q_type'], q['q_type'])}] {q['question_text'][:40]}...",
                on_press=lambda x, idx=i: self.show_detail(idx)
            )
            self.question_list.add_widget(item)

        if hasattr(self, 'count_label'):
            self.count_label.text = f"共 {len(self.filtered_questions)} 题"

    def show_detail(self, index):
        """显示题目详情"""
        self.current_index = index
        q = self.filtered_questions[index]
        self.clear_widgets()

        layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

        # 顶部导航
        top_bar = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=50)
        back_btn = MDFlatButton(text="返回列表")
        back_btn.bind(on_press=lambda x: self.show_browser())
        top_bar.add_widget(back_btn)
        top_bar.add_widget(MDLabel(text=f"{index+1}/{len(self.filtered_questions)}", halign="right"))
        layout.add_widget(top_bar)

        scroll = MDScrollView()
        content = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=10)
        content.bind(minimum_height=content.setter('height'))

        type_names = {"single": "单选题", "multiple": "多选题", "judge": "判断题", "case": "案例分析题"}
        content.add_widget(MDLabel(text=f"【{type_names.get(q['q_type'], q['q_type'])}】", theme_text_color="Primary", font_style="Subtitle1"))

        # 题干
        q_card = MDCard(orientation="vertical", padding=15, spacing=10)
        q_card.add_widget(MDLabel(text="题干：", font_style="Subtitle2"))
        q_card.add_widget(MDLabel(text=q['question_text']))
        content.add_widget(q_card)

        # 选项
        options = q.get('options', [])
        if options:
            opt_card = MDCard(orientation="vertical", padding=15, spacing=5)
            opt_card.add_widget(MDLabel(text="选项：", font_style="Subtitle2"))
            for i, opt in enumerate(options):
                opt_card.add_widget(MDLabel(text=f"{chr(65+i)}. {opt}"))
            content.add_widget(opt_card)

        # 答案
        ans_card = MDCard(orientation="vertical", padding=15, spacing=5, md_bg_color=(0.9, 1, 0.9, 1))
        ans_card.add_widget(MDLabel(text=f"正确答案：{q.get('answer', '')}", theme_text_color="Success", font_style="Subtitle2"))
        if q.get('analysis'):
            ans_card.add_widget(MDLabel(text=f"解析：{q['analysis']}"))
        content.add_widget(ans_card)

        # AI解析按钮
        ai_btn = MDFillRoundFlatButton(
            text="AI 智能解析",
            md_bg_color=(0.1, 0.5, 0.9, 1),
            size_hint_y=None,
            height=50
        )
        ai_btn.bind(on_press=self.show_ai_selector)
        content.add_widget(ai_btn)

        self.ai_result_label = MDLabel(text="", size_hint_y=None)
        self.ai_result_label.bind(texture_size=lambda x, v: setattr(self.ai_result_label, 'height', v[1]))
        content.add_widget(self.ai_result_label)

        # 笔记
        note_card = MDCard(orientation="vertical", padding=15, spacing=10)
        note_card.add_widget(MDLabel(text="✍ 我的笔记：", font_style="Subtitle2"))
        self.note_input = MDTextField(
            text=q.get('note_text', ''),
            hint_text="添加你对这道题的理解...",
            multiline=True,
            size_hint_y=None,
            height=120
        )
        note_card.add_widget(self.note_input)
        save_note_btn = MDFillRoundFlatButton(text="保存笔记", md_bg_color=(0.2, 0.7, 0.3, 1), size_hint_y=None, height=45)
        save_note_btn.bind(on_press=self.save_note)
        note_card.add_widget(save_note_btn)
        content.add_widget(note_card)

        scroll.add_widget(content)
        layout.add_widget(scroll)

        # 底部导航
        nav_bar = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        prev_btn = MDFlatButton(text="上一题", disabled=(index == 0))
        prev_btn.bind(on_press=lambda x: self.show_detail(index - 1))
        nav_bar.add_widget(prev_btn)
        next_btn = MDFillRoundFlatButton(text="下一题", disabled=(index >= len(self.filtered_questions) - 1))
        next_btn.bind(on_press=lambda x: self.show_detail(index + 1))
        nav_bar.add_widget(next_btn)
        layout.add_widget(nav_bar)

        self.add_widget(layout)

    def show_ai_selector(self, instance):
        """显示AI服务选择"""
        items = []
        for key, preset in AI_PRESETS.items():
            has_key = "✓" if get_preset_api_key(key) else "✗"
            items.append(f"{preset['name']} {has_key}")
        items.append("默认配置")

        menu_items = [{"text": item, "viewclass": "OneLineListItem",
                       "on_press": lambda x=item: self.do_ai_analyze(items.index(x))} for item in items]
        self.ai_menu = MDDropdownMenu(caller=instance, items=menu_items, width_mult=4)
        self.ai_menu.open()

    def do_ai_analyze(self, idx):
        """执行AI解析"""
        self.ai_menu.dismiss()
        preset_keys = list(AI_PRESETS.keys())
        preset_name = preset_keys[idx] if idx < len(preset_keys) else None

        if not get_preset_api_key(preset_name):
            self.show_dialog("提示", f"{AI_PRESETS[preset_name]['name']} 未配置 API Key，请先在设置中配置！")
            return

        q = self.filtered_questions[self.current_index]
        self.ai_result_label.text = "正在调用 AI 解析，请稍候..."

        # 用线程避免卡顿
        import threading
        def worker():
            result = analyze_question(q['question_text'], q.get('options', []), q['q_type'], preset_name)
            Clock.schedule_once(lambda dt: self.set_ai_result(result))
        threading.Thread(target=worker, daemon=True).start()

    def set_ai_result(self, result):
        self.ai_result_label.text = f"AI解析：\n{result}"

    def save_note(self, instance):
        q = self.filtered_questions[self.current_index]
        note = self.note_input.text.strip()
        db.update_question_note(q['id'], note)
        q['note_text'] = note
        self.show_dialog("成功", "笔记已保存！")

    def show_dialog(self, title, text):
        dialog = MDDialog(title=title, text=text, buttons=[
            MDFlatButton(text="确定", on_release=lambda x: dialog.dismiss())
        ])
        dialog.open()
