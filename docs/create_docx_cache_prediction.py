"""Create .docx for reviewer response about cache prediction/placement - pure Python."""
import zipfile, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "reviewer_response_cache_prediction.docx")

CT = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'

RELS = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'

WRELS = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def esc(t):
    return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def mkp(text, bold=False, sz=24, rtl=True):
    b = '<w:b/><w:bCs/>' if bold else ''
    r = '<w:rtl/>' if rtl else ''
    ppr = '<w:pPr><w:bidi/><w:jc w:val="right"/></w:pPr>' if rtl else '<w:pPr></w:pPr>'
    return f'<w:p>{ppr}<w:r><w:rPr>{b}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>{r}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>'

def blank():
    return '<w:p><w:pPr><w:bidi/></w:pPr></w:p>'

lines = []
a = lines.append

# === TITLE ===
a(mkp("پاسخ به ریویور: محل cache چگونه انتخاب می‌شود و منظور از cache prediction چیست؟", True, 34))
a(blank())

# === QUESTION ===
a(mkp("سوال ریویور", True, 30))
a(mkp("محل cache چگونه و بر چه اساسی انتخاب می‌شود؟ شما درباره cache prediction صحبت کردید اما نگفتید منظورتان چیست. چه چیزی را می‌خواهید predict کنید؟ pattern آن را یا جای cache کردنش را؟"))
a(blank())

# === SHORT ANSWER ===
a(mkp("پاسخ کوتاه", True, 30))
a(mkp("در سیستم FL-RL-TRC ما، هر دو مورد predict می‌شود — اما در دو فاز مجزا و با دو مکانیزم یادگیری متفاوت:"))
a(blank())
a(mkp("فاز ۱ (FL): پیش‌بینی محبوبیت task (یعنی pattern) برای تصمیم‌گیری اینکه «چه چیزی» باید در cache قرار گیرد (pre-placement).", True))
a(mkp("فاز ۲ (RL): تصمیم‌گیری پویا درباره «کجا و چه زمانی» یک آیتم از cache خارج شود (eviction).", True))
a(blank())
a(mkp("محل cache نیز مشخص است: هر RSU یک cache محلی دارد. نتیجه task در cache همان RSU که task را اجرا کرده ذخیره می‌شود. در صورت محبوبیت بالا، نتیجه به RSUهای مجاور هم تکثیر (replicate) می‌شود."))
a(blank())

# === DETAIL: PHASE 1 ===
a(mkp("فاز ۱: پیش‌بینی محبوبیت task با Federated Learning", True, 28))
a(blank())
a(mkp("هدف این فاز پاسخ به سوال «چه نتایجی در آینده نزدیک درخواست خواهند شد؟» است. FL advisor یک مدل MLP (شبکه عصبی) روی هر RSU آموزش می‌دهد که بر اساس ۱۲ ویژگی، یک امتیاز محبوبیت (popularity score) بین ۰ تا ۱ تولید می‌کند."))
a(blank())
a(mkp("ویژگی‌های ورودی مدل FL:", True))
a(mkp("- فرکانس درخواست نرمالایز شده (RequestFreq)"))
a(mkp("- فرکانس لگاریتمی (LogFreq)"))
a(mkp("- اولویت task (Priority)"))
a(mkp("- اندازه داده (DataSize)"))
a(mkp("- محلی بودن task (IsLocal)"))
a(mkp("- سرعت متوسط خودروهای درخواست‌کننده (VehicleSpeed)"))
a(mkp("- بار فعلی RSU (RSULoad)"))
a(mkp("- ضریب افت محبوبیت زمانی (PopularityDecay)"))
a(mkp("- نوع task به صورت one-hot (TaskType_0 تا TaskType_3)"))
a(blank())
a(mkp("خروجی مدل: امتیاز محبوبیت در بازه [0,1]. آیتم‌هایی با امتیاز بالاتر از آستانه 0.5 برای pre-placement در cache انتخاب می‌شوند."))
a(blank())
a(mkp("پس FL دقیقاً pattern (الگوی محبوبیت) را predict می‌کند — و بر اساس آن تصمیم pre-placement گرفته می‌شود.", True))
a(blank())

# === DETAIL: WHERE ===
a(mkp("محل cache چگونه تعیین می‌شود؟", True, 28))
a(blank())
a(mkp("محل cache در سیستم ما یک تصمیم ثابت معماری نیست بلکه به صورت هوشمند و چند سطحی عمل می‌کند:"))
a(blank())
a(mkp("سطح ۱ — Cache محلی RSU:", True))
a(mkp("هر RSU یک cache با ظرفیت محدود (مثلاً ۱۰۰ آیتم) دارد. وقتی یک task اجرا می‌شود، نتیجه در cache همان RSU ذخیره می‌شود. این ساده‌ترین و سریع‌ترین سطح است."))
a(blank())
a(mkp("سطح ۲ — تکثیر به RSUهای مجاور (Hot Replication):", True))
a(mkp("اگر یک نتیجه cache شده بسیار پرتقاضا باشد (فرکانس بالاتر از آستانه hot_threshold)، به صورت خودکار در cache RSUهای مجاور هم کپی می‌شود. این تضمین می‌کند خودروهایی که بین RSUها حرکت می‌کنند هم به نتایج دسترسی دارند."))
a(blank())
a(mkp("سطح ۳ — Forwarding بین RSUها:", True))
a(mkp("اگر نتیجه در cache محلی نباشد، سیستم cache RSUهای دیگر را هم جستجو می‌کند (forwarding). در صورت یافتن، نتیجه به cache محلی هم کپی می‌شود."))
a(blank())
a(mkp("سطح ۴ — FL-based Pre-placement:", True))
a(mkp("قبل از اینکه درخواست‌ها برسند، FL advisor پیش‌بینی می‌کند کدام نتایج محبوب خواهند بود و آنها را از قبل در cache RSUهای مربوطه قرار می‌دهد (proactive pre-placement). این مهم‌ترین نوآوری کار ماست."))
a(blank())

# === DETAIL: PHASE 2 ===
a(mkp("فاز ۲: مدیریت پویای cache با Reinforcement Learning", True, 28))
a(blank())
a(mkp("وقتی cache پر شود، باید تصمیم گرفته شود کدام آیتم حذف شود. این تصمیم توسط RL agent گرفته می‌شود. RL agent وضعیت فعلی cache را مشاهده می‌کند (نرخ پر بودن، hit rate، بار RSU و ...) و یکی از ۵ عملیات eviction را انتخاب می‌کند:"))
a(blank())
a(mkp("- No Operation (حفظ وضع فعلی)"))
a(mkp("- Evict LRU (حذف کم‌استفاده‌ترین اخیراً)"))
a(mkp("- Evict LFU (حذف کم‌تکرارترین)"))
a(mkp("- Evict Random (حذف تصادفی)"))
a(mkp("- Shrink TTL (کاهش عمر همه آیتم‌ها)"))
a(blank())
a(mkp("RL agent با یادگیری آنلاین، بهترین سیاست eviction را بر اساس شرایط لحظه‌ای شبکه یاد می‌گیرد."))
a(blank())

# === SUMMARY ===
a(mkp("خلاصه: FL چه چیزی predict می‌کند؟", True, 28))
a(blank())
a(mkp("| سوال | پاسخ | مکانیزم |", True))
a(mkp("چه چیزی cache شود؟ | FL محبوبیت (pattern) هر task را predict می‌کند | FL Advisor (MLP + FedAvg)"))
a(mkp("کجا cache شود؟ | در RSU محلی + تکثیر به مجاورها در صورت محبوبیت بالا | Hot Replication + Forwarding"))
a(mkp("چه زمانی حذف شود؟ | RL agent بر اساس وضعیت لحظه‌ای تصمیم می‌گیرد | DQN Agent"))
a(blank())
a(mkp("بنابراین، وقتی می‌گوییم cache prediction، منظور ما پیش‌بینی محبوبیت task (pattern) است — نه پیش‌بینی مکان cache. مکان cache یک تصمیم معماری مشخص است (RSU محلی + تکثیر هوشمند)، در حالی که «چه چیزی باید cache شود» توسط FL predict می‌شود.", True))

body = "\n".join(lines)
body = body.replace(f' xmlns:w="{W}"', '')

doc = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}">
<w:body>
{body}
</w:body>
</w:document>'''

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CT)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/_rels/document.xml.rels', WRELS)
    z.writestr('word/document.xml', doc)

print(f"Created: {OUT}")
