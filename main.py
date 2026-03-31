import os
import json
import sqlite3
import hashlib
import base64
from PIL import Image
import customtkinter as ctk
import google.generativeai as genai
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# إعدادات المظهر العام لواجهة التطبيق
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ==========================================================
# 📊 1. الموديول المالي وقاعدة البيانات (Database & Auth)
# ==========================================================
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect("george_ai_system.db", check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # جدول المستخدمين والخطط المالية
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    plan TEXT DEFAULT 'Free'
                )
            """)
            
    def register_user(self, username, password):
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            with self.conn:
                self.conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                                  (username, pwd_hash))
            return True, "تم إنشاء الحساب بنجاح!"
        except sqlite3.IntegrityError:
            return False, "اسم المستخدم موجود بالفعل!"

    def login_user(self, username, password):
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute("SELECT plan FROM users WHERE username=? AND password_hash=?", 
                       (username, pwd_hash))
        result = cursor.fetchone()
        if result:
            return True, result[0]
        return False, None

    def upgrade_plan(self, username):
        with self.conn:
            self.conn.execute("UPDATE users SET plan='Pro' WHERE username=?", (username,))

# ==========================================================
# 🛡️ 2. موديول التشفير والذكاء الاصطناعي (AI & Crypto)
# ==========================================================
class GeorgeAICore:
    def __init__(self, api_key, password):
        genai.configure(api_key=api_key)
        self.flash_model = genai.GenerativeModel('gemini-1.5-flash')
        self.pro_model = genai.GenerativeModel('gemini-1.5-pro')
        
        # تفعيل التشفير العسكري AES-256 لحفظ الشات
        self.fernet = Fernet(self._derive_key(password))
        self.history_file = "secure_chat_history.enc"
        
        # فتح جلسة شات بالذاكرة
        self.chat_session = self.pro_model.start_chat(history=self._load_history())

    def _derive_key(self, password: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'george_fahmy_ultra_salt_2026',
            iterations=150000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'rb') as f:
                    decrypted = self.fernet.decrypt(f.read()).decode('utf-8')
                return json.loads(decrypted)
            except: return []
        return []

    def save_history(self):
        history_data = []
        for message in self.chat_session.history:
            history_data.append({
                "role": message.role,
                "parts": [p.text for p in message.parts if hasattr(p, 'text')]
            })
        encrypted = self.fernet.encrypt(json.dumps(history_data).encode('utf-8'))
        with open(self.history_file, 'wb') as f:
            f.write(encrypted)

    def ask_giant(self, prompt, user_plan):
        """الـ Smart Routing لتقليل التكلفة وتحقيق المكسب"""
        # لو الحساب مجاني -> يروح للـ Flash علطول
        if user_plan == "Free":
            response = self.flash_model.generate_content(prompt)
        else:
            # لو الحساب Pro وسؤال بسيط -> Flash برضه لتوفير فلوسنا
            if len(prompt.split()) < 5 or "هاي" in prompt or "ازيك" in prompt:
                response = self.flash_model.generate_content(prompt)
            # لو سؤال برمجي عميق -> يروح للـ Pro
            else:
                response = self.chat_session.send_message(prompt)
                self.save_history()
                
        return response.text

# ==========================================================
# 🎨 3. موديول الواجهة الرسومية (UI App)
# ==========================================================
class GeorgeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GEORGE FAHMY AI - Global SaaS Edition 🌍")
        self.geometry("700x600")
        
        # استدعاء الأنظمة
        self.db = DatabaseManager()
        self.ai = None
        
        # بيانات الجلسة الحالية
        self.current_user = None
        self.user_plan = "Free"
        
        self.show_login_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    # 🔑 شاشة الدخول
    def show_login_screen(self):
        self.clear_screen()
        
        ctk.CTkLabel(self, text="G E O R G E   F A H M Y   A I", font=("Fira Code", 26, "bold")).pack(pady=30)
        
        self.u_input = ctk.CTkEntry(self, placeholder_text="اسم المستخدم")
        self.u_input.pack(pady=10, ipadx=40)
        
        self.p_input = ctk.CTkEntry(self, placeholder_text="باسورد التشفير والدخول", show="*")
        self.p_input.pack(pady=10, ipadx=40)
        
        self.api_input = ctk.CTkEntry(self, placeholder_text="أدخل الـ Gemini API Key", show="*")
        self.api_input.pack(pady=10, ipadx=40)
        
        ctk.CTkButton(self, text="دخول", command=self.process_login).pack(pady=10)
        ctk.CTkButton(self, text="إنشاء حساب جديد", fg_color="green", command=self.process_register).pack(pady=5)

    def process_register(self):
        u, p = self.u_input.get(), self.p_input.get()
        if u and p:
            success, msg = self.db.register_user(u, p)
            print(msg)

    def process_login(self):
        u, p, api = self.u_input.get(), self.p_input.get(), self.api_input.get()
        success, plan = self.db.login_user(u, p)
        
        if success and api:
            self.current_user = u
            self.user_plan = plan
            # تفعيل محرك الـ AI بالتشفير العسكري
            self.ai = GeorgeAICore(api_key=api, password=p)
            self.show_pricing_screen()

    # 💸 شاشة الخطط والأسعار
    def show_pricing_screen(self):
        self.clear_screen()
        
        ctk.CTkLabel(self, text=f"أهلاً يا {self.current_user}! خطتك: [{self.user_plan}]", font=("Fira Code", 16)).pack(pady=10)
        ctk.CTkLabel(self, text="اختر خطتك لتفعيل القوة العالمية", font=("Fira Code", 22, "bold")).pack(pady=15)
        
        frame = ctk.CTkFrame(self)
        frame.pack(pady=10, fill="both", expand=True, padx=20)
        
        # بوكس المجاني
        free_box = ctk.CTkFrame(frame, fg_color="#333333")
        free_box.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(free_box, text="الخطة المجانية\n\n$0 / شهر\n\n- موديل سريع\n- شات محدود").pack(pady=10)
        ctk.CTkButton(free_box, text="دخول للشات", command=self.show_chat_screen).pack(pady=10)
        
        # بوكس البرو
        pro_box = ctk.CTkFrame(frame, fg_color="#1a365d")
        pro_box.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(pro_box, text="الخطة الـ Pro\n\n$5 / شهر\n\n- الموديل العملاق\n- فك التشفير\n- ذاكرة مستمرة").pack(pady=10)
        
        if self.user_plan == "Free":
            ctk.CTkButton(pro_box, text="اشترك بـ $5 (Stripe)", fg_color="gold", text_color="black", command=self.simulate_payment).pack(pady=10)
        else:
            ctk.CTkButton(pro_box, text="دخول للشات البرو", command=self.show_chat_screen).pack(pady=10)

    def simulate_payment(self):
        # محاكاة الدفع والترقية
        self.db.upgrade_plan(self.current_user)
        self.user_plan = "Pro"
        print("💳 تم سحب $5 وتفعيل الخطة البرو بنجاح!")
        self.show_chat_screen()

    # 🤖 شاشة الشات النهائية
    def show_chat_screen(self):
        self.clear_screen()
        self.geometry("800x600")
        
        # الهيدر التعريفي بالبراند
        intro_text = "🤖 أنا GEORGE FAHMY AI، أسرع وأرخص ذكاء اصطناعي في العالم!"
        ctk.CTkLabel(self, text=intro_text, font=("Fira Code", 16, "bold"), text_color="gold").pack(pady=10)
        
        self.chat_display = ctk.CTkTextbox(self, font=("Fira Code", 14))
        self.chat_display.pack(pady=10, padx=20, fill="both", expand=True)
        self.chat_display.configure(state="disabled")
        
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(pady=10, padx=20, fill="x")
        
        self.user_input = ctk.CTkEntry(input_frame, placeholder_text="اسأل العملاق أي شيء...")
        self.user_input.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        ctk.CTkButton(input_frame, text="إرسال", command=self.send_message).pack(side="right", padx=10, pady=10)

    def send_message(self):
        prompt = self.user_input.get()
        if not prompt: return
        
        # طباعة كلام المستخدم
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"👤 أنت: {prompt}\n\n")
        self.chat_display.configure(state="disabled")
        self.user_input.delete(0, "end")
        
        # جلب الرد من المحرك الذكي الموفر للتكلفة
        reply = self.ai.ask_giant(prompt, self.user_plan)
        
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"🤖 GEORGE FAHMY AI:\n{reply}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

if __name__ == "__main__":
    app = GeorgeApp()
    app.mainloop()
