"""Create .docx without external dependencies."""
import zipfile, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "reviewer_response_task_result_caching.docx")

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
    return f'<w:p xmlns:w="{W}">{ppr}<w:r><w:rPr>{b}<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>{r}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>'

def blank():
    return f'<w:p xmlns:w="{W}"><w:pPr><w:bidi/></w:pPr></w:p>'

lines = []
a = lines.append

a(mkp("پاسخ به ریویور: چرا نتیجه task را کش می‌کنیم نه خود task را؟", True, 36))
a(blank())
a(mkp("سوال ریویور", True, 30))
a(mkp("چرا به جای کش کردن نتیجه task، خود task (یعنی سرویس/برنامه اجرایی) را کش نمی‌کنیم تا حتی با ورودی و خروجی متفاوت هم بتوانیم پاسخ دهیم؟"))
a(blank())

a(mkp("سه رویکرد کشینگ در ادبیات", True, 30))
a(mkp("در ادبیات MEC سه رویکرد کشینگ متمایز وجود دارد:"))
a(blank())
a(mkp("Content Caching: ذخیره فایل‌های داده (نقشه، ویدیو). فقط تأخیر دانلود را کاهش می‌دهد؛ محاسبه همچنان باید انجام شود.", True))
a(blank())
a(mkp("Service Caching (کش خود task): ذخیره برنامه/سرویس اجرایی روی edge server. با ورودی‌های متفاوت هم قابل استفاده است، اما task هر بار باید از اول اجرا شود.", True))
a(mkp('Liu et al. (2022) تعریف می‌کنند: «Service caching به کش کردن برنامه‌ها و کتابخانه‌های مورد نیاز اشاره دارد. فقط سرورهایی که سرویس مربوطه را دارند می‌توانند task کاربر را اجرا کنند.»'))
a(blank())
a(mkp("Task Result Caching (رویکرد ما): ذخیره خروجی محاسبه‌شده. در صورت cache hit، محاسبه کاملاً حذف می‌شود و فقط تأخیر ارتباطی باقی می‌ماند.", True))
a(blank())

a(mkp("چرا Result Caching بهتر از Service Caching است؟", True, 30))
a(blank())
a(mkp("۱. Service Caching محاسبه تکراری را حذف نمی‌کند.", True))
a(mkp("مثال: ۲۰ خودرو در یک تقاطع «تحلیل ترافیک» درخواست می‌کنند."))
a(mkp("- Service Caching: برنامه موجود است ← ۲۰ بار اجرا ← ۲۰ برابر مصرف CPU و انرژی"))
a(mkp("- Result Caching (ما): یک بار اجرا، ۱۹ بار از cache ← صرفه‌جویی حدود ۹۵٪"))
a(blank())
a(mkp("۲. گلوگاه اصلی محاسبه تکراری است، نه نبود سرویس.", True))
a(mkp("در معماری SDN-VANET، سرویس‌ها از قبل روی RSU نصب هستند. مشکل واقعی اجرای مکرر یک محاسبه مشابه توسط خودروهای مختلف است — نه نبود برنامه."))
a(blank())
a(mkp("۳. ورودی taskها در VANET بسیار تکراری است.", True))
a(mkp("تحقیقات نشان می‌دهد فرکانس مشاهده محیط بسیار بیشتر از تغییرات محیط است (Zhang et al., 2024). خودروهای یک منطقه جغرافیایی محاسبات یکسان درخواست می‌کنند. نتایج تجربی ما (نرخ cache hit برابر ۹۷٪) تأیید می‌کند که اکثریت قریب به اتفاق درخواست‌ها با نتایج قبلی مطابقت دارند."))
a(blank())
a(mkp("۴. صرفه‌جویی انرژی فقط با Result Caching ممکن است.", True))
a(mkp("در مدل انرژی ما، cache hit انرژی محاسباتی را به صفر می‌رساند. Service caching این قابلیت را ندارد چون task همچنان اجرا می‌شود."))
a(blank())

a(mkp("پشتیبانی کارهای پیشین", True, 30))
a(blank())
a(mkp("CoxNet (Nour et al., 2021):", True))
a(mkp("معماری computation reuse برای edge computing. نتایج محاسبات قبلی را بازاستفاده می‌کند و زمان اجرای task را تا ۵۰٪ کاهش می‌دهد."))
a(blank())
a(mkp("Zhang et al. (arXiv:2401.01017, 2024):", True))
a(mkp("در survey خود تأیید می‌کنند که «ورودی یک task در بازه زمانی، تا حد زیادی تکراری است» و computation reuse بهبود عملکرد قابل توجهی دارد."))
a(blank())
a(mkp("Xu et al. (Digital Signal Processing, 2024):", True))
a(mkp("صریحاً بیان می‌کنند که در شبکه‌های خودرویی، داده محاسباتی یک خودرو می‌تواند توسط خودروهای دیگر با نیازهای مشابه بازاستفاده شود."))
a(blank())
a(mkp("Nour et al. (ACM Computing Surveys, 2023, DOI: 10.1145/3609504):", True))
a(mkp("در survey جامع خود، computation reuse را به عنوان یک پارادایم متمایز و پیشرفته‌تر نسبت به content caching و service caching دسته‌بندی می‌کنند."))
a(blank())

a(mkp("جدول مقایسه", True, 30))
a(blank())
a(mkp("جنبه | Content Caching | Service Caching (کش خود task) | Task Result Caching (ما)", True))
a(mkp("چه چیزی کش می‌شود | فایل داده | برنامه/سرویس | خروجی محاسبه"))
a(mkp("حذف محاسبه تکراری | خیر | خیر | بله"))
a(mkp("صرفه‌جویی CPU | ۰٪ | ۰٪ | حدود ۱۰۰٪"))
a(mkp("پاسخ به ورودی متفاوت | — | بله (اجرای مجدد) | فقط برای taskهای یکسان"))
a(mkp("مناسب وقتی taskها تکراری‌اند | — | سود محدود | حداکثر سود"))
a(blank())

a(mkp("نکته نهایی", True, 30))
a(mkp("دو رویکرد متضاد نیستند بلکه مکمل هستند. در معماری ما، سرویس‌ها از قبل روی RSU مستقر هستند (service caching ضمنی) و Result Caching به عنوان یک لایه بهینه‌سازی اضافی عمل می‌کند. اگر تنوع ورودی بالا بود (cache hit پایین)، service caching ارجح بود — اما ماهیت ترافیک خودرویی (تکرار بالای محاسبات مشابه) result caching را به استراتژی برتر تبدیل می‌کند."))

body = "\n".join(lines)
# Remove per-element namespace, use it on root
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
