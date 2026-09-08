"""
题库管理屏幕
Excel导入、题库浏览、科目管理、导出题库
"""
import os
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivy.uix.spinner import Spinner
import db
from file_import import import_file, generate_excel_template


class BankScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = []

    def on_enter(self):
        self.load_questions()
        self.show_main()

    def load_questions(self):
        self.questions = db.get_all_questions()

    def show_main(self):
        """显示题库管理主界面"""
        self.clear_widgets()
        layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10)

        title = MDLabel(text="题库管理", font_style="H5", size_hint_y=None, height=50)
        layout.add_widget(title)

        # 统计
        stats = MDLabel(
            text=f"题库总数：{len(self.questions)} 题 | 科目：{len(db.get_subjects())} 个",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=30
        )
        layout.add_widget(stats)

        # 操作按钮
        btn_grid = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=250)

        import_btn = MDFillRoundFlatButton(
            text="📥 导入 Excel 题库",
            md_bg_color=(0.1, 0.5, 0.9, 1),
            size_hint_y=None,
            height=55,
            font_size=18
        )
        import_btn.bind(on_press=self.do_import)
        btn_grid.add_widget(import_btn)

        template_btn = MDFillRoundFlatButton(
            text="📄 下载 Excel 导入模板",
            md_bg_color=(0.95, 0.6, 0.1, 1),
            size_hint_y=None,
            height=55,
            font_size=18
        )
        template_btn.bind(on_press=self.download_template)
        btn_grid.add_widget(template_btn)

        export_btn = MDFillRoundFlatButton(
            text="📤 导出题库",
            md_bg_color=(0.2, 0.7, 0.3, 1),
            size_hint_y=None,
            height=55,
            font_size=18
        )
        export_btn.bind(on_press=self.export_bank)
        btn_grid.add_widget(export_btn)

        subject_btn = MDFillRoundFlatButton(
            text="📁 科目管理",
            md_bg_color=(0.6, 0.3, 0.8, 1),
            size_hint_y=None,
            height=55,
            font_size=18
        )
        subject_btn.bind(on_press=self.manage_subjects)
        btn_grid.add_widget(subject_btn)

        layout.add_widget(btn_grid)

        # 题目列表
        layout.add_widget(MDLabel(text="题目列表：", font_style="Subtitle1", size_hint_y=None, height=30))
        scroll = MDScrollView()
        list_widget = MDList()
        type_names = {"single": "单选", "multiple": "多选", "judge": "判断", "case": "案例"}

        for q in self.questions[:200]:  # 最多显示200条
            item = TwoLineListItem(
                text=f"[{type_names.get(q['q_type'], q['q_type'])}] {q['question_text'][:40]}...",
                secondary=f"答案：{q.get('answer', '')} | 作答{q.get('try_count', 0)}次 错{q.get('wrong_count', 0)}次",
                on_press=lambda x, item_q=q: self.show_question_detail(item_q)
            )
            list_widget.add_widget(item)

        if len(self.questions) > 200:
            list_widget.add_widget(TwoLineListItem(
                text=f"... 还有 {len(self.questions) - 200} 题未显示",
                secondary="请使用筛选功能查看"
            ))

        scroll.add_widget(list_widget)
        layout.add_widget(scroll)

        bottom = MDBoxLayout(size_hint_y=None, height=50)
        back_btn = MDFlatButton(text="返回首页")
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        bottom.add_widget(back_btn)
        layout.add_widget(bottom)

        self.add_widget(layout)

    def do_import(self, instance=None):
        """导入Excel题库"""
        # 安卓上需要用文件选择器
        # 简化处理：提示用户将Excel文件放到指定目录，然后输入文件名
        content = MDBoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(MDLabel(
            text="请将Excel文件放到手机存储根目录，然后输入文件名（如：questions.xlsx）",
            font_style="Body2"
        ))
        self.import_filename = MDTextField(hint_text="Excel文件名（如：questions.xlsx）", size_hint_y=None, height=50)
        content.add_widget(self.import_filename)

        # 科目选择
        subjects = db.get_subjects()
        subject_names = [s["name"] for s in subjects]
        self.import_subject = Spinner(text="选择科目", values=subject_names if subject_names else ["默认"])
        content.add_widget(self.import_subject)

        dialog = MDDialog(
            title="导入 Excel 题库",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda x: dialog.dismiss()),
                MDFillRoundFlatButton(text="导入", on_release=lambda x: self.perform_import(dialog))
            ]
        )
        dialog.open()

    def perform_import(self, dialog):
        """执行导入"""
        filename = self.import_filename.text.strip()
        if not filename:
            self.show_dialog("提示", "请输入文件名！")
            return

        # 尝试多个路径
        possible_paths = [
            f"/sdcard/{filename}",
            f"/storage/emulated/0/{filename}",
            f"/sdcard/Download/{filename}",
            f"/storage/emulated/0/Download/{filename}",
            filename,
        ]

        filepath = None
        for p in possible_paths:
            if os.path.exists(p):
                filepath = p
                break

        if not filepath:
            self.show_dialog("错误", f"找不到文件：{filename}\n\n请确保文件在手机存储根目录或Download目录下！")
            return

        try:
            questions, msg = import_file(filepath)

            # 设置科目
            subject_name = self.import_subject.text
            subject_id = 0
            for s in db.get_subjects():
                if s["name"] == subject_name:
                    subject_id = s["id"]
                    break

            for q in questions:
                q['subject_id'] = subject_id

            count = db.add_questions_batch(questions)
            dialog.dismiss()
            self.load_questions()
            self.show_main()
            self.show_dialog("成功", f"成功导入 {count} 道题！")
        except Exception as e:
            self.show_dialog("导入失败", f"错误：{str(e)}")

    def download_template(self, instance):
        """下载Excel模板"""
        try:
            # 保存到手机存储
            save_paths = ["/sdcard/题目导入模板.xlsx", "/storage/emulated/0/题目导入模板.xlsx"]
            saved = False
            for path in save_paths:
                try:
                    success, msg = generate_excel_template(path)
                    if success:
                        self.show_dialog("成功", f"模板已保存到：\n{path}\n\n请按模板格式填写后导入。")
                        saved = True
                        break
                except Exception:
                    continue
            if not saved:
                self.show_dialog("提示", "请在电脑版中下载模板，或手动创建Excel文件。\n\n模板格式：题干、题型、选项A-D、答案、解析、科目")
        except Exception as e:
            self.show_dialog("错误", str(e))

    def export_bank(self, instance):
        """导出题库"""
        self.show_dialog("提示", "导出功能：请选择导出格式\n\n1. Excel - 与导入模板格式相同\n2. PDF - 可打印试卷格式\n3. Word - 可编辑文档\n\n手机端导出文件保存在 /sdcard/ 目录下。")

    def manage_subjects(self, instance):
        """科目管理"""
        tree = db.get_subject_tree()
        text = "科目列表（二级目录）：\n\n"
        for top, children in tree:
            text += f"📁 {top['name']}\n"
            for child in children:
                text += f"  └ {child['name']}\n"
        text += "\n\n科目管理请在电脑版中操作（添加/编辑/删除科目）。"
        self.show_dialog("科目管理", text)

    def show_question_detail(self, q):
        """显示题目详情"""
        type_names = {"single": "单选题", "multiple": "多选题", "judge": "判断题", "case": "案例分析题"}
        text = f"【{type_names.get(q['q_type'], q['q_type'])}】\n\n"
        text += f"题干：{q['question_text']}\n\n"
        options = q.get('options', [])
        if options:
            for i, opt in enumerate(options):
                text += f"{chr(65+i)}. {opt}\n"
            text += "\n"
        text += f"正确答案：{q.get('answer', '')}\n"
        if q.get('analysis'):
            text += f"解析：{q['analysis']}\n"
        text += f"\n作答次数：{q.get('try_count', 0)} | 错误次数：{q.get('wrong_count', 0)}"
        if q.get('note_text'):
            text += f"\n\n我的笔记：{q['note_text']}"
        self.show_dialog("题目详情", text)

    def show_dialog(self, title, text):
        dialog = MDDialog(title=title, text=text, buttons=[
            MDFlatButton(text="确定", on_release=lambda x: dialog.dismiss())
        ])
        dialog.open()
