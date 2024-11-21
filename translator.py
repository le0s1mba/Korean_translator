import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import keyboard
import pyperclip
import urllib.request
import urllib.parse
import json
import threading
import os
from PIL import Image, ImageDraw, ImageTk
import pystray
import sv_ttk

class TranslatorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Modern Translator")
        self.root.withdraw()
        self.popup = None
        self.is_translating = False
        self.ctrl_pressed = False
        
        sv_ttk.set_theme("dark")
        
        keyboard.on_press_key('ctrl', self.ctrl_down)
        keyboard.on_release_key('ctrl', self.ctrl_up)
        keyboard.on_press_key('`', self.handle_hotkey, suppress=True)
        
        self.style = ttk.Style()
        self.create_custom_styles()
        
    def create_custom_styles(self):
        self.style.configure("Custom.TFrame", background="#2b2b2b")
        self.style.configure("Custom.TLabel", background="#2b2b2b", foreground="#ffffff", font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", background="#2b2b2b", foreground="#ffffff", font=("Segoe UI", 12, "bold"))
    
    def ctrl_down(self, _): self.ctrl_pressed = True
    def ctrl_up(self, _): self.ctrl_pressed = False
    
    def handle_hotkey(self, _):
        if self.ctrl_pressed:
            if self.popup and tk.Toplevel.winfo_exists(self.popup):
                self.popup.destroy()
            self.root.after(100, self.show_popup)
            
    def translate_text(self, text: str) -> str:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ko&tl=en&dt=t&q={urllib.parse.quote(text)}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})) as response:
                data = json.loads(response.read().decode('utf-8'))
                return ''.join(sentence[0] for sentence in data[0] if sentence[0])
        except Exception as e:
            messagebox.showerror("Error", f"Translation error: {str(e)}")
            return ""

    def show_popup(self):
        try:
            self.popup = tk.Toplevel(self.root)
            self.popup.title("Translator")
            self.popup.configure(bg="#2b2b2b")
            self.popup.attributes('-alpha', 0.95, '-topmost', True)
            
            x = (self.popup.winfo_screenwidth() - 500) // 2
            y = (self.popup.winfo_screenheight() - 400) // 2
            self.popup.geometry(f'500x400+{x}+{y}')
            
            main_frame = ttk.Frame(self.popup, style="Custom.TFrame", padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(main_frame, text="Korean to English Translator", style="Title.TLabel").pack(pady=(0, 20))
            
            input_frame = ttk.Frame(main_frame, style="Custom.TFrame")
            input_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(input_frame, text="Enter Korean text (Press Enter to translate, Shift+Enter for new line):", 
                     style="Custom.TLabel").pack(anchor="w", pady=(0, 5))
            
            self.text_input = scrolledtext.ScrolledText(
                input_frame, height=12, font=("Segoe UI", 11),
                bg="#363636", fg="#ffffff", insertbackground="#ffffff"
            )
            self.text_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            
            status_frame = ttk.Frame(main_frame, style="Custom.TFrame")
            status_frame.pack(fill=tk.X, pady=(10, 0))
            
            self.char_count = ttk.Label(status_frame, text="Characters: 0", style="Custom.TLabel")
            self.char_count.pack(side=tk.LEFT)
            
            self.text_input.bind('<KeyRelease>', self.update_char_count)
            self.text_input.bind('<Return>', self.handle_return)
            self.text_input.bind('<Shift-Return>', self.handle_shift_return)
            self.popup.bind('<Escape>', lambda e: self.popup.destroy())
            
            self.popup.protocol("WM_DELETE_WINDOW", self.popup.destroy)
            self.popup.after(10, self._ensure_focus)
            
        except Exception as e:
            print(f"Error creating popup: {str(e)}")
    
    def _ensure_focus(self):
        try:
            if self.popup and tk.Toplevel.winfo_exists(self.popup):
                self.popup.focus_force()
                self.text_input.focus_set()
        except Exception as e:
            print(f"Error setting focus: {str(e)}")
    
    def handle_return(self, event):
        if not event.state & 0x1:
            self.handle_translation()
            return 'break'
    
    def handle_shift_return(self, event):
        current_pos = self.text_input.index(tk.INSERT)
        self.text_input.insert(current_pos, '\n')
        return 'break'
    
    def update_char_count(self, _):
        count = len(self.text_input.get('1.0', tk.END).strip())
        self.char_count.config(text=f"Characters: {count}")
    
    def translation_thread(self, text: str):
        try:
            translated_text = self.translate_text(text)
            if translated_text:
                pyperclip.copy(translated_text)
                if self.popup and tk.Toplevel.winfo_exists(self.popup):
                    self.popup.destroy()
                keyboard.press_and_release('ctrl+v')
        finally:
            self.is_translating = False
            
    def handle_translation(self):
        if self.is_translating:
            return
            
        text = self.text_input.get('1.0', tk.END).strip()
        if text:
            self.is_translating = True
            threading.Thread(target=self.translation_thread, args=(text,), daemon=True).start()

def create_tray_icon(app):
    icon = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    draw.rectangle([10, 10, 54, 54], fill="#007AFF")
    draw.text((25, 15), "T", fill="white", font=None, size=24)
    
    return pystray.Icon(
        "translator",
        icon,
        "Modern Translator",
        menu=pystray.Menu(
            pystray.MenuItem("Exit", lambda: os._exit(0))
        )
    )

def main():
    app = TranslatorApp()
    tray_icon = create_tray_icon(app)
    threading.Thread(target=tray_icon.run, daemon=True).start()
    app.root.mainloop()

if __name__ == "__main__":
    main()