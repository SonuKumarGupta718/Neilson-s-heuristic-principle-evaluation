from flask import Flask, render_template, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import re
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)


class NielsenHCIAnalyzer:
    def __init__(self, url):
        self.url = url
        self.report = defaultdict(list)

    def fetch_soup(self):
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(self.url, timeout=10, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def analyze(self):
        soup = self.fetch_soup()
        text = soup.get_text().lower()

        heuristics = [
            {
                "id": 1,
                "title": "Visibility of System Status",
                "icon": "📡",
                "result": "Status indicators found." if "loading" in text else "No obvious system status feedback detected.",
                "pass": "loading" in text
            },
            {
                "id": 2,
                "title": "Match Between System and Real World",
                "icon": "🌍",
                "result": "Technical jargon detected." if re.search(r"api|backend|exception", text) else "Language appears user-friendly.",
                "pass": not bool(re.search(r"api|backend|exception", text))
            },
            {
                "id": 3,
                "title": "User Control and Freedom",
                "icon": "🕹️",
                "result": "Undo/Cancel navigation found." if soup.find("a", string=re.compile("back|cancel|undo", re.I)) else "No undo or cancel options detected.",
                "pass": bool(soup.find("a", string=re.compile("back|cancel|undo", re.I)))
            },
            {
                "id": 4,
                "title": "Consistency and Standards",
                "icon": "📐",
                "result": "Standard UI components (buttons/forms) detected." if soup.find("button") else "Few standard UI components detected.",
                "pass": bool(soup.find("button"))
            },
            {
                "id": 5,
                "title": "Error Prevention",
                "icon": "🛡️",
                "result": "Forms detected — input validation should be reviewed." if soup.find("form") else "No forms detected.",
                "pass": bool(soup.find("form"))
            },
            {
                "id": 6,
                "title": "Recognition Rather Than Recall",
                "icon": "🧠",
                "result": "Labels detected to aid recognition." if soup.find("label") else "Few labels detected.",
                "pass": bool(soup.find("label"))
            },
            {
                "id": 7,
                "title": "Flexibility and Efficiency of Use",
                "icon": "⚡",
                "result": "Keyboard shortcuts detected." if soup.find(attrs={"accesskey": True}) else "No keyboard shortcuts detected.",
                "pass": bool(soup.find(attrs={"accesskey": True}))
            },
            {
                "id": 8,
                "title": "Aesthetic and Minimalist Design",
                "icon": "🎨",
                "result": "High content density detected." if len(text) > 5000 else "Content density appears reasonable.",
                "pass": len(text) <= 5000
            },
            {
                "id": 9,
                "title": "Help Users Recognize, Diagnose, and Recover from Errors",
                "icon": "🔧",
                "result": "Error messages detected." if re.search(r"error|invalid|failed", text) else "No visible error messages detected.",
                "pass": bool(re.search(r"error|invalid|failed", text))
            },
            {
                "id": 10,
                "title": "Help and Documentation",
                "icon": "📖",
                "result": "Help/FAQ links detected." if soup.find("a", string=re.compile("help|faq|support", re.I)) else "No help documentation detected.",
                "pass": bool(soup.find("a", string=re.compile("help|faq|support", re.I)))
            },
        ]

        passed = sum(1 for h in heuristics if h["pass"])
        score = int((passed / len(heuristics)) * 100)

        return {"heuristics": heuristics, "score": score, "url": self.url}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL is required"}), 400
    if not url.startswith("http"):
        url = "https://" + url
    try:
        analyzer = NielsenHCIAnalyzer(url)
        result = analyzer.analyze()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    data = request.get_json()
    heuristics = data.get("heuristics", [])
    url = data.get("url", "")
    score = data.get("score", 0)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.setFillColorRGB(0.1, 0.4, 0.9)
    c.drawString(40, y, "Nielsen HCI Heuristic Evaluation Report")
    y -= 20

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(40, y, f"URL: {url}")
    y -= 15
    c.drawString(40, y, f"Usability Score: {score}/100")
    y -= 25

    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(40, y, width - 40, y)
    y -= 20

    c.setFont("Helvetica", 11)
    for h in heuristics:
        if y < 80:
            c.showPage()
            y = height - 50

        status = "✓ PASS" if h["pass"] else "✗ ISSUE"
        if h["pass"]:
            c.setFillColorRGB(0.1, 0.7, 0.3)
        else:
            c.setFillColorRGB(0.9, 0.3, 0.2)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, f"{h['id']}. {h['title']}   [{status}]")
        y -= 15

        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica", 10)
        c.drawString(55, y, f"→ {h['result']}")
        y -= 20

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="heuristic_report.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
