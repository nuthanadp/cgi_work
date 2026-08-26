import re

def format_headings(text):
    return re.sub(r'^(.*[📌🎯💻🧠].*)$', r'<b>\1</b>', text, flags=re.MULTILINE)

def bullets_to_html(text):
    lines = text.split("\n")
    html_lines = []
    in_list = False
    for line in lines:
        line = line.strip()
        line = re.sub(r'\b(must|should|optional)\b', r'<span class="keyword">\1</span>', line, flags=re.IGNORECASE)
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:]}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if line:
                html_lines.append(line)
    if in_list:
        html_lines.append("</ul>")
    return "<br>".join(html_lines)

def format_preview(text):
    formatted = format_headings(text)
    return bullets_to_html(formatted)
