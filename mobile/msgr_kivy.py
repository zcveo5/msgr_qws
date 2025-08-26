from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp

# Переменная для названия приложения
APP_TITLE = "My Messenger"

# Создаем KV строку для стилизации
Builder.load_string('''
<ChatListItem>:
    size_hint_y: None
    height: 50
    canvas.before:
        Color:
            rgba: (0.9, 0.9, 0.9, 1) if self.selected else (1, 1, 1, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: root.text
        font_size: 18
        halign: 'left'
        valign: 'middle'
        padding: 10, 0
        size_hint_x: 0.8
        text_size: self.width, None

<MessageBubble>:
    size_hint: None, None
    height: max(dp(40), lbl.texture_size[1] + dp(20))
    width: min(lbl.texture_size[0] + dp(30), root.max_width)
    padding: dp(10), dp(5)

    canvas.before:
        Color:
            rgba: root.bubble_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(15),]

    Label:
        id: lbl
        text: root.text
        font_size: dp(16)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'
        size_hint: None, None
        size: self.texture_size
        color: (0, 0, 0, 1)
''')


class ChatListItem(Button):
    """Элемент списка чатов"""
    text = StringProperty("")
    selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)


class MessageBubble(BoxLayout):
    """Пузырек сообщения"""
    text = StringProperty("")
    bubble_color = ListProperty([0.8, 0.9, 1, 1])
    max_width = dp(300)  # Максимальная ширина пузырька

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Привязываем обновление размера при изменении текста
        self.bind(text=self.update_size)

    def update_size(self, instance, value):
        # Обновляем размер при изменении текста
        self.width = min(self.ids.lbl.texture_size[0] + dp(30), self.max_width)
        self.height = max(dp(40), self.ids.lbl.texture_size[1] + dp(20))


class ChatListScreen(Screen):
    """Экран списка чатов"""
    title = StringProperty(APP_TITLE)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Основной макет
        layout = BoxLayout(orientation='vertical')

        # Верхняя панель с заголовком
        header = BoxLayout(size_hint=(1, None), height=dp(60))
        header.add_widget(Label(
            text=self.title,
            font_size=dp(24),
            bold=True,
            halign='center',
            valign='middle'
        ))
        layout.add_widget(header)

        # Прокручиваемый список чатов
        scroll_view = ScrollView()
        chat_list = GridLayout(cols=1, size_hint_y=None, spacing=dp(5))
        chat_list.bind(minimum_height=chat_list.setter('height'))

        # Добавляем тестовые чаты
        for i in range(20):
            item = ChatListItem(
                text=f"Чат {i + 1} - Участник {i + 1}",
                size_hint_y=None,
                height=dp(60))
            item.bind(on_press=self.open_chat)
            chat_list.add_widget(item)

        scroll_view.add_widget(chat_list)
        layout.add_widget(scroll_view)

        self.add_widget(layout)

    def open_chat(self, instance):
        """Переход в экран чата с анимацией влево"""
        app = App.get_running_app()
        app.chat_title = instance.text

        # Устанавливаем направление анимации ВЛЕВО
        app.root.transition.direction = 'left'
        app.root.current = 'chat'


class ChatScreen(Screen):
    """Экран чата"""
    chat_title = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        # Верхняя панель с кнопкой назад и названием чата
        header = BoxLayout(size_hint=(1, None), height=dp(60))
        btn_back = Button(
            text="< Назад",
            size_hint_x=None,
            width=dp(100),
            font_size=dp(18),
        background_color = (0.8, 0.8, 1, 1),
        background_normal = '')

        btn_back.bind(on_press=self.go_back)
        header.add_widget(btn_back)

        self.title_label = Label(
        text = self.chat_title,
        font_size = dp(24),
        bold = True,
        halign = 'center',
        valign = 'middle')

        header.add_widget(self.title_label)
        self.layout.add_widget(header)

        # Область сообщений с прокруткой
        self.messages_scroll = ScrollView()
        self.messages_layout = GridLayout(
            cols=1,
            size_hint_y=None,
            spacing=dp(10),
        padding = dp(10))
        self.messages_layout.bind(minimum_height=self.messages_layout.setter('height'))
        self.messages_scroll.add_widget(self.messages_layout)
        self.layout.add_widget(self.messages_scroll)

        # Нижняя панель ввода
        footer = BoxLayout(
            size_hint=(1, None),
            height=dp(60),
        padding = dp(5),
        spacing = dp(5))

        self.message_input = TextInput(
            hint_text="Введите сообщение...",
            multiline=True,
            size_hint_x=0.8)
        footer.add_widget(self.message_input)

        btn_send = Button(
            text="Отправить",
            size_hint_x=0.2,
            background_color=(0, 0.7, 0, 1),
            background_normal='')
        btn_send.bind(on_press=self.send_message)
        footer.add_widget(btn_send)

        self.layout.add_widget(footer)
        self.add_widget(self.layout)

        # Привязка к изменению размера окна
        Window.bind(on_resize=self.on_window_resize)


    def on_window_resize(self, instance, width, height):
        """Обновление максимальной ширины пузырьков при изменении размера окна"""
        max_width = width * 0.8  # 80% ширины окна
        for child in self.messages_layout.children:
            if hasattr(child, 'max_width'):
                child.max_width = max_width
                child.update_size(child, child.text)


    def on_chat_title(self, instance, value):
        if hasattr(self, 'title_label'):
            self.title_label.text = value


    def go_back(self, instance):
        """Возврат к списку чатов с анимацией вправо"""
        app = App.get_running_app()

        # Устанавливаем направление анимации ВПРАВО
        app.root.transition.direction = 'right'
        app.root.current = 'chat_list'


    def send_message(self, instance):
        text = self.message_input.text.strip()
        if text:
            bubble = MessageBubble(text=text)

            # Устанавливаем максимальную ширину
            bubble.max_width = Window.width * 0.8

            # Выравнивание в зависимости от отправителя
            if len(self.messages_layout.children) % 3 == 0:
                bubble.bubble_color = (0.9, 0.9, 0.9, 1)  # Сообщение собеседника

                # Создаем контейнер для выравнивания влево
                container = BoxLayout(orientation='horizontal')
                container.add_widget(bubble)
                container.add_widget(BoxLayout(size_hint_x=None, width=Window.width * 0.2))
                self.messages_layout.add_widget(container)
            else:
                bubble.bubble_color = (0.8, 0.9, 1, 1)  # Ваше сообщение

                # Создаем контейнер для выравнивания вправо
                container = BoxLayout(orientation='horizontal')
                container.add_widget(BoxLayout(size_hint_x=None, width=Window.width * 0.2))
                container.add_widget(bubble)
                self.messages_layout.add_widget(container)

            self.message_input.text = ''

            # Прокрутка вниз
            self.messages_scroll.scroll_y = 0


class Settings(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)


class MessengerApp(App):
    def build(self):
        # Создаем менеджер экранов с SlideTransition
        sm = ScreenManager(transition=SlideTransition(duration=0.3))

        # Создаем экраны
        chat_list_screen = ChatListScreen(name='chat_list')
        chat_screen = ChatScreen(name='chat')

        # Добавляем экраны в менеджер
        sm.add_widget(chat_list_screen)
        sm.add_widget(chat_screen)

        # Храним ссылки для обновления
        self.chat_list_screen = chat_list_screen
        self.chat_screen = chat_screen
        self.chat_title = APP_TITLE + " - Чат"

        return sm

    def on_chat_title(self, instance, value):
        self.chat_screen.chat_title = value


if __name__ == '__main__':
    Window.size = (400, 700)
    Window.minimum_width, Window.minimum_height = 300, 500

    MessengerApp().run()