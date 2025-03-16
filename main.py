import os
import sqlite3
import tkinter as tk
import sys
from tkinter import ttk, simpledialog, messagebox

class MovieDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_tables()
    
    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''\n        CREATE TABLE IF NOT EXISTS movies (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            title TEXT NOT NULL,\n            filename TEXT NOT NULL,\n            rating1 REAL DEFAULT 0,\n            rating2 REAL DEFAULT 0,\n            watched1 INTEGER DEFAULT 0,\n            watched2 INTEGER DEFAULT 0,\n            link TEXT\n        )\n        ''')
        conn.commit()
        conn.close()
    
    def add_movie(self, title, filename, link="", rating1=0, rating2=0, watched1=0, watched2=0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO movies (title, filename, rating1, rating2, watched1, watched2, link)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, filename, rating1, rating2, watched1, watched2, link))
        conn.commit()
        conn.close()
    
    def update_movie(self, movie_id, title=None, rating1=None, rating2=None, watched1=None, watched2=None, link=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        update_fields = []
        params = []
        
        if title is not None:
            update_fields.append("title = ?")
            params.append(title)
        
        if rating1 is not None:
            update_fields.append("rating1 = ?")
            params.append(rating1)
        
        if rating2 is not None:
            update_fields.append("rating2 = ?")
            params.append(rating2)
        
        if watched1 is not None:
            update_fields.append("watched1 = ?")
            params.append(watched1)
        
        if watched2 is not None:
            update_fields.append("watched2 = ?")
            params.append(watched2)
        
        if link is not None:
            update_fields.append("link = ?")
            params.append(link)
        
        if update_fields:
            params.append(movie_id)
            query = f"UPDATE movies SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    def get_all_movies(self, sort_by=None, sort_order="ASC"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT id, title, filename, rating1, rating2, watched1, watched2, link FROM movies"
        
        if sort_by:
            query += f" ORDER BY {sort_by} {sort_order}"
        
        cursor.execute(query)
        movies = cursor.fetchall()
        conn.close()
        return movies
    
    def get_movie_by_id(self, movie_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, filename, rating1, rating2, watched1, watched2, link FROM movies WHERE id = ?", (movie_id,))
        movie = cursor.fetchone()
        conn.close()
        return movie
    
    def get_movie_by_filename(self, filename):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, filename, rating1, rating2, watched1, watched2, link FROM movies WHERE filename = ?", (filename,))
        movie = cursor.fetchone()
        conn.close()
        return movie
    
    def delete_movie(self, movie_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
        conn.commit()
        conn.close()
class MovieCatalogApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电影目录管理系统")
        self.root.geometry("800x600")
        
        # 初始化数据库
        self.db = MovieDatabase("movies.db")
        
        # 获取应用程序所在目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            app_dir = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 扫描电影文件夹
        self.movie_folder = os.path.join(app_dir, "movie")
        if not os.path.exists(self.movie_folder):
            os.makedirs(self.movie_folder)
        
        # 创建界面
        self.create_widgets()
        
        # 加载电影列表
        self.scan_movie_folder()
        self.load_movies()
    
    def create_widgets(self):
        # 创建工具栏
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # 刷新按钮
        refresh_btn = tk.Button(toolbar, text="刷新列表", command=self.refresh)
        refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 删除按钮
        delete_btn = tk.Button(toolbar, text="删除条目", command=self.delete_movie)
        delete_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 排序选项
        sort_frame = tk.Frame(toolbar)
        sort_frame.pack(side=tk.RIGHT, padx=5, pady=5)
        
        tk.Label(sort_frame, text="排序方式:").pack(side=tk.LEFT)
        self.sort_var = tk.StringVar(value="名称")
        sort_options = ttk.Combobox(sort_frame, textvariable=self.sort_var, 
                                   values=["名称", "李的评分", "彭的评分"], state="readonly")
        sort_options.pack(side=tk.LEFT, padx=5)
        sort_options.bind("<<ComboboxSelected>>", self.on_sort_change)
        self.sort_order_var = tk.StringVar(value="ASC")
        order_btn = tk.Button(sort_frame, text="↑", width=2, 
                             command=self.toggle_sort_order)
        order_btn.pack(side=tk.LEFT)
        self.order_btn = order_btn
        
        # 创建电影列表
        columns = ("id", "title", "filename", "rating1", "rating2", "watched1", "watched2")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        
        # 设置列标题
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="名称")
        self.tree.heading("filename", text="文件名")
        self.tree.heading("rating1", text="李的评分")
        self.tree.heading("rating2", text="彭的评分")
        self.tree.heading("watched1", text="李是否看过")
        self.tree.heading("watched2", text="彭是否看过")
        
        # 设置列宽，并允许拖动调整
        self.tree.column("id", width=50, stretch=False)
        self.tree.column("title", width=250, stretch=False)
        self.tree.column("filename", width=250, stretch=False)
        self.tree.column("rating1", width=100, stretch=False)
        self.tree.column("rating2", width=100, stretch=False)
        self.tree.column("watched1", width=80, stretch=False)
        self.tree.column("watched2", width=80, stretch=False)
        
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加水平滚动条
        h_scrollbar = ttk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscroll=h_scrollbar.set)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree.pack(expand=True, fill=tk.BOTH)
    
    def scan_movie_folder(self):
        # 扫描电影文件夹，将新文件和文件夹添加到数据库
        for filename in os.listdir(self.movie_folder):
            file_path = os.path.join(self.movie_folder, filename)
            if filename != ".gitkeep":
                # 检查是否为文件夹（电视剧）或文件（电影）
                is_dir = os.path.isdir(file_path)
                
                # 检查文件/文件夹是否已在数据库中
                if not self.db.get_movie_by_filename(filename):
                    # 添加到数据库，使用文件名作为默认标题
                    title = filename
                    if not is_dir:
                        title = os.path.splitext(filename)[0]
                    self.db.add_movie(title, filename)
    
    def load_movies(self):
        # 清空当前列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 从数据库加载电影
        sort_by = self.sort_var.get()
        # 添加排序字段映射
        sort_mapping = {
            "名称": "title",
            "李的评分": "rating1",
            "彭的评分": "rating2"
        }
        # 如果sort_by在映射中，则使用映射后的值
        if sort_by in sort_mapping:
            sort_by = sort_mapping[sort_by]
        
        sort_order = self.sort_order_var.get()
        movies = self.db.get_all_movies(sort_by, sort_order)
        
        # 填充列表
        for movie in movies:
            # 显示所有需要的字段（不包括链接）
            self.tree.insert("", tk.END, values=movie[:7])
    
    def refresh(self):
        self.scan_movie_folder()
        self.load_movies()
    
    def on_sort_change(self, event=None):
        self.load_movies()
    
    def toggle_sort_order(self):
        current_order = self.sort_order_var.get()
        if current_order == "ASC":
            self.sort_order_var.set("DESC")
            self.order_btn.config(text="↓")
        else:
            self.sort_order_var.set("ASC")
            self.order_btn.config(text="↑")
        self.load_movies()
    
    def add_movie(self):
        # 创建添加电影对话框
        add_dialog = tk.Toplevel(self.root)
        add_dialog.title("添加电影")
        add_dialog.geometry("400x200")
        add_dialog.transient(self.root)
        add_dialog.grab_set()
        
        # 居中显示窗口
        add_dialog.update_idletasks()
        width = add_dialog.winfo_width()
        height = add_dialog.winfo_height()
        x = (add_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (add_dialog.winfo_screenheight() // 2) - (height // 2)
        add_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # 标题输入
        tk.Label(add_dialog, text="标题:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        title_entry = tk.Entry(add_dialog, width=30)
        title_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # 文件名输入
        tk.Label(add_dialog, text="文件名:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        filename_entry = tk.Entry(add_dialog, width=30)
        filename_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # 链接输入
        tk.Label(add_dialog, text="链接:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        link_entry = tk.Entry(add_dialog, width=30)
        link_entry.grid(row=2, column=1, padx=10, pady=5)
        
        def save_movie():
            title = title_entry.get().strip()
            filename = filename_entry.get().strip()
            link = link_entry.get().strip()
            
            if not title or not filename:
                messagebox.showerror("错误", "标题和文件名不能为空")
                return
            
            # 创建空文件
            file_path = os.path.join(self.movie_folder, filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass
            
            # 添加到数据库
            self.db.add_movie(title, filename, link)
            add_dialog.destroy()
            self.refresh()
        
        # 保存按钮
        save_btn = tk.Button(add_dialog, text="保存", command=save_movie)
        save_btn.grid(row=3, column=0, columnspan=2, pady=20)
    
    def on_item_double_click(self, event):
        # 获取选中的项
        item = self.tree.selection()[0]
        movie_id = self.tree.item(item, "values")[0]
        
        # 获取电影信息
        movie = self.db.get_movie_by_id(movie_id)
        if not movie:
            return
        
        # 创建编辑对话框
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title("编辑电影")
        edit_dialog.geometry("400x350")
        edit_dialog.transient(self.root)
        edit_dialog.grab_set()
        
        # 居中显示窗口
        edit_dialog.update_idletasks()
        width = edit_dialog.winfo_width()
        height = edit_dialog.winfo_height()
        x = (edit_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (edit_dialog.winfo_screenheight() // 2) - (height // 2)
        edit_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # 标题输入
        tk.Label(edit_dialog, text="标题:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        title_entry = tk.Entry(edit_dialog, width=30)
        title_entry.insert(0, movie[1])
        title_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # 文件名（只读）
        tk.Label(edit_dialog, text="文件名:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        filename_label = tk.Label(edit_dialog, text=movie[2])
        filename_label.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 评分1输入
        tk.Label(edit_dialog, text="李的评分:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        rating1_entry = tk.Entry(edit_dialog, width=10)
        rating1_entry.insert(0, str(movie[3]))
        rating1_entry.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 评分2输入
        tk.Label(edit_dialog, text="彭的评分:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        rating2_entry = tk.Entry(edit_dialog, width=10)
        rating2_entry.insert(0, str(movie[4]))
        rating2_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 李是否看过复选框
        tk.Label(edit_dialog, text="李是否看过:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        watched1_var = tk.IntVar(value=movie[5])
        watched1_check = tk.Checkbutton(edit_dialog, variable=watched1_var)
        watched1_check.grid(row=4, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 彭是否看过复选框
        tk.Label(edit_dialog, text="彭是否看过:").grid(row=5, column=0, sticky=tk.W, padx=10, pady=5)
        watched2_var = tk.IntVar(value=movie[6])
        watched2_check = tk.Checkbutton(edit_dialog, variable=watched2_var)
        watched2_check.grid(row=5, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 链接输入 - 默认为相对路径
        tk.Label(edit_dialog, text="链接:").grid(row=6, column=0, sticky=tk.W, padx=10, pady=5)
        link_entry = tk.Entry(edit_dialog, width=30)
        # 如果链接为空，则设置为相对路径
        default_link = movie[7] if movie[7] else os.path.join("movie", movie[2])
        link_entry.insert(0, default_link)
        link_entry.grid(row=6, column=1, padx=10, pady=5)
        
        # 添加打开文件/文件夹按钮
        def open_file_or_folder():
            file_path = os.path.join(self.movie_folder, movie[2])
            if os.path.exists(file_path):
                # 使用系统默认程序打开文件或文件夹
                os.startfile(file_path)
            else:
                messagebox.showerror("错误", f"文件或文件夹不存在: {file_path}")
        
        # 创建按钮框架来容纳两个按钮
        btn_frame = tk.Frame(edit_dialog)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=15)
        
        # 在按钮框架中放置两个按钮
        open_btn = tk.Button(btn_frame, text="打开文件/文件夹", width=15, command=open_file_or_folder)
        open_btn.pack(side=tk.LEFT, padx=10)
        
        def save_edit():
            title = title_entry.get().strip()
            rating1 = float(rating1_entry.get().strip() or 0)
            rating2 = float(rating2_entry.get().strip() or 0)
            watched1 = watched1_var.get()
            watched2 = watched2_var.get()
            link = link_entry.get().strip()
            
            if not title:
                messagebox.showerror("错误", "标题不能为空")
                return
            
            # 更新数据库
            self.db.update_movie(movie_id, title, rating1, rating2, watched1, watched2, link)
            edit_dialog.destroy()
            self.refresh()
        
        # 保存按钮
        save_btn = tk.Button(btn_frame, text="保存", width=15, command=save_edit)
        save_btn.pack(side=tk.LEFT, padx=10)

    def delete_movie(self):
        # 获取选中的项
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要删除的条目")
            return
        
        # 获取电影信息
        item = selected_items[0]
        movie_id = self.tree.item(item, "values")[0]
        movie_title = self.tree.item(item, "values")[1]
        movie_filename = self.tree.item(item, "values")[2]
        
        # 确认删除
        confirm = messagebox.askyesno("确认删除", f"确定要删除《{movie_title}》吗？\n注意：这将只删除数据库中的记录，不会删除实际文件。")
        if not confirm:
            return
        
        # 从数据库中删除
        self.db.delete_movie(movie_id)
        
        # 刷新列表
        self.refresh()
        
        # 提示成功
        messagebox.showinfo("成功", f"已成功删除《{movie_title}》")
        # edit_dialog.destroy()  # 删除这一行，因为在删除操作中不存在edit_dialog变量

# 程序入口点
if __name__ == "__main__":
    root = tk.Tk()
    app = MovieCatalogApp(root)
    root.mainloop()