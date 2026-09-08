"""
错题本屏幕
查看错题、错题练习、导出错题
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.dialog import MDDialog
from kivy.uix.spinner import Spinner
import db


class WrongScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wrong_questions = []

    def on_enter(self):
        self.load_wrong()
        self.show_list()

    def load_wrong(self):
        """加载错题"""
        self.wrong_questions = db.get_wrong_questions()

    def show_list(self):
        """显示错题列表"""
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

        title = MDLabel(text="错题本", font_style="H5", size_hint_y=None, height=50)
        layout.add_widget(title)

        # 统计
        stats = MDLabel(
            text=f"共 {len(self.wrong_questions)} 道错题",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=30
        )
        layout.add_widget(stats)

        # 操作按钮
        btn_bar = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
        practice_btn = MDFillRoundFlatButton(text="错题练习", md_bg_color=(0.9, 0.5, 0.1, 1))
        practice_btn.bind(on_press=self.start_practice)
        btn_bar.add_widget(practice_btn)
        export_btn = MDFillRoundFlatButton(text="导出错题", md_bg_color=(0.2, 0.7, 0.3, 1))
        export_btn.bind(on_press=self.export_wrong)
        btn_bar.add_widget(export_btn)
        layout.add_widget(btn_bar)

        # 错题列表
        scroll = MDScrollView()
        list_widget = MDList()
        type_names = {"single": "单选", "multiple": "多选", "judge": "判断", "case": "案例"}

        if not self.wrong_questions:
            list_widget.add_widget(TwoLineListItem(text="暂无错题", secondary="去答题吧！"))
        else:
            for q in self.wrong_questions:
                item = TwoLineListItem(
                    text=f"[{type_names.get(q['q_type'], q['q_type'])}] {q['question_text'][:40]}...",
                    secondary=f"错误次数：{q.get('wrong_count', 1)} | 正确答案：{q.get('answer', '')}",
                    on_press=lambda x, item_q=q: self.show_detail(item_q)
                )
                list_widget.add_widget(item)

        scroll.add_widget(list_widget)
        layout.add_widget(scroll)

        # 底部
        bottom = MDBoxLayout(size_hint_y=None, height=50)
        back_btn = MDFlatButton(text="返回首页")
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        bottom.add_widget(back_btn)
        layout.add_widget(bottom)

        self.add_widget(layout)

    def show_detail(self, q):
        """显示错题详情"""
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=10)

        top_bar = MDBoxLayout(size_hint_y=None, height=50)
        back_btn = MDFlatButton(text="返回列表")
        back_btn.bind(on_press=lambda x: self.show_list())
        top_bar.add_widget(back_btn)
        layout.add_widget(top_bar)

        scroll = MDScrollView()
        content = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, padding=10)
        content.bind(minimum_height=content.setter('height'))

        type_names = {"single": "单选题", "multiple": "多选题", "judge": "判断题", "case": "案例分析题"}
        content.add_widget(MDLabel(text=f"【{type_names.get(q['q_type'], q['q_type'])}】", theme_text_color="Primary"))

        q_card = MDCard(orientation="vertical", padding=15, spacing=10)
        q_card.add_widget(MDLabel(text="题干：", font_style="Subtitle2"))
        q_card.add_widget(MDLabel(text=q['question_text']))
        content.add_widget(q_card)

        options = q.get('options', [])
        if options:
            opt_card = MDCard(orientation="vertical", padding=15, spacing=5)
            for i, opt in enumerate(options):
                opt_card.add_widget(MDLabel(text=f"{chr(65+i)}. {opt}"))
            content.add_widget(opt_card)

        ans_card = MDCard(orientation="vertical", padding=15, spacing=5, md_bg_color=(0.9, 1, 0.9, 1))
        ans_card.add_widget(MDLabel(text=f"正确答案：{q.get('answer', '')}", theme_text_color="Success"))
        if q.get('analysis'):
            ans_card.add_widget(MDLabel(text=f"解析：{q['analysis']}"))
        ans_card.add_widget(MDLabel(text=f"错误次数：{q.get('wrong_count', 1)}"))
        content.add_widget(ans_card)

        if q.get('note_text'):
            note_card = MDCard(orientation="vertical", padding=15, spacing=5, md_bg_color=(1, 0.95, 0.85, 1))
            note_card.add_widget(MDLabel(text=f"我的笔记：{q['note_text']}"))
            content.add_widget(note_card)

        scroll.add_widget(content)
        layout.add_widget(scroll)

        self.add_widget(layout)

    def start_practice(self, instance):
        """开始错题练习"""
        if not self.wrong_questions:
            self.show_dialog("提示", "没有错题，无需练习！")
            return
        # 跳转到答题界面，用错题
        quiz_screen = self.manager.get_screen('quiz')
        quiz_screen.questions = self.wrong_questions[:50]  # 最多50题
        quiz_screen.current_index = 0
        quiz_screen.user_answers = {}
        quiz_screen.elapsed_time = 0
        import time
        quiz_screen.start_time = time.time()
        quiz_screen.time_limit = 0
        from kivy.clock import Clock
        quiz_screen.timer_event = Clock.schedule_interval(quiz_screen.update_timer, 1)
        quiz_screen.show_question()
        self.manager.current = 'quiz'

    def export_wrong(self, instance):
        """导出错题"""
        if not self.wrong_questions:
            self.show_dialog("提示", "没有错题可导出！")
            return
        # 简单提示：导出功能需要文件选择器
        self.show_dialog("提示", "错题导出功能：请在电脑版中操作导出，或使用题库管理的导出功能。\n\n手机端导出文件保存在应用目录下。")

    def show_dialog(self, title, text):
        dialog = MDDialog(title=title, text=text, buttons=[
            MDFlatButton(text="确定", on_release=lambda x: dialog.dismiss())
        ])
        dialog.open()
