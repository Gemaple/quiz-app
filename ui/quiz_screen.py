"""
答题屏幕
包含：答题设置、答题界面、结果显示
"""
import json
import time
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.clock import Clock
import db


class QuizScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = []
        self.current_index = 0
        self.user_answers = {}
        self.start_time = None
        self.timer_event = None
        self.elapsed_time = 0
        self.show_setup()

    def on_enter(self):
        self.show_setup()

    def show_setup(self):
        """显示答题设置界面"""
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', padding=20, spacing=15)

        title = MDLabel(text="开始答题", font_style="H5", size_hint_y=None, height=50)
        layout.add_widget(title)

        # 科目选择
        layout.add_widget(MDLabel(text="选择科目：", size_hint_y=None, height=30))
        self.subject_btn = MDFillRoundFlatButton(text="全部科目", size_hint_y=None, height=50)
        self.subject_btn.bind(on_press=self.show_subject_menu)
        layout.add_widget(self.subject_btn)
        self.selected_subject_id = 0

        # 题型选择
        layout.add_widget(MDLabel(text="选择题型：", size_hint_y=None, height=30))
        type_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=100)
        self.type_checks = {}
        for q_type, name in [("single", "单选题"), ("multiple", "多选题"), ("judge", "判断题"), ("case", "案例分析题")]:
            box = MDBoxLayout(orientation='horizontal', spacing=10)
            cb = CheckBox(active=True)
            self.type_checks[q_type] = cb
            box.add_widget(cb)
            box.add_widget(MDLabel(text=name))
            type_layout.add_widget(box)
        layout.add_widget(type_layout)

        # 题量
        layout.add_widget(MDLabel(text="题目数量：", size_hint_y=None, height=30))
        self.count_input = MDTextField(text="20", hint_text="输入题量（1-9999）", size_hint_y=None, height=50)
        layout.add_widget(self.count_input)

        # 随机抽题
        random_box = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        self.random_check = CheckBox(active=True)
        random_box.add_widget(self.random_check)
        random_box.add_widget(MDLabel(text="随机抽题"))
        layout.add_widget(random_box)

        # 限时
        timed_box = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        self.timed_check = CheckBox(active=False)
        timed_box.add_widget(self.timed_check)
        timed_box.add_widget(MDLabel(text="限时考试（分钟）"))
        self.time_input = MDTextField(text="30", size_hint_x=0.3, disabled=True)
        timed_box.add_widget(self.time_input)
        self.timed_check.bind(active=lambda x, v: setattr(self.time_input, 'disabled', not v))
        layout.add_widget(timed_box)

        layout.add_widget(MDLabel())

        # 开始按钮
        start_btn = MDFillRoundFlatButton(
            text="开始答题",
            md_bg_color=(0.1, 0.5, 0.9, 1),
            size_hint_y=None,
            height=60,
            font_size=20
        )
        start_btn.bind(on_press=self.start_quiz)
        layout.add_widget(start_btn)

        back_btn = MDFlatButton(text="返回首页", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def show_subject_menu(self, instance):
        """显示科目选择菜单"""
        subjects = db.get_subjects()
        menu_items = [{"text": "全部科目", "viewclass": "OneLineListItem",
                       "on_press": lambda x="全部", i=0: self.select_subject(i, "全部科目")}]
        tree = db.get_subject_tree()
        for top, children in tree:
            menu_items.append({"text": top["name"], "viewclass": "OneLineListItem",
                               "on_press": lambda x=top["name"], i=top["id"]: self.select_subject(i, x)})
            for child in children:
                menu_items.append({"text": "  └ " + child["name"], "viewclass": "OneLineListItem",
                                   "on_press": lambda x=child["name"], i=child["id"]: self.select_subject(i, x)})
        self.menu = MDDropdownMenu(caller=instance, items=menu_items, width_mult=4)
        self.menu.open()

    def select_subject(self, subject_id, name):
        self.selected_subject_id = subject_id
        self.subject_btn.text = name
        self.menu.dismiss()

    def start_quiz(self, instance):
        """开始答题"""
        try:
            count = int(self.count_input.text)
        except ValueError:
            self.show_dialog("提示", "请输入有效的题目数量！")
            return

        selected_types = [t for t, cb in self.type_checks.items() if cb.active]
        if not selected_types:
            self.show_dialog("提示", "请至少选择一种题型！")
            return

        # 获取题目
        type_order = ["single", "multiple", "judge", "case"]
        all_questions = []
        for q_type in type_order:
            if q_type in selected_types:
                qs = db.get_questions_by_type(q_type, self.selected_subject_id if self.selected_subject_id > 0 else None)
                all_questions.extend(qs)

        if not all_questions:
            self.show_dialog("提示", "该科目和题型下没有题目，请先导入题库！")
            return

        # 随机或顺序取题
        import random
        if self.random_check.active:
            random.shuffle(all_questions)
        self.questions = all_questions[:count]
        self.current_index = 0
        self.user_answers = {}
        self.elapsed_time = 0
        self.start_time = time.time()

        # 启动计时器
        if self.timed_check.active:
            try:
                self.time_limit = int(self.time_input.text) * 60
            except ValueError:
                self.time_limit = 30 * 60
        else:
            self.time_limit = 0

        self.timer_event = Clock.schedule_interval(self.update_timer, 1)
        self.show_question()

    def update_timer(self, dt):
        """更新计时器"""
        self.elapsed_time = int(time.time() - self.start_time)
        if hasattr(self, 'timer_label'):
            mins, secs = divmod(self.elapsed_time, 60)
            self.timer_label.text = f"用时：{mins:02d}:{secs:02d}"
            if self.time_limit > 0 and self.elapsed_time >= self.time_limit:
                self.timer_event.cancel()
                self.submit_quiz(None)

    def show_question(self):
        """显示当前题目"""
        self.clear_widgets()
        q = self.questions[self.current_index]

        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=10)

        # 顶部信息栏
        top_bar = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        top_bar.add_widget(MDLabel(text=f"第 {self.current_index+1}/{len(self.questions)} 题", font_style="Subtitle1"))
        self.timer_label = MDLabel(text="用时：00:00", halign="right")
        top_bar.add_widget(self.timer_label)
        layout.add_widget(top_bar)

        # 题型标签
        type_names = {"single": "单选题", "multiple": "多选题", "judge": "判断题", "case": "案例分析题"}
        type_label = MDLabel(
            text=f"【{type_names.get(q['q_type'], q['q_type'])}】",
            theme_text_color="Primary",
            size_hint_y=None,
            height=30
        )
        layout.add_widget(type_label)

        # 题干
        scroll = MDScrollView()
        content = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        q_card = MDCard(orientation="vertical", padding=15, spacing=10)
        q_card.add_widget(MDLabel(text=q['question_text'], font_style="Body1"))
        content.add_widget(q_card)

        # 选项
        self.option_checks = {}
        options = q.get('options', [])
        if options:
            for i, opt in enumerate(options):
                letter = chr(65 + i)
                opt_box = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
                if q['q_type'] == 'multiple':
                    cb = CheckBox(group=None)
                else:
                    cb = CheckBox(group=f"q{self.current_index}")
                self.option_checks[letter] = cb
                opt_box.add_widget(cb)
                opt_box.add_widget(MDLabel(text=f"{letter}. {opt}"))
                content.add_widget(opt_box)
        elif q['q_type'] == 'judge':
            for val in ["正确", "错误"]:
                opt_box = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=50)
                cb = CheckBox(group=f"q{self.current_index}")
                self.option_checks[val] = cb
                opt_box.add_widget(cb)
                opt_box.add_widget(MDLabel(text=val))
                content.add_widget(opt_box)
        else:
            # 案例分析题用文本输入
            self.case_input = MDTextField(hint_text="请输入答案...", multiline=True, size_hint_y=None, height=100)
            content.add_widget(self.case_input)

        scroll.add_widget(content)
        layout.add_widget(scroll)

        # 底部按钮
        btn_bar = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=60)
        prev_btn = MDFlatButton(text="上一题", disabled=(self.current_index == 0))
        prev_btn.bind(on_press=self.prev_question)
        btn_bar.add_widget(prev_btn)

        next_btn = MDFillRoundFlatButton(text="下一题" if self.current_index < len(self.questions)-1 else "交卷")
        next_btn.bind(on_press=self.next_or_submit)
        btn_bar.add_widget(next_btn)
        layout.add_widget(btn_bar)

        self.add_widget(layout)

    def save_current_answer(self):
        """保存当前题目的答案"""
        q = self.questions[self.current_index]
        if q['q_type'] == 'case':
            if hasattr(self, 'case_input'):
                self.user_answers[self.current_index] = self.case_input.text
        else:
            selected = []
            for letter, cb in self.option_checks.items():
                if cb.active:
                    selected.append(letter)
            if q['q_type'] == 'judge':
                self.user_answers[self.current_index] = selected[0] if selected else ""
            else:
                self.user_answers[self.current_index] = ''.join(sorted(selected))

    def prev_question(self, instance):
        self.save_current_answer()
        if self.current_index > 0:
            self.current_index -= 1
            self.show_question()

    def next_or_submit(self, instance):
        self.save_current_answer()
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self.show_question()
        else:
            self.submit_quiz(instance)

    def submit_quiz(self, instance):
        """交卷"""
        if self.timer_event:
            self.timer_event.cancel()

        self.save_current_answer()

        # 判分
        correct = 0
        wrong_list = []
        for i, q in enumerate(self.questions):
            user_ans = self.user_answers.get(i, "")
            correct_ans = q.get('answer', "")
            is_correct = (user_ans.upper() == correct_ans.upper()) if correct_ans else False
            if is_correct:
                correct += 1
            else:
                wrong_list.append((i, q, user_ans, correct_ans))
            # 更新统计
            db.update_question_stats(q['id'], is_correct)
            if not is_correct:
                db.add_wrong_question(q['id'], user_ans)

        # 保存考试记录
        mins, secs = divmod(self.elapsed_time, 60)
        db.add_exam_record(
            total=len(self.questions),
            correct=correct,
            score=int(correct / len(self.questions) * 100) if self.questions else 0,
            duration=f"{mins}分{secs}秒",
            subject_id=0
        )

        # 显示结果
        self.show_result(correct, len(self.questions), wrong_list)

    def show_result(self, correct, total, wrong_list):
        """显示考试结果"""
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', padding=20, spacing=15)

        score = int(correct / total * 100) if total else 0
        title = MDLabel(text="考试完成！", halign="center", font_style="H4", size_hint_y=None, height=60)
        layout.add_widget(title)

        result_card = MDCard(orientation="vertical", padding=20, spacing=10, size_hint_y=None, height=200)
        result_card.add_widget(MDLabel(text=f"得分：{score} 分", halign="center", font_style="H3", theme_text_color="Primary"))
        result_card.add_widget(MDLabel(text=f"答对：{correct} 题", halign="center"))
        result_card.add_widget(MDLabel(text=f"答错：{total - correct} 题", halign="center"))
        mins, secs = divmod(self.elapsed_time, 60)
        result_card.add_widget(MDLabel(text=f"用时：{mins}分{secs}秒", halign="center"))
        layout.add_widget(result_card)

        # 错题明细
        if wrong_list:
            layout.add_widget(MDLabel(text=f"错题明细（{len(wrong_list)}题）：", font_style="Subtitle1", size_hint_y=None, height=30))
            scroll = MDScrollView()
            list_content = MDBoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
            list_content.bind(minimum_height=list_content.setter('height'))
            for idx, q, user_ans, correct_ans in wrong_list[:20]:
                card = MDCard(orientation="vertical", padding=10, spacing=5, size_hint_y=None)
                card.add_widget(MDLabel(text=f"第{idx+1}题：{q['question_text'][:50]}...", font_style="Body2"))
                card.add_widget(MDLabel(text=f"你的答案：{user_ans or '未作答'}", theme_text_color="Error"))
                card.add_widget(MDLabel(text=f"正确答案：{correct_ans}", theme_text_color="Success"))
                list_content.add_widget(card)
            scroll.add_widget(list_content)
            layout.add_widget(scroll)

        layout.add_widget(MDLabel())

        # 按钮
        btn_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=60)
        retry_btn = MDFillRoundFlatButton(text="再答一次", md_bg_color=(0.1, 0.5, 0.9, 1))
        retry_btn.bind(on_press=lambda x: self.show_setup())
        btn_layout.add_widget(retry_btn)
        home_btn = MDFlatButton(text="返回首页")
        home_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        btn_layout.add_widget(home_btn)
        layout.add_widget(btn_layout)

        self.add_widget(layout)

    def show_dialog(self, title, text):
        dialog = MDDialog(title=title, text=text, buttons=[
            MDFlatButton(text="确定", on_release=lambda x: dialog.dismiss())
        ])
        dialog.open()
