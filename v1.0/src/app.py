import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import configparser
import re
import time
from openai import OpenAI

# Глобальные константы
_CONFIG_INI = "settings.ini"

class TranslationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ren'Py AI Tool - Denis Edition")
        self.root.resizable(False, False)
        
        # Переменные интерфейса
        self.api_key_var = tk.StringVar()
        self.api_url_var = tk.StringVar(value="https://openrouter.ai/api/v1")
        self.translate_to_var = tk.StringVar(value="Russian")
        self.input_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.engine_var = tk.StringVar(value="google/gemini-2.0-flash-lite:free")
        self.batch_size_var = tk.StringVar(value="10")
        self.temperature_var = tk.StringVar(value="0.3")
        self.prompt_var = tk.StringVar(value="You are a professional editor. Correct grammar and spelling in the following Russian text, preserving Ren'Py tags.")

        self.is_running = False
        self.load_config()
        self.create_widgets()

    def create_widgets(self):
        padding = {'padx': 5, 'pady': 5}

        # Сетка интерфейса
        tk.Label(self.root, text="API Key:").grid(row=0, column=0, sticky='e', **padding)
        tk.Entry(self.root, textvariable=self.api_key_var, width=50, show="*").grid(row=0, column=1, columnspan=2, sticky='w', **padding)

        tk.Label(self.root, text="API URL:").grid(row=1, column=0, sticky='e', **padding)
        tk.Entry(self.root, textvariable=self.api_url_var, width=50).grid(row=1, column=1, columnspan=2, sticky='w', **padding)

        tk.Label(self.root, text="Target Lang:").grid(row=2, column=0, sticky='e', **padding)
        tk.Entry(self.root, textvariable=self.translate_to_var, width=50).grid(row=2, column=1, columnspan=2, sticky='w', **padding)

        tk.Label(self.root, text="Input Path:").grid(row=3, column=0, sticky='e', **padding)
        tk.Entry(self.root, textvariable=self.input_path_var, width=40).grid(row=3, column=1, sticky='w', **padding)
        tk.Button(self.root, text="Browse", command=self.browse_input).grid(row=3, column=2, sticky='w', **padding)

        tk.Label(self.root, text="Output Path:").grid(row=4, column=0, sticky='e', **padding)
        tk.Entry(self.root, textvariable=self.output_path_var, width=40).grid(row=4, column=1, sticky='w', **padding)
        tk.Button(self.root, text="Browse", command=self.browse_output).grid(row=4, column=2, sticky='w', **padding)

        tk.Label(self.root, text="Model Engine:").grid(row=5, column=0, sticky='e', **padding)
        tk.Entry(self.root, textvariable=self.engine_var, width=50).grid(row=5, column=1, columnspan=2, sticky='w', **padding)

        # Ряд: Batch Size и Temperature
        tk.Label(self.root, text="Batch / Temp:").grid(row=6, column=0, sticky='e', **padding)
        params_frame = tk.Frame(self.root)
        params_frame.grid(row=6, column=1, columnspan=2, sticky='w')
        
        tk.Entry(params_frame, textvariable=self.batch_size_var, width=8).pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(params_frame, text="T:").pack(side=tk.LEFT, padx=(5, 2))
        tk.Entry(params_frame, textvariable=self.temperature_var, width=8).pack(side=tk.LEFT)

        tk.Label(self.root, text="System Prompt:").grid(row=7, column=0, sticky='e', **padding)
        tk.Entry(self.root, textvariable=self.prompt_var, width=50).grid(row=7, column=1, columnspan=2, sticky='w', **padding)

        self.start_button = tk.Button(self.root, text="Start Process", command=self.start_translation, bg="#2ecc71", fg="white", font=('Arial', 10, 'bold'))
        self.start_button.grid(row=8, column=0, columnspan=3, pady=10, sticky='nsew', padx=50)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_translation, state=tk.DISABLED, bg="#e74c3c", fg="white")
        self.stop_button.grid(row=9, column=0, columnspan=3, pady=5, sticky='nsew', padx=50)

        self.progress_bar = ttk.Progressbar(self.root, orient='horizontal', length=400, mode='determinate')
        self.progress_bar.grid(row=10, column=0, columnspan=3, pady=10)

        self.log_text = tk.Text(self.root, height=12, width=65, font=('Consolas', 9))
        self.log_text.grid(row=11, column=0, columnspan=3, **padding)

    def browse_input(self):
        path = filedialog.askdirectory()
        if path: self.input_path_var.set(path)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path: self.output_path_var.set(path)

    def log(self, message):
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)

    def save_config(self):
        config = configparser.ConfigParser()
        config['Settings'] = {
            "api_key": self.api_key_var.get(),
            "api_url": self.api_url_var.get(),
            "engine": self.engine_var.get(),
            "batch_size": self.batch_size_var.get(),
            "temperature": self.temperature_var.get(),
            "prompt": self.prompt_var.get(),
            "translate_to": self.translate_to_var.get(),
            "input_path": self.input_path_var.get(),
            "output_path": self.output_path_var.get()
        }
        with open(_CONFIG_INI, "w", encoding='utf-8') as f:
            config.write(f)

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(_CONFIG_INI):
            config.read(_CONFIG_INI, encoding='utf-8')
            if 'Settings' in config:
                s = config['Settings']
                self.api_key_var.set(s.get("api_key", ""))
                self.api_url_var.set(s.get("api_url", "https://openrouter.ai/api/v1"))
                self.engine_var.set(s.get("engine", "google/gemini-2.0-flash-lite:free"))
                self.batch_size_var.set(s.get("batch_size", "10"))
                self.temperature_var.set(s.get("temperature", "0.3"))
                self.prompt_var.set(s.get("prompt", self.prompt_var.get()))
                self.translate_to_var.set(s.get("translate_to", "Russian"))
                self.input_path_var.set(s.get("input_path", ""))
                self.output_path_var.set(s.get("output_path", ""))

    def start_translation(self):
        if not self.api_key_var.get():
            messagebox.showwarning("Warning", "Enter API Key!")
            return
        self.save_config()
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        threading.Thread(target=self.process_files, daemon=True).start()

    def stop_translation(self):
        self.is_running = False
        self.log("Stopping process...")

    def process_files(self):
        input_dir = self.input_path_var.get()
        output_dir = self.output_path_var.get()
        
        if not input_dir or not output_dir:
            self.log("Error: Paths not selected!")
            self.reset_ui()
            return
            
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        
        files = [f for f in os.listdir(input_dir) if f.endswith('.rpy')]
        if not files:
            self.log("No .rpy files found!")
            self.reset_ui()
            return

        self.progress_bar['maximum'] = len(files)
        client = OpenAI(api_key=self.api_key_var.get(), base_url=self.api_url_var.get())

        for idx, filename in enumerate(files):
            if not self.is_running: break
            self.log(f"File {idx+1}/{len(files)}: {filename}")
            self.translate_file(os.path.join(input_dir, filename), os.path.join(output_dir, filename), client)
            self.progress_bar['value'] = idx + 1
        
        self.log("All tasks completed!")
        self.reset_ui()

    def translate_file(self, in_path, out_path, client):
        with open(in_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        translatable_items = []
        pattern = re.compile(r'^(?P<prefix>\s*(?:old\s+|new\s+|".*?"\s+|[\w\d_]+\s+)?")(?P<text>.+?)(?P<suffix>")(?P<extra>.*)$')

        for i, line in enumerate(lines):
            match = pattern.match(line)
            if match and not line.strip().startswith(('#', 'default', 'define')):
                translatable_items.append({'index': i, 'text': match.group('text'), 'match': match})

        batch_size = int(self.batch_size_var.get())
        for i in range(0, len(translatable_items), batch_size):
            if not self.is_running: break
            batch = translatable_items[i:i + batch_size]
            texts_to_process = [item['text'] for item in batch]
            
            try:
                processed_texts = self.call_ai(texts_to_process, client)
                if processed_texts and len(processed_texts) == len(batch):
                    for j, new_text in enumerate(processed_texts):
                        item = batch[j]
                        m = item['match']
                        lines[item['index']] = f"{m.group('prefix')}{new_text}{m.group('suffix')}{m.group('extra')}\n"
                else:
                    self.log(f"Error: Batch mismatch in {os.path.basename(in_path)}")
            except Exception as e:
                self.log(f"AI Error: {str(e)}")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def call_ai(self, texts, client):
        target_lang = self.translate_to_var.get()
        user_content = f"Target Language: {target_lang}\n\nTexts to process:\n" + "\n".join([f"{i}:{t}" for i, t in enumerate(texts)])
        
        try:
            temp = float(self.temperature_var.get())
        except:
            temp = 0.3
            
        response = client.chat.completions.create(
            model=self.engine_var.get(),
            messages=[
                {"role": "system", "content": self.prompt_var.get()},
                {"role": "user", "content": user_content}
            ],
            temperature=temp
        )
        
        result_text = response.choices[0].message.content
        results = []
        for line in result_text.strip().split('\n'):
            res = re.sub(r'^\d+:', '', line).strip()
            if res: results.append(res)
        return results[:len(texts)]

    def reset_ui(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = TranslationGUI(root)
    root.mainloop()