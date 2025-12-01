import os
import json
import shutil
from datetime import datetime
from PIL import Image, ExifTags

from kivy.lang import Builder
from kivy.core.window import Window
from kivy.properties import StringProperty, ListProperty
from kivy.factory import Factory
from kivy.utils import platform  # Для определения, где мы запущены (Android или ПК)

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.menu import MDDropdownMenu
from kivymd.toast import toast

# Размер окна для тестов на ПК (на телефоне игнорируется)
Window.size = (360, 740)


class CameraScreen(MDScreen):
    """Экран камеры"""

    def on_enter(self):
        # Включаем камеру
        if self.ids.camera_widget:
            self.ids.camera_widget.play = True

    def on_leave(self):
        # Выключаем для экономии батареи
        if self.ids.camera_widget:
            self.ids.camera_widget.play = False


class GalleryScreen(MDScreen):
    entries = ListProperty([])
    current_category_filter = StringProperty("Все")

    def on_enter(self):
        self.update_data()

    def update_data(self):
        app = MDApp.get_running_app()
        self.entries = app.load_entries()
        # Сортировка: новые сверху
        self.entries.sort(key=lambda x: datetime.strptime(x['date'], "%d.%m.%Y %H:%M"), reverse=True)
        # Фильтр
        self.filter_gallery(self.ids.search_field.text)

    def filter_gallery(self, search_text=""):
        container = self.ids.entries_box
        container.clear_widgets()
        app = MDApp.get_running_app()

        for entry in self.entries:
            cat_match = (self.current_category_filter == "Все") or \
                        (entry.get('category', '') == self.current_category_filter)

            text_match = search_text.lower() in entry.get('note', '').lower() or \
                         search_text.lower() in entry.get('category', '').lower()

            if cat_match and text_match:
                item = app.create_entry_item(entry)
                container.add_widget(item)

    def open_category_menu(self, caller):
        categories = ["Все", "Учёба", "Путешествия", "Идеи", "Личное", "Работа"]
        menu_items = [
            {
                "text": cat,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=cat: self.set_category_filter(x),
            } for cat in categories
        ]
        self.menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=4)
        self.menu.open()

    def set_category_filter(self, category):
        self.current_category_filter = category
        self.ids.filter_btn.text = f"Фильтр: {category}"
        self.menu.dismiss()
        self.filter_gallery(self.ids.search_field.text)


class ViewerScreen(MDScreen):
    photo_path = StringProperty("")


class EntryItem(MDCard):
    photo_path = StringProperty("")
    note = StringProperty("")
    date = StringProperty("")
    category = StringProperty("")
    entry_id = StringProperty("")


class PhotoDiaryApp(MDApp):
    dialog = None

    def build(self):
        self.title = "Photo Diary Pro"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Light"

        # --- ПУТИ ХРАНЕНИЯ ---
        # user_data_dir автоматически выбирает правильную папку на Android
        self.base_dir = self.user_data_dir
        self.photos_dir = os.path.join(self.base_dir, "photos")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.entries_path = os.path.join(self.data_dir, "entries.json")
        self.export_path = os.path.join(self.base_dir, "export.json")

        os.makedirs(self.photos_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        return Builder.load_file("photodiary.kv")

    def on_start(self):
        # --- ВАЖНО: ЗАПРОС РАЗРЕШЕНИЙ НА ANDROID ---
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])

    # --- КАМЕРА ---
    def capture_photo(self):
        camera = self.root.get_screen("camera").ids.camera_widget
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.png"
        path = os.path.join(self.photos_dir, filename)

        # Сохранение кадра
        try:
            camera.export_to_png(path)
            toast("Снимок сохранён")
            # Показываем превью
            self.root.get_screen("camera").last_photo_path = path
        except Exception as e:
            toast(f"Ошибка камеры: {e}")

    # --- EXIF ---
    def get_exif_date(self, photo_path):
        try:
            image = Image.open(photo_path)
            exif = image._getexif()
            if exif:
                # 36867 = DateTimeOriginal
                date_str = exif.get(36867)
                if date_str: return date_str
        except:
            pass
        return datetime.now().strftime("%Y:%m:%d %H:%M:%S")

    # --- JSON ---
    def load_entries(self):
        if not os.path.exists(self.entries_path):
            return []
        try:
            with open(self.entries_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def save_entries_file(self, entries):
        with open(self.entries_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    def save_current_entry(self):
        screen = self.root.get_screen("camera")
        path = screen.last_photo_path
        note = screen.ids.note_input.text.strip()
        category = screen.ids.category_input.text.strip() or "Общее"

        if not path or not os.path.exists(path):
            self.show_alert("Ошибка", "Сначала сделайте фото!")
            return

        exif_date = self.get_exif_date(path)

        new_entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "path": path,
            "note": note,
            "category": category,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "datetime_original": exif_date
        }

        entries = self.load_entries()
        entries.append(new_entry)
        self.save_entries_file(entries)

        toast("Запись сохранена!")
        screen.ids.note_input.text = ""
        screen.last_photo_path = ""  # сброс превью
        self.root.current = "gallery"

    # --- ЭКСПОРТ ---
    def export_data(self):
        entries = self.load_entries()
        try:
            with open(self.export_path, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
            self.show_alert("Экспорт", f"Сохранено в:\n{self.export_path}")
        except Exception as e:
            self.show_alert("Ошибка", str(e))

    # --- UI HELPERS ---
    def create_entry_item(self, entry):
        item = Factory.EntryItem()
        item.photo_path = entry.get("path", "")
        item.note = entry.get("note", "")
        item.date = entry.get("date", "")
        item.category = entry.get("category", "")
        item.entry_id = entry.get("id", "")
        return item

    def confirm_delete(self, entry_id, photo_path):
        self.dialog = MDDialog(
            title="Удалить?",
            text="Восстановить будет невозможно.",
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="УДАЛИТЬ", md_bg_color=(1, 0, 0, 1),
                               on_release=lambda x: self.delete_entry(entry_id, photo_path))
            ],
        )
        self.dialog.open()

    def delete_entry(self, entry_id, photo_path):
        if self.dialog: self.dialog.dismiss()
        if os.path.exists(photo_path):
            try:
                os.remove(photo_path)
            except:
                pass

        entries = [e for e in self.load_entries() if e.get('id') != entry_id]
        self.save_entries_file(entries)
        self.root.get_screen("gallery").update_data()
        toast("Удалено")

    def open_edit(self, entry_id, text):
        self.edit_field = MDTextField(text=text, multiline=True)
        self.dialog = MDDialog(
            title="Редактировать",
            type="custom",
            content_cls=self.edit_field,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="ОК", on_release=lambda x: self.save_edit(entry_id))
            ]
        )
        self.dialog.open()

    def save_edit(self, entry_id):
        new_text = self.edit_field.text
        entries = self.load_entries()
        for e in entries:
            if e['id'] == entry_id: e['note'] = new_text
        self.save_entries_file(entries)
        if self.dialog: self.dialog.dismiss()
        self.root.get_screen("gallery").update_data()
        toast("Обновлено")

    def open_viewer(self, path):
        self.root.get_screen("viewer").photo_path = path
        self.root.current = "viewer"

    def toggle_theme(self):
        self.theme_cls.theme_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"

    def show_alert(self, title, text):
        MDDialog(title=title, text=text, size_hint=(0.8, None)).open()


if __name__ == "__main__":
    PhotoDiaryApp().run()