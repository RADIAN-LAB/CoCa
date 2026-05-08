"""Create .docx for reviewer response about redundancy types - pure Python."""
import zipfile, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "reviewer_response_redundancy_types.docx")

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
a(mkp("پاسخ به ریویور: آیا سیستم هر دو نوع افزونگی (درون‌خودرویی و بین‌خودرویی) را پوشش می‌دهد؟", True, 32))
a(blank())

# === QUESTION ===
a(mkp("سوال ریویور", True, 30))
a(mkp("دو موضوع مهم است: (۱) خودرو A اقدام به ارسال تسک‌های تکراری می‌کند، و (۲) دو خودروی A و B اقدام به ارسال تسک‌های تکراری می‌کنند (مثلاً هر دو کنار هم هستند و هر دو در حال تصویربرداری از یک شی هستند). آیا هدف ما رسیدگی به هر دوی این موارد است یا فقط یکی؟"))
a(blank())

# === SHORT ANSWER ===
a(mkp("پاسخ کوتاه: هر دو نوع افزونگی پوشش داده می‌شود.", True, 28))
a(blank())
a(mkp("سیستم FL-RL-TRC به طور ذاتی هر دو سناریو را مدیریت می‌کند. دلیل آن طراحی cache key است که مستقل از هویت خودرو عمل می‌کند."))
a(blank())

# === MECHANISM ===
a(mkp("مکانیزم: چرا هر دو نوع افزونگی پوشش داده می‌شود؟", True, 28))
a(blank())
a(mkp("کلید cache در سیستم ما فقط بر اساس سه ویژگی ذاتی task ساخته می‌شود:", True))
a(mkp("key = hash(task_type, priority, data_size)", False, 24, False))
a(blank())
a(mkp("نکته کلیدی: هویت خودرو (vehicle ID)، زمان ارسال، و شناسه RSU در cache key دخیل نیستند."))
a(blank())
a(mkp("این به این معناست که:"))
a(blank())

a(mkp("سناریو ۱ — افزونگی درون‌خودرویی (Intra-Vehicle Redundancy):", True))
a(mkp("خودرو A در زمان t1 تسک «تحلیل ترافیک، اولویت ۲، اندازه ۵۰۰ کیلوبایت» ارسال می‌کند. سپس همان خودرو A در زمان t2 همان تسک را دوباره ارسال می‌کند. چون cache key هر دو یکسان است (task_type و priority و data_size تغییر نکرده)، بار دوم cache hit می‌شود و محاسبه تکرار نمی‌شود."))
a(blank())

a(mkp("سناریو ۲ — افزونگی بین‌خودرویی (Inter-Vehicle Redundancy):", True))
a(mkp("خودرو A و خودرو B هر دو کنار هم هستند و هر دو تسک «پردازش تصویر سنسور، اولویت ۲، اندازه ۵۰۰ کیلوبایت» ارسال می‌کنند. چون vehicle ID در cache key نیست، هر دو درخواست cache key یکسانی تولید می‌کنند. اگر تسک خودرو A اول اجرا شود، نتیجه cache می‌شود و خودرو B بدون اجرای مجدد از cache پاسخ می‌گیرد."))
a(blank())

# === WHY THIS DESIGN ===
a(mkp("چرا cache key مستقل از هویت خودرو طراحی شده؟", True, 28))
a(blank())
a(mkp("این یک تصمیم طراحی آگاهانه است. در محیط VANET:"))
a(blank())
a(mkp("۱. محاسبه وابسته به «چه چیزی» محاسبه می‌شود، نه «چه کسی» درخواست کرده.", True))
a(mkp("مثلاً نتیجه «تحلیل ترافیک تقاطع X» برای همه خودروهای آن منطقه یکسان است، صرف‌نظر از اینکه کدام خودرو درخواست داده."))
a(blank())
a(mkp("۲. سناریوی بین‌خودرویی (سناریو ۲) فراوان‌ترین نوع افزونگی است.", True))
a(mkp("همان‌طور که در Problem Statement مقاله آمده: «ده‌ها خودرو ممکن است به طور مستقل درخواست‌های محاسباتی یکسان ارسال کنند — مانند تحلیل ترافیک، بهینه‌سازی مسیر برای مقاصد مشترک، یا پردازش داده‌های محیطی از مناطق پوشش مشترک سنسور.»"))
a(blank())
a(mkp("۳. سناریوی درون‌خودرویی (سناریو ۱) هم به طور طبیعی پوشش داده می‌شود.", True))
a(mkp("اگر خودرویی در یک بازه زمانی کوتاه همان تسک را تکرار کند (مثلاً سنسور هر ثانیه تصویر می‌گیرد)، cache key یکسان تولید می‌شود و نتیجه قبلی بازاستفاده می‌شود."))
a(blank())

# === SUPPORTING MECHANISMS ===
a(mkp("مکانیزم‌های تکمیلی برای پوشش هر دو سناریو", True, 28))
a(blank())
a(mkp("علاوه بر cache key مستقل از خودرو، مکانیزم‌های زیر هر دو نوع افزونگی را تقویت می‌کنند:"))
a(blank())
a(mkp("Hot Replication:", True))
a(mkp("اگر یک نتیجه بسیار پرتقاضا باشد (هم از یک خودرو، هم از چند خودرو)، به صورت خودکار در cache RSUهای مجاور تکثیر می‌شود. این تضمین می‌کند خودروهایی که بین RSUها حرکت می‌کنند هم از cache بهره ببرند."))
a(blank())
a(mkp("Cache Forwarding:", True))
a(mkp("اگر خودرو B در RSU دیگری باشد و همان تسک را درخواست کند، سیستم cache RSUهای مجاور را هم جستجو می‌کند (forwarding). این سناریوی بین‌خودرویی را حتی در صورت توزیع جغرافیایی خودروها پوشش می‌دهد."))
a(blank())
a(mkp("FL-based Pre-placement:", True))
a(mkp("مدل FL الگوهای محبوبیت task را یاد می‌گیرد. این الگوها شامل هر دو نوع تکرار هستند: هم تکرار درون‌خودرویی (یک خودرو مکرراً یک تسک خاص را درخواست می‌کند) و هم تکرار بین‌خودرویی (تسک‌های رایج در یک منطقه). FL این الگوها را در قالب فرکانس درخواست (RequestFreq) و ضریب افت محبوبیت (PopularityDecay) ثبت می‌کند."))
a(blank())

# === SUMMARY TABLE ===
a(mkp("جدول خلاصه", True, 28))
a(blank())
a(mkp("| سناریو | توضیح | آیا پوشش داده شده؟ | مکانیزم |", True))
a(mkp("خودرو A تسک تکراری ارسال می‌کند | افزونگی درون‌خودرویی | بله | cache key مستقل از زمان + TTL"))
a(mkp("خودرو A و B تسک یکسان ارسال می‌کنند | افزونگی بین‌خودرویی | بله | cache key مستقل از vehicle ID + Forwarding + Replication"))
a(mkp("خودرو A و B در RSUهای مختلف هستند | افزونگی بین‌خودرویی توزیع‌شده | بله | Cache Forwarding + Hot Replication"))
a(blank())

# === RECOMMENDATION ===
a(mkp("پیشنهاد برای اصلاح مقدمه", True, 28))
a(blank())
a(mkp("ریویور درست می‌فرماید که باید هر دو نوع افزونگی به صراحت در مقدمه ذکر شود. پیشنهاد می‌شود جمله زیر به مقدمه اضافه شود:"))
a(blank())
a(mkp("«افزونگی محاسباتی در VANETها در دو سطح رخ می‌دهد: (۱) افزونگی درون‌خودرویی، که در آن یک خودرو به صورت مکرر محاسبات یکسانی درخواست می‌کند (مثلاً خوانش مکرر سنسور از محیط بدون تغییر)، و (۲) افزونگی بین‌خودرویی، که در آن چندین خودرو در یک منطقه جغرافیایی به طور مستقل محاسبات یکسانی درخواست می‌کنند (مثلاً تصویربرداری همزمان از یک شی یا تحلیل ترافیک یک تقاطع). سیستم FL-RL-TRC با طراحی cache key مبتنی بر ویژگی‌های ذاتی task (نه هویت خودرو)، هر دو نوع افزونگی را به طور یکپارچه مدیریت می‌کند.»", True))

body = "\n".join(lines)

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
