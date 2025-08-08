from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import base64
import os
from datetime import datetime

app = Flask(__name__)

@app.route("/crawl", methods=["GET"])
def crawl():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400
    
    # 可选参数
    wait_for_js = request.args.get("wait_js", "false").lower() == "true"
    take_screenshot = request.args.get("screenshot", "false").lower() == "true"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            
            # 等待 JS 渲染完成（可选增强功能）
            if wait_for_js:
                page.wait_for_load_state("networkidle")
            
            title = page.title()
            html = page.content()
            
            result = {"title": title, "html": html}
            
            # 截图功能（可选增强功能）
            if take_screenshot:
                screenshot_path = f"/tmp/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=screenshot_path)
                
                # 将截图转换为 base64 返回
                if os.path.exists(screenshot_path):
                    with open(screenshot_path, "rb") as f:
                        screenshot_data = base64.b64encode(f.read()).decode()
                        result["screenshot"] = screenshot_data
                    os.remove(screenshot_path)  # 清理临时文件
            
            browser.close()
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "Railway Playwright API is running",
        "endpoints": {
            "crawl": "/crawl?url=<target_url>",
            "parameters": {
                "url": "目标网页 URL (必填)",
                "wait_js": "等待 JS 渲染完成 (可选, true/false, 默认 false)",
                "screenshot": "返回页面截图 (可选, true/false, 默认 false)"
            }
        },
        "example": "/crawl?url=https://example.com&wait_js=true&screenshot=true"
    })

@app.route("/health", methods=["GET"])
def simple_health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
