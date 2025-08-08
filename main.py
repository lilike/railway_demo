from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route("/crawl", methods=["GET"])
def crawl():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            title = page.title()
            html = page.content()
            browser.close()
        return jsonify({"title": title, "html": html})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "Railway Playwright API is running", "endpoint": "/crawl?url=<target_url>"})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port)
