"""
首页屏幕
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle
import db


class HomeScreen(MDScreen):
    def on_enter(self):
        """进入页面时刷新统计"""
        self.update_stats()

    def update_stats(self):
        """更新统计数据"""
        stats = db.get_stats()
        if hasattr(self, 'stats_label'):
            self.stats_label.text = (
                f"题库总数：{stats['total_questions']} 题\n"
                f"科目数：{stats['total_subjects']} 个\n"
                f"累计答题：{stats['total_exams']} 次\n"
                f"错题数：{stats['total_wrong']} 题"
            )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = MDBoxLayout(orientation='vertical', padding=20, spacing=15)

        # 标题
        title = MDLabel(
            text="答题助手",
            halign="center",
            font_style="H4",
            size_hint_y=None,
            height=60
        )
        layout.add_widget(title)

        subtitle = MDLabel(
            text="安卓版 - 随时随地刷题学习",
            halign="center",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=30
        )
        layout.add_widget(subtitle)

        # 统计卡片
        stats_card = MDCard(
            orientation="vertical",
            padding=20,
            spacing=10,
            size_hint_y=None,
            height=180,
            md_bg_color=(0.95, 0.95, 1, 1)
        )
        self.stats_label = MDLabel(
            text="加载中...",
            font_style="Body1"
        )
        stats_card.add_widget(self.stats_label)
        layout.add_widget(stats_card)

        # 功能按钮网格
        btn_grid = GridLayout(cols=2, spacing=15, padding=10)
        btn_grid.size_hint_y = None
        btn_grid.height = 300

        buttons = [
            ("开始答题", "quiz", (0.1, 0.5, 0.9, 1)),
            ("学习模式", "review", (0.2, 0.7, 0.3, 1)),
            ("错题本", "wrong", (0.9, 0.5, 0.1, 1)),
            ("题库管理", "bank", (0.6, 0.3, 0.8, 1)),
            ("导入题库", "import", (0.95, 0.6, 0.1, 1)),
            ("设置", "settings", (0.5, 0.5, 0.5, 1)),
        ]

        for text, target, color in buttons:
            btn = MDFillRoundFlatButton(
                text=text,
                md_bg_color=color,
                size_hint=(1, 1),
                font_size=18
            )
            if target == "import":
                btn.bind(on_press=lambda x: self.import_excel())
            else:
                btn.bind(on_press=lambda x, t=target: self.navigate(t))
            btn_grid.add_widget(btn)

        layout.add_widget(btn_grid)
        layout.add_widget(MDLabel())  # 占位

        self.add_widget(layout)

    def import_excel(self):
        """跳转到题库管理的导入功能"""
        self.manager.current = 'bank'
        # 触发导入
        bank_screen = self.manager.get_screen('bank')
        if hasattr(bank_screen, 'do_import'):
            bank_screen.do_import()

    def navigate(self, screen_name):
        """页面跳转"""
        self.manager.current = screen_name
