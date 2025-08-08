# Railway Playwright API

基于 Railway 部署的 Playwright 爬虫 HTTP 接口项目。

## 功能特性

- ✅ HTTP 接口接收爬虫请求
- ✅ 使用 Playwright + Chromium 进行网页爬取
- ✅ 返回页面标题和 HTML 内容
- ✅ 支持 Railway 一键部署
- ✅ 健康检查端点

## 接口说明

### 爬虫接口
- **请求方式**: GET
- **接口路径**: `/crawl`
- **参数**: 
  - `url` (必填) - 要爬取的网页 URL

### 响应格式
```json
{
  "title": "页面标题",
  "html": "<!DOCTYPE html>..."
}
```

### 错误响应
```json
{
  "error": "错误信息描述"
}
```

## 使用示例

```bash
# 爬取示例网站
curl "https://your-railway-domain.railway.app/crawl?url=https://example.com"

# 健康检查
curl "https://your-railway-domain.railway.app/"
```

## 本地开发

1. 安装依赖：
```bash
pip install -r requirements.txt
playwright install chromium
```

2. 启动服务：
```bash
python main.py
```

3. 测试接口：
```bash
curl "http://localhost:5000/crawl?url=https://example.com"
```

## Railway 部署

1. 将代码推送到 GitHub 仓库
2. 在 Railway 中连接该仓库
3. Railway 会自动识别 `Procfile` 并执行部署
4. 部署完成后获取域名进行测试

## 项目结构

```
railway_demo/
├── main.py          # Flask 应用主文件
├── requirements.txt # Python 依赖
├── Procfile        # Railway 部署配置
├── start.sh        # 启动脚本
└── README.md       # 项目说明
```

## 技术栈

- **语言**: Python 3.11+
- **Web 框架**: Flask
- **爬虫框架**: Playwright (Chromium)
- **部署平台**: Railway
