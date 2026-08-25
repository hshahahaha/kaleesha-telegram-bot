# نشر بوت كليشة على Railway

ارفع **محتويات هذا المجلد** إلى مشروع Railway جديد. يكتشف Railway ملف `requirements.txt` ويثبت منه مكتبة البوت، ثم يشغّل `python kaleesha_bot_railway.py` وفق `railway.json`. يعيد Railway تشغيل العملية تلقائيًا عند التعطل حتى 10 مرات.

## المتغيرات السرية في Railway

من Railway افتح مشروعك، ثم `Variables`، وأضف القيم التالية. لا تضع التوكن في الملف ولا ترفعه إلى GitHub:

| الاسم | القيمة |
|---|---|
| `BOT_TOKEN` | التوكن الجديد من BotFather |
| `ADMIN_ID` | `1427023555` |
| `MINI_APP_URL` | `https://hshahahaha.github.io/ayman-ph-website/#/collection/best-selling` |

بعد الحفظ، نفّذ إعادة نشر للخدمة. في `Deploy Logs` يجب أن يظهر تثبيت `python-telegram-bot` ثم بدء عملية `python kaleesha_bot_railway.py` دون أخطاء. عند `/start` يرسل البوت صورة البداية `kaleesha_start_image.jpg` مع العبارة «اضغط على الزر الموجود على اليسار كما في الصورة.» فقط، ولا يعرض أي زر إضافي أسفل خانة الكتابة.

## إذا ظهرت نسخة قديمة في Railway

اربط خدمة Railway بهذا المستودع مباشرة: `https://github.com/hshahahaha/kaleesha-telegram-bot`. بعد الربط، افتح الخدمة ثم اختر **Deployments** واضغط **Deploy Latest Commit** أو **Redeploy**. لا تنشئ خدمة جديدة من ملف ZIP قديم ولا تعتمد على نشر سابق.

بعد أن تصبح حالة النشر **Success**، افتح `Deploy Logs` وتأكد من ظهور الأمر `python kaleesha_bot_railway.py`. بعدها أرسل `/start` إلى البوت. النسخة الحديثة ترسل الصورة وتعليق «اضغط على الزر الموجود على اليسار كما في الصورة.» فقط، ولا تعرض زرًا سفليًا.

> ملاحظة: يحتفظ البوت بقاعدة المستخدمين في ملف SQLite. للاعتمادية الطويلة وتفادي فقدان القائمة عند إعادة بناء الخدمة، اربط Volume دائم في Railway ثم اضبط `DB_PATH` على مسار داخل الـ Volume، مثل `/data/kaleesha_bot.db`.
