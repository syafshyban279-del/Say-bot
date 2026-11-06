import os
import telebot
import requests
import random
import time
import re
import base64
from urllib.parse import unquote, urlparse
from string import ascii_letters, digits
from concurrent.futures import ThreadPoolExecutor

API_TOKEN = '9182112317:AAHS0bKkn1K-A_txVNbXx0NWlG2woH_7LL0'
bot = telebot.TeleBot(API_TOKEN)

admins = ['8193131587']  # ضع معرف الأدمن هنا

banned_users = []  # إضافة المتغير المفقود
user_notifications = False
bot_stopped = False

executor = ThreadPoolExecutor(max_workers=10000)

class Zefoy:
    def __init__(self, chat_id, url):
        self.chat_id = chat_id
        self.base_url = 'https://zefoy.com/'
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'}
        self.session = requests.Session()
        self.captcha_1 = None
        self.captcha_ = {}
        self.services = {}
        self.services_ids = {}
        self.services_status = {}
        self.url = url
        self.selected_services = []
        self.current_directory = os.path.dirname(os.path.abspath(__file__))
        self.captcha_path = os.path.join(self.current_directory, 'captcha.png')

    def send_message(self, message):
        bot.send_message(self.chat_id, message)

    def get_captcha(self):
        try:
            if os.path.exists(os.path.join(self.current_directory, 'session')):
                self.session.cookies.set("PHPSESSID", open(os.path.join(self.current_directory, 'session'), encoding='utf-8').read(), domain='zefoy.com')
            request = self.session.get(self.base_url, headers=self.headers)
            if 'Enter Video URL' in request.text:
                self.video_key = request.text.split('" placeholder="Enter Video URL"')[0].split('name="')[-1]
                return True

            for x in re.findall(r'<input type="hidden" name="(.*)" value="(.*)">', request.text):
                self.captcha_[x[0]] = x[1]

            self.captcha_1 = request.text.split('type="text" name="')[1].split('" oninput="this.value=this.value.toLowerCase()"')[0]
            captcha_url = request.text.split('<img src="')[1].split('" onerror="imgOnError()" class="')[0]
            request = self.session.get(f"{self.base_url}{captcha_url}", headers=self.headers)
            
            with open(self.captcha_path, 'wb') as f:
                f.write(request.content)

            if os.path.exists(self.captcha_path):
                self.send_message('🔍 - جاري حل الكابتشا ....')
                return False
            else:
                self.send_message("⚠️ - لم يتم العثور على ملف الكابتشا")
                return False
        except Exception as e:
            self.send_message(f"⚠️ - حدث خطأ أثناء الحصول على الكابتشا: {e}")
            return False

    def send_captcha(self, new_session=False):
        if new_session:
            self.session = requests.Session()
            try:
                os.remove(os.path.join(self.current_directory, 'session'))
            except FileNotFoundError:
                pass
            time.sleep(2)
        if self.get_captcha():
            self.send_message('🔍 - تم حل الكابتشا بنجاح')
            return (True, 'The session already exists')
        
        captcha_solve = self.solve_captcha(self.captcha_path)
        if captcha_solve[0]:
            self.captcha_[self.captcha_1] = captcha_solve[1]
            request = self.session.post(self.base_url, headers=self.headers, data=self.captcha_)

            if 'Enter Video URL' in request.text:
                self.send_message('✅ تم إنشاء الجلسة')
                with open(os.path.join(self.current_directory, 'session'), 'w', encoding='utf-8') as f:
                    f.write(self.session.cookies.get('PHPSESSID'))
                self.send_message(f"🎉 تم حل الكابتشا بنجاح: {captcha_solve[1]}")
                self.video_key = request.text.split('" placeholder="Enter Video URL"')[0].split('name="')[-1]
                return (True, captcha_solve[1])
            else:
                self.send_message(f"⚠️ - فشل في حل الكابتشا.")
                return (False, captcha_solve[1])
        else:
            self.send_message(f"⚠️ - فشل في حل الكابتشا: {captcha_solve[1]}")
            return (False, captcha_solve[1])

    def solve_captcha(self, path_to_file):
        if os.path.exists(path_to_file):
            task = path_to_file
        else:
            return (False, "ملف الكابتشا غير موجود")

        try:
            with open(task, 'rb') as f:
                request = self.session.post('https://api.ocr.space/parse/image?K87899142388957', headers={'apikey': 'K87899142388957'}, files={'task': f}).json()
            solved_text = request['ParsedResults'][0]['ParsedText'].strip()
            if solved_text:
                return (True, solved_text)
            else:
                return (False, "لم يتم استخراج نص من الكابتشا")
        except (IndexError, KeyError, FileNotFoundError) as e:
            return (False, f"خطأ في قراءة الكابتشا: {e}")

    def get_status_services(self):
        request = self.session.get(self.base_url, headers=self.headers).text
        for x in re.findall(r'<h5 class="card-title">.+</h5>\n.+\n.+', request):
            service_name = x.split('<h5 class="card-title">')[1].split('<')[0].strip()
            service_status = x.split('d-sm-inline-block">')[1].split('</small>')[0].strip()
            self.services[service_name] = service_status
        for x in re.findall(r'<h5 class="card-title mb-3">.+</h5>\n<form action=".+">', request):
            service_name = x.split('title mb-3">')[1].split('<')[0].strip()
            service_id = x.split('<form action="')[1].split('">')[0].strip()
            self.services_ids[service_name] = service_id
        for x in re.findall(r'<h5 class="card-title">.+</h5>\n.+<button .+', request):
            service_name = x.split('<h5 class="card-title">')[1].split('<')[0].strip()
            self.services_status[service_name] = False if 'disabled class' in x else True
        return (self.services, self.services_status)

    def get_table(self):
        self.services.clear()
        self.get_status_services()
        message = "🛠️ الخدمات المتاحة:\n\n"
        available_services = {
            "Followers": "متابعين",
            "Likes": "لايكات",
            "Views": "مشاهدات",
            "Shares": "شير",
            "Favorites": "مفضلة",
            "Live Views": "مشاهدات لايف"
        }
        for service, name in available_services.items():
            if service in self.services and self.services_status[service]:
                message += f"✅ {name}\n"
        message += "\nاكتب اسماء الخدمات التي تريد استخدامها:"
        self.send_message(message)

    def find_video(self):
        if not self.selected_services:
            self.send_message("❌ لم تختر الخدمة بعد")
            return

        parsed_url = urlparse(self.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            self.send_message("❌ الرابط غير صحيح. الرجاء إدخال رابط صحيح.")
            return
        
        while True:
            for service in self.selected_services:
                self.service = service
                if self.service not in self.services_ids:
                    self.get_status_services()
                    time.sleep(1)
                request = self.session.post(f'{self.base_url}{self.services_ids[self.service]}', headers={'content-type':'multipart/form-data; boundary=----WebKitFormBoundary0nU8PjANC8BhQgjZ', 'user-agent': self.headers['user-agent'], 'origin':'https://zefoy.com'}, data=f'------WebKitFormBoundary0nU8PjANC8BhQgjZ\r\nContent-Disposition: form-data; name="{self.video_key}"\r\n\r\n{self.url}\r\n------WebKitFormBoundary0nU8PjANC8BhQgjZ--\r\n')
                try:
                    self.video_info = base64.b64decode(unquote(request.text.encode()[::-1])).decode()
                except:
                    time.sleep(3)
                    continue
                if 'Session expired. Please re-login' in self.video_info:
                    self.send_message('⚠️ انتهت الجلسة، يتم إعادة تسجيل الدخول...')
                    self.send_captcha()
                    return
                elif 'service is currently not working' in self.video_info:
                    self.send_message(f"⚠️ الخدمة {service} غير متاحة حالياً")
                    continue
                elif """onsubmit="showHideElements""" in self.video_info:
                    self.video_info = [self.video_info.split('" name="')[1].split('"')[0], self.video_info.split('value="')[1].split('"')[0]]
                    self.use_service()
                    continue
                elif 'Checking Timer...' in self.video_info:
                    try:
                        t = int(re.findall(r'ltm=(\d*);', self.video_info)[0])
                    except:
                        continue
                    self.send_message(f"⏳ تبقى {t} ثانية.")
                    time.sleep(t)
                    continue
                elif 'Too many requests. Please slow' in self.video_info:
                    time.sleep(3)
                    continue
                elif 'Not found video' in self.video_info:
                    self.send_message("❌ لم يتم العثور على الفيديو. الرجاء إدخال رابط صحيح.")
                    return
                else:
                    self.send_message(f"✅ تمت معالجة الفيديو بنجاح للخدمة: {self.service}")

    def use_service(self):
        self.token = "".join(random.choices(ascii_letters + digits, k=16))
        request = self.session.post(f'{self.base_url}{self.services_ids[self.service]}', headers={'content-type': f'multipart/form-data; boundary=----WebKitFormBoundary{self.token}', 'user-agent': self.headers['user-agent'], 'origin': 'https://zefoy.com'}, data=f'------WebKitFormBoundary{self.token}\r\nContent-Disposition: form-data; name="{self.video_info[0]}"\r\n\r\n{self.video_info[1]}\r\n------WebKitFormBoundary{self.token}--\r\n')
        try:
            res = base64.b64decode(unquote(request.text.encode()[::-1])).decode()
        except:
            time.sleep(3)
            return ""
        if 'Session expired. Please re-login' in res:
            self.send_message('⚠️ انتهت الجلسة، يتم إعادة تسجيل الدخول...')
            self.send_captcha()
            return ""
        elif 'Too many requests. Please slow' in res:
            time.sleep(3)
        elif 'service is currently not working' in res:
            return '⚠️ الخدمة غير متاحة حالياً، حاول لاحقاً'
        else:
            self.send_message(f'✅ تم إرسال {self.service} بنجاح للرابط: {self.url}')
            self.find_video()

    def select_service(self):
        self.get_table()
        bot.register_next_step_handler_by_chat_id(self.chat_id, self.process_service_selection)

    def process_service_selection(self, message):
        services_requested = message.text.split("\n")
        services_map = {
            "متابعين": "Followers",
            "لايكات": "Likes",
            "مشاهدات": "Views",
            "شير": "Shares",
            "مفضلة": "Favorites",
            "مشاهدات لايف": "Live Views"
        }
        for service in services_requested:
            if service in services_map:
                self.selected_services.append(services_map[service])
                self.send_message(f"⏳ جاري تنفيذ: {service}...")
            else:
                self.send_message(f"❌ الخدمة {service} غير متاحة. الرجاء اختيار خدمة متاحة.")
        
        self.find_video()

    def ask_for_video_url(self):
        self.send_message("🔗 ضع رابط المقطع:")
        bot.register_next_step_handler_by_chat_id(self.chat_id, self.process_video_url)

    def process_video_url(self, message):
        self.url = message.text.strip()
        executor.submit(self.send_captcha)  # استخدام executor لتنفيذ العمليات في خلفية

@bot.message_handler(commands=['adm'])
def admin_panel(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "🚫 لوحة الإدارة متاحة في المحادثات الخاصة فقط.")
        return

    chat_id = message.chat.id
    if str(chat_id) not in admins:
        bot.send_message(chat_id, "🚫 ليس لديك صلاحيات الوصول إلى هذه اللوحة.")
        return
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        telebot.types.InlineKeyboardButton("🔒 حظر", callback_data="ban_user"),
        telebot.types.InlineKeyboardButton("🔓 فك حظر", callback_data="unban_user"),
        telebot.types.InlineKeyboardButton("🛑 إيقاف", callback_data="stop_bot"),
        telebot.types.InlineKeyboardButton("✅ تشغيل", callback_data="start_bot"),
        telebot.types.InlineKeyboardButton("🔔 إشعارات المستخدمين", callback_data="user_notifications"),
        telebot.types.InlineKeyboardButton("⭐ تعين مستخدم كأدمن", callback_data="assign_admin"),
        telebot.types.InlineKeyboardButton("❌ تنزيل مستخدم من أدمن", callback_data="remove_admin"),
        telebot.types.InlineKeyboardButton("👥 قائمة الإدمن", callback_data="admin_list"),
        telebot.types.InlineKeyboardButton("🚫 قائمة المحظورين", callback_data="banned_list"),
        telebot.types.InlineKeyboardButton("📢 إذاعة", callback_data="broadcast_message")
    )
    bot.send_message(chat_id, "🎛️ لوحة الإدارة", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "ban_user":
        msg = bot.send_message(chat_id, "✋ أدخل معرف المستخدم المراد حظره:")
        bot.register_next_step_handler(msg, ban_user)
    
    elif call.data == "unban_user":
        msg = bot.send_message(chat_id, "🔓 أدخل معرف المستخدم المراد فك حظره:")
        bot.register_next_step_handler(msg, unban_user)
    
    elif call.data == "stop_bot":
        stop_bot(chat_id)
    
    elif call.data == "start_bot":
        start_bot(chat_id)
    
    elif call.data == "user_notifications":
        toggle_user_notifications(chat_id)
    
    elif call.data == "assign_admin":
        msg = bot.send_message(chat_id, "⭐ أدخل معرف المستخدم لتعينه كأدمن:")
        bot.register_next_step_handler(msg, assign_admin)
    
    elif call.data == "remove_admin":
        msg = bot.send_message(chat_id, "❌ أدخل معرف المستخدم لتنزيله من أدمن:")
        bot.register_next_step_handler(msg, remove_admin)
    
    elif call.data == "admin_list":
        show_admin_list(chat_id)
    
    elif call.data == "banned_list":
        show_banned_list(chat_id)
    
    elif call.data == "broadcast_message":
        msg = bot.send_message(chat_id, "📢 أدخل الرسالة للإذاعة لجميع المستخدمين:")
        bot.register_next_step_handler(msg, broadcast_message)

def ban_user(message):
    user_id = message.text
    if user_id not in banned_users:
        banned_users.append(user_id)
        bot.send_message(message.chat.id, f"🚫 تم حظر المستخدم: {user_id}")
    else:
        bot.send_message(message.chat.id, "🚫 المستخدم محظور بالفعل.")

def unban_user(message):
    user_id = message.text
    if user_id in banned_users:
        banned_users.remove(user_id)
        bot.send_message(message.chat.id, f"✅ تم فك حظر المستخدم: {user_id}")
    else:
        bot.send_message(message.chat.id, "🚫 المستخدم غير محظور.")

def stop_bot(chat_id):
    global bot_stopped
    bot_stopped = True
    bot.send_message(chat_id, "🛑 تم إيقاف البوت. لن يستطيع المستخدمون استخدامه حتى يتم تشغيله مجدداً.")

def start_bot(chat_id):
    global bot_stopped
    bot_stopped = False
    bot.send_message(chat_id, "✅ تم تشغيل البوت مجدداً. يمكن للمستخدمين الآن استخدامه.")

def toggle_user_notifications(chat_id):
    global user_notifications
    user_notifications = not user_notifications
    status = "تشغيل" if user_notifications else "إيقاف"
    bot.send_message(chat_id, f"🔔 تم {status} إشعارات المستخدمين.")

def assign_admin(message):
    user_id = message.text
    if user_id not in admins:
        admins.append(user_id)
        bot.send_message(message.chat.id, f"⭐ تم تعين {user_id} كأدمن.")
    else:
        bot.send_message(message.chat.id, "⭐ المستخدم بالفعل أدمن.")

def remove_admin(message):
    user_id = message.text
    if user_id in admins:
        admins.remove(user_id)
        bot.send_message(message.chat.id, f"❌ تم تنزيل {user_id} من الأدمن.")
    else:
        bot.send_message(message.chat.id, "❌ المستخدم ليس أدمن.")

def show_admin_list(chat_id):
    if admins:
        bot.send_message(chat_id, "👥 قائمة الأدمن:\n" + "\n".join(admins))
    else:
        bot.send_message(chat_id, "❌ لا يوجد أدمن حالياً.")

def show_banned_list(chat_id):
    if banned_users:
        bot.send_message(chat_id, "🚫 قائمة المحظورين:\n" + "\n".join(banned_users))
    else:
        bot.send_message(chat_id, "✅ لا يوجد مستخدمين محظورين حالياً.")

def broadcast_message(message):
    broadcast_text = message.text
    sent_count = 0
    for user_id in bot.get_chat_administrators(message.chat.id):
        try:
            bot.send_message(user_id.user.id, f"📢 إذاعة: {broadcast_text}")
            sent_count += 1
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ لم يتم إرسال الرسالة إلى {user_id.user.id}: {e}")
    bot.send_message(message.chat.id, f"✅ تم إرسال الرسالة إلى {sent_count} مستخدمين.")

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if str(chat_id) in banned_users:
        bot.send_message(chat_id, "🚫 أنت محظور من استخدام هذا البوت.")
        return
    if bot_stopped:
        bot.send_message(chat_id, "🛑 البوت متوقف حالياً.")
    else:
        bot.send_message(chat_id, "👋 مرحباً بك! ضع رابط تيك توك للتحقق من الخدمات المتاحة.")

@bot.message_handler(func=lambda message: message.chat.type == 'supergroup' and "tiktok.com" in message.text)
def handle_tiktok_link(message):
    chat_id = message.chat.id
    if str(chat_id) in banned_users:
        bot.send_message(chat_id, "🚫 أنت محظور من استخدام هذا البوت.")
        return
    
    video_url = message.text.strip()
    bot.send_message(chat_id, f"🔗 تم استلام الرابط: {video_url}. جاري المعالجة...")  # الرد على الفور لتأكيد الاستلام
    executor.submit(process_tiktok_link, chat_id, video_url)  # استخدام executor لتنفيذ العمليات بشكل متزامن

def process_tiktok_link(chat_id, video_url):
    try:
        Z = Zefoy(chat_id, video_url)
        Z.url = video_url
        Z.send_captcha()
        Z.select_service()
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ حدث خطأ أثناء معالجة الرابط: {e}")

bot.polling()
