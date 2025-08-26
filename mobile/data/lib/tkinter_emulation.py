from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label as KivyLabel
from kivy.uix.button import Button as KivyButton
from kivy.uix.textinput import TextInput as KivyEntry
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.properties import StringProperty


class TkinterEmulator:
    class Tk:
        def __init__(self):
            self.children = []
            self._title = "Tkinter Emulator"
            self._geometry = "400x300"
            # Добавляем контейнер для виджетов
            self.container = BoxLayout(orientation='vertical')

        def mainloop(self):
            TkApp(self).run()

        def title(self, title):
            self._title = title

        def geometry(self, size):
            self._geometry = size

    class Frame(BoxLayout):
        def __init__(self, master=None, **kwargs):
            super().__init__(**kwargs)
            self.master = master
            self.orientation = 'vertical'
            self.padding = 10
            self.spacing = 5
            self.children = []

            if master:
                master.children.append(self)

        def pack(self, **kwargs):
            if isinstance(self.master, TkinterEmulator.Tk):
                self.master.container.add_widget(self)
            elif self.master:
                self.master.add_widget(self)
            return self

    class Label(KivyLabel):
        def __init__(self, master=None, text="", **kwargs):
            super().__init__(**kwargs)
            self.master = master
            self.text = text
            self.font_size = 14
            self.halign = 'left'
            self.valign = 'center'
            self.size_hint_y = None
            self.height = 30

            if master:
                master.children.append(self)

        def pack(self, **kwargs):
            if self.master:
                self.master.add_widget(self)
            return self

    class Button(KivyButton):
        def __init__(self, master=None, text="", command=None, **kwargs):
            super().__init__(**kwargs)
            self.master = master
            self.text = text
            self.command = command
            self.font_size = 14
            self.size_hint_y = None
            self.height = 40

            self.bind(on_press=self.on_button_press)

            if master:
                master.children.append(self)

        def pack(self, **kwargs):
            if self.master:
                self.master.add_widget(self)
            return self

        def on_button_press(self, instance):
            if self.command:
                self.command()

    class Entry(KivyEntry):
        def __init__(self, master=None, **kwargs):
            super().__init__(**kwargs)
            self.master = master
            self.font_size = 14
            self.size_hint_y = None
            self.height = 40
            self.multiline = False

            if master:
                master.children.append(self)

        def pack(self, **kwargs):
            if self.master:
                self.master.add_widget(self)
            return self

        def get(self):
            return self.text

        def delete(self, start, end):
            self.text = self.text[:start] + self.text[end:]

        def insert(self, index, string):
            self.text = self.text[:index] + string + self.text[index:]

    class Listbox(ScrollView):
        def __init__(self, master=None, **kwargs):
            super().__init__(**kwargs)
            self.master = master
            self.size_hint = (1, None)
            self.height = 100

            # Внутренний контейнер для элементов
            self.list_container = BoxLayout(
                orientation='vertical',
                size_hint_y=None
            )
            self.list_container.bind(minimum_height=self.list_container.setter('height'))
            self.add_widget(self.list_container)

            self.items = []
            self.selected_index = -1

            if master:
                master.children.append(self)

        def pack(self, **kwargs):
            if self.master:
                self.master.add_widget(self)
            return self

        def insert(self, index, item):
            lbl = KivyLabel(
                text=str(item),
                size_hint_y=None,
                height=30,
                halign='left',
                valign='center',
                color=(0, 0, 0, 1)  # Черный цвет текста
            )
            lbl.index = index
            lbl.bind(on_touch_down=self.select_item)

            if index >= len(self.items):
                self.items.append(lbl)
                self.list_container.add_widget(lbl)
            else:
                self.items.insert(index, lbl)
                self.list_container.add_widget(lbl)

        def delete(self, index):
            if 0 <= index < len(self.items):
                self.list_container.remove_widget(self.items[index])
                del self.items[index]

        def get(self, index):
            if 0 <= index < len(self.items):
                return self.items[index].text
            return None

        def curselection(self):
            return [self.selected_index] if self.selected_index >= 0 else []

        def select_item(self, instance, touch):
            if instance.collide_point(*touch.pos):
                # Сброс предыдущего выделения
                for item in self.items:
                    item.background_color = (1, 1, 1, 1)

                # Установка нового выделения
                instance.background_color = (0.7, 0.7, 1, 1)
                self.selected_index = instance.index
                return True
            return False

    class StringVar(EventDispatcher):
        def __init__(self, value=''):
            super().__init__()
            self._value = value
            self._trace_callbacks = []

        def get(self):
            return self._value

        def set(self, value):
            if self._value != value:
                self._value = value
                # Вызываем все зарегистрированные callback-функции
                for callback in self._trace_callbacks:
                    callback()

        def trace(self, mode, callback):
            """Регистрирует callback-функцию, которая будет вызываться при изменении значения"""
            self._trace_callbacks.append(callback)
            return len(self._trace_callbacks) - 1  # Возвращаем ID для удаления

        def trace_remove(self, trace_id):
            """Удаляет callback по его ID"""
            if 0 <= trace_id < len(self._trace_callbacks):
                self._trace_callbacks.pop(trace_id)

        # Для совместимости с Kivy
        value = property(get, set)

# Приложение Kivy для запуска эмулятора
class TkApp(App):
    def __init__(self, tk_root, **kwargs):
        super().__init__(**kwargs)
        self.tk_root = tk_root

    def build(self):
        self.title = self.tk_root._title
        width, height = map(int, self.tk_root._geometry.split('x'))
        Window.size = (width, height)

        # Возвращаем корневой контейнер Tk
        return self.tk_root.container


_tk = TkinterEmulator()

Tk = _tk.Tk
Button = _tk.Button
Label = _tk.Label
Listbox = _tk.Listbox
Entry = _tk.Entry
Frame = _tk.Frame
StringVar = _tk.StringVar
