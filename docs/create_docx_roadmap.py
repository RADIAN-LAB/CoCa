"""Create a .docx file from roadmap_two_papers_fa.md without external dependencies."""
import os
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IN_MD = os.path.join(BASE_DIR, "roadmap_two_papers_fa.md")
OUT_DOCX = os.path.join(BASE_DIR, "roadmap_two_papers_fa.docx")

CT = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
RELS = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
WRELS = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"></Relationships>'
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def paragraph(text: str, *, bold: bool = False, size: int = 24, rtl: bool = True) -> str:
    b = '<w:b/><w:bCs/>' if bold else ''
    r = '<w:rtl/>' if rtl else ''
    ppr = '<w:pPr><w:bidi/><w:jc w:val="right"/></w:pPr>' if rtl else '<w:pPr></w:pPr>'
    return (
        f'<w:p xmlns:w="{W}">' 
        f'{ppr}<w:r><w:rPr>{b}<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>{r}</w:rPr>'
        f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>'
    )


def blank() -> str:
    return f'<w:p xmlns:w="{W}"><w:pPr><w:bidi/></w:pPr></w:p>'


def normalize_line(line: str) -> str:
    return line.strip().replace("**", "")


def line_to_paragraph(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return blank()

    if stripped == "---":
        return blank()

    if stripped.startswith("# "):
        return paragraph(normalize_line(stripped[2:]), bold=True, size=34)
    if stripped.startswith("## "):
        return paragraph(normalize_line(stripped[3:]), bold=True, size=30)
    if stripped.startswith("### "):
        return paragraph(normalize_line(stripped[4:]), bold=True, size=26)
    if stripped.startswith("- "):
        return paragraph("• " + normalize_line(stripped[2:]), size=24)
    if stripped.startswith("  - "):
        return paragraph("◦ " + normalize_line(stripped[4:]), size=22)

    return paragraph(normalize_line(stripped), size=24)


with open(IN_MD, "r", encoding="utf-8") as fh:
    md_lines = fh.readlines()

body_parts = [line_to_paragraph(line) for line in md_lines]
body = "\n".join(body_parts)
body = body.replace(f' xmlns:w="{W}"', '')

doc = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W}">
<w:body>
{body}
</w:body>
</w:document>'''

with zipfile.ZipFile(OUT_DOCX, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('[Content_Types].xml', CT)
    zf.writestr('_rels/.rels', RELS)
    zf.writestr('word/_rels/document.xml.rels', WRELS)
    zf.writestr('word/document.xml', doc)

print(f"Created: {OUT_DOCX}")
