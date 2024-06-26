import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from configparser import ConfigParser

'''BACKUP GUI BY TKINTER

class ConfigEditor:
    def __init__(self, master, config_file):
        self.master = master
        self.master.title("Config Editor")

        self.config_file = config_file
        self.config = ConfigParser()
        self.config.read(self.config_file)

        self.create_widgets()

    def create_widgets(self):
        self.tree = ttk.Treeview(self.master, columns=('Value'))
        self.tree.heading('#0', text='Option')
        self.tree.heading('Value', text='Value')

        for section in self.config.sections():
            values = dict(self.config.items(section))
            for option, value in values.items():
                self.tree.insert('', 'end', text=option, values=(value,))

        self.tree.pack(expand=True, fill='both')
        self.tree.bind("<Double-1>", self.edit_value)

    def edit_value(self, event):
        item = self.tree.selection()[0]
        option = self.tree.item(item, 'text')
        value = self.tree.item(item, 'values')[0]

        new_value = self.prompt_for_input(f"Enter value for '{option}'", value)
        if new_value is not None:
            # Найдем секцию, к которой относится параметр
            section = self.find_section_by_option(option)
            self.config.set(section, option, new_value)

            # Обновим значение в Treeview
            self.tree.item(item, values=(new_value,))

            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)

    def prompt_for_input(self, prompt, default_value):
        user_input = simpledialog.askstring("Input", prompt, initialvalue=default_value)
        return user_input

    def find_section_by_option(self, option):
        for section in self.config.sections():
            if option in self.config[section]:
                return section

'''



class ConfigEditor:
    def __init__(self, master, config_file, auth_callback):
        self.master = master
        self.master.title("Config Editor")

        self.config_file = config_file
        self.config = ConfigParser()
        self.config.read(self.config_file)
        self.auth_callback = auth_callback

        self.create_widgets()

    def create_widgets(self):
        self.tree = ttk.Treeview(self.master, columns=('Value'))
        self.tree.heading('#0', text='Option')
        self.tree.heading('Value', text='Value')

        for section in self.config.sections():
            values = dict(self.config.items(section))
            for option, value in values.items():
                self.tree.insert('', 'end', text=option, values=(value,))

        self.tree.pack(expand=True, fill='both')

        self.btn_apply = ttk.Button(self.master, text="Применить изменения", command=self.apply_changes)
        self.btn_apply.pack(pady=10)

    def apply_changes(self):
        for item in self.tree.get_children():
            option = self.tree.item(item, 'text')
            value = self.tree.item(item, 'values')[0]

            new_value = self.prompt_for_input(f"Enter value for '{option}'", value)
            if new_value is not None:
                section = self.find_section_by_option(option)
                self.config.set(section, option, new_value)

        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

        try:
            self.auth_callback()
            messagebox.showinfo("Успех", "Изменения успешно применены.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка повторной авторизации: {e}")

    def prompt_for_input(self, prompt, default_value):
        user_input = simpledialog.askstring("Input", prompt, initialvalue=default_value)
        return user_input

    def find_section_by_option(self, option):
        for section in self.config.sections():
            if option in self.config[section]:
                return section


# Пример использования:
class YourClassWithAuthentication:
    async def _authenticate(self):
        pass
        #Ваш текущий код аутентификации

    def open_config_editor(self):
        root = tk.Tk()
        config_editor = ConfigEditor(root, "путь_к_вашему_файлу_конфигурации", self._authenticate)
        root.mainloop()

# Запуск GUI
if __name__ == "__main__":
    app = YourClassWithAuthentication()
    app.open_config_editor()