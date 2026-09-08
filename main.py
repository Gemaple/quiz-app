"""
答题助手 - 安卓版
基于 Kivy + KivyMD 开发
功能：做题、学习、错题本、题库管理、Excel导入导出、AI解析
"""
import os
import sys
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.card import MDCard
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.gridlayout import MDGridLayout

# 初始化数据库
import db
db.init_db()

# 导入各个屏幕
from ui.home_screen import HomeScreen
from ui.quiz_screen import QuizScreen
from ui.review_screen import ReviewScreen
from ui.wrong_screen import WrongScreen
from ui.bank_screen import BankScreen
from ui.settings_screen import SettingsScreen


KV = '''
<ContentNavigationDrawer>:
    orientation: "vertical"
    padding: "8dp"
    spacing: "8dp"

    AnchorLayout:
        anchor_x: "left"
        size_hint_y: None
        height: avatar.height

        Image:
            id: avatar
            size_hint: None, None
            size: "56dp", "56dp"
            source: "data/logo/kivy-icon-256.png"

    MDLabel:
        text: "答题助手"
        font_style: "Button"
        size_hint_y: None
        height: self.texture_size[1]

    MDLabel:
        text: "安卓版"
        font_style: "Caption"
        size_hint_y: None
        height: self.texture_size[1]

    ScrollView:
        MDList:
            OneLineListItem:
                text: "首页"
                on_press: app.root.current = 'home'
            OneLineListItem:
                text: "开始答题"
                on_press: app.root.current = 'quiz_setup'
            OneLineListItem:
                text: "学习模式"
                on_press: app.root.current = 'review'
            OneLineListItem:
                text: "错题本"
                on_press: app.root.current = 'wrong'
            OneLineListItem:
                text: "题库管理"
                on_press: app.root.current = 'bank'
            OneLineListItem:
                text: "设置"
                on_press: app.root.current = 'settings'
'''


class QuizApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        Builder.load_string(KV)

        self.sm = ScreenManager()
        self.sm.add_widget(HomeScreen(name='home'))
        self.sm.add_widget(QuizScreen(name='quiz'))
        self.sm.add_widget(ReviewScreen(name='review'))
        self.sm.add_widget(WrongScreen(name='wrong'))
        self.sm.add_widget(BankScreen(name='bank'))
        self.sm.add_widget(SettingsScreen(name='settings'))

        return self.sm

    def navigate_to(self, screen_name):
        """页面跳转"""
        self.sm.current = screen_name

    def show_dialog(self, title, text):
        """显示提示对话框"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="确定",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()


if __name__ == '__main__':
    QuizApp().run()
