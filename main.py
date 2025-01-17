import os
import random
import json
import tkinter as tk
from tkinter import messagebox

class NonDenseIndexedFile:
    def __init__(self, file_path):
        self.file_path = file_path
        self.index_area = []
        self.data_blocks = []
        self.overflow_area = []
        self.block_size = 10
        self.load_data()

    def load_data(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    self.index_area = data.get('index_area', [])
                    self.data_blocks = data.get('data_blocks', [])
                    self.overflow_area = data.get('overflow_area', [])
            except json.JSONDecodeError:
                # Якщо файл пошкоджений, ініціалізуємо порожні дані
                self.index_area = []
                self.data_blocks = []
                self.overflow_area = []
                self.save_data()  # Зберігаємо порожні дані

    def save_data(self):
        with open(self.file_path, 'w') as f:
            json.dump({
                'index_area': self.index_area,
                'data_blocks': self.data_blocks,
                'overflow_area': self.overflow_area
            }, f)

    def search(self, key):
        comparisons = 0
        # Пошук в індексній області
        for index_entry in self.index_area:
            comparisons += 1
            if index_entry['start'] <= key <= index_entry['end']:
                block_id = index_entry['block_id']
                break
        else:
            return None, comparisons  # Ключ не знайдено

        # Пошук у блоці
        for record in self.data_blocks[block_id]:
            comparisons += 1
            if record['key'] == key:
                return record, comparisons

        # Пошук у області переповнення (метод Шарра)
        for record in self.overflow_area:
            comparisons += 1
            if record['key'] == key:
                return record, comparisons

        return None, comparisons

    def add_record(self, key, data):
        # Перевірка унікальності ключа
        existing_record, _ = self.search(key)
        if existing_record:
            existing_record['data'] = data  # Оновлення даних
        else:
            # Додати запис у відповідний блок або область переповнення
            block_id = self._find_or_create_block(key)
            if len(self.data_blocks[block_id]) < self.block_size:
                self.data_blocks[block_id].append({'key': key, 'data': data})
            else:
                self.overflow_area.append({'key': key, 'data': data})
                self._rebuild_index()

        self.save_data()

    def delete_record(self, key):
        # Видалення з блоку
        for block in self.data_blocks:
            for record in block:
                if record['key'] == key:
                    block.remove(record)
                    self.save_data()
                    return

        # Видалення з області переповнення
        for record in self.overflow_area:
            if record['key'] == key:
                self.overflow_area.remove(record)
                self.save_data()
                return

        raise ValueError("Record not found")

    def edit_record(self, key, new_data):
        record, _ = self.search(key)
        if not record:
            raise ValueError("Record not found")

        record['data'] = new_data
        self.save_data()

    def _find_or_create_block(self, key):
        # Знайти відповідний блок або створити новий
        for idx, index_entry in enumerate(self.index_area):
            if index_entry['start'] <= key <= index_entry['end']:
                return index_entry['block_id']

        # Створення нового блоку
        new_block_id = len(self.index_area)
        self.index_area.append({'start': key, 'end': key, 'block_id': new_block_id})
        self.data_blocks.append([])
        return new_block_id

    def _rebuild_index(self):
        # Перебудова індексної області, метод Шарра
        if len(self.overflow_area) > self.block_size:
            for record in self.overflow_area:
                block_id = self._find_or_create_block(record['key'])
                if len(self.data_blocks[block_id]) < self.block_size:
                    self.data_blocks[block_id].append(record)
                    self.overflow_area.remove(record)

    def fill_random_data(self, num_records):
        for _ in range(num_records):
            key = random.randint(1, num_records * 10)
            data = f"RandomData{key}"
            self.add_record(key, data)

    def calculate_average_comparisons(self, search_attempts):
        total_comparisons = 0
        for _ in range(search_attempts):
            random_key = random.randint(1, 100000)
            _, comparisons = self.search(random_key)
            total_comparisons += comparisons
        return total_comparisons / search_attempts


class DatabaseApp:
    def __init__(self, root, db):
        self.root = root
        self.db = db
        self.root.title("Non-Dense Indexed Database")


        self.key_label = tk.Label(root, text="Key:")
        self.key_label.grid(row=0, column=0)
        self.key_entry = tk.Entry(root)
        self.key_entry.grid(row=0, column=1)

        self.data_label = tk.Label(root, text="Data:")
        self.data_label.grid(row=1, column=0)
        self.data_entry = tk.Entry(root)
        self.data_entry.grid(row=1, column=1)


        self.add_button = tk.Button(root, text="Add", command=self.add_record)
        self.add_button.grid(row=2, column=0)

        self.search_button = tk.Button(root, text="Search", command=self.search_record)
        self.search_button.grid(row=2, column=1)

        self.edit_button = tk.Button(root, text="Edit", command=self.edit_record)
        self.edit_button.grid(row=3, column=0)

        self.delete_button = tk.Button(root, text="Delete", command=self.delete_record)
        self.delete_button.grid(row=3, column=1)

        self.fill_button = tk.Button(root, text="Fill Random Data", command=self.fill_random_data)
        self.fill_button.grid(row=4, column=0)

        self.stats_button = tk.Button(root, text="Show Stats", command=self.show_stats)
        self.stats_button.grid(row=4, column=1)

    def add_record(self):
        try:
            key = int(self.key_entry.get())
            data = self.data_entry.get()
            self.db.add_record(key, data)
            messagebox.showinfo("Success", "Record added successfully.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def search_record(self):
        try:
            key = int(self.key_entry.get())
            record, comparisons = self.db.search(key)
            if record:
                self.data_entry.delete(0, tk.END)
                self.data_entry.insert(0, record['data'])
                messagebox.showinfo("Success", f"Record found: {record}. Comparisons: {comparisons}")
            else:
                messagebox.showinfo("Not Found", f"Record not found. Comparisons: {comparisons}")
        except ValueError:
            messagebox.showerror("Error", "Invalid key.")

    def edit_record(self):
        try:
            key = int(self.key_entry.get())
            new_data = self.data_entry.get()
            self.db.edit_record(key, new_data)
            messagebox.showinfo("Success", "Record updated successfully.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def delete_record(self):
        try:
            key = int(self.key_entry.get())
            self.db.delete_record(key)
            messagebox.showinfo("Success", "Record deleted successfully.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def fill_random_data(self):
        try:
            self.db.fill_random_data(10000)
            messagebox.showinfo("Success", "Database filled with random data.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_stats(self):
        try:
            average_comparisons = self.db.calculate_average_comparisons(15)
            messagebox.showinfo("Statistics", f"Average comparisons: {average_comparisons}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    db = NonDenseIndexedFile("database.json")

    root = tk.Tk()
    app = DatabaseApp(root, db)
    root.mainloop()
