# SusDE 套利监控 Telegram 机器人

这是一个自动监控 SusDE 套利机会的 Telegram 机器人，能够定期计算 USDT → SUSDE → USDE → USDT 的套利路径收益率。

## 功能特性

- 🔄 自动监控套利机会（USDT → SUSDE → USDE → USDT）
- 📊 计算年化收益率和实时盈亏
- 🚨 高收益告警（默认阈值 20%）
- 📱 Telegram 机器人交互
- 🌐 Web API 接口
- ☁️ Railway 部署支持

## 套利路径

1. **USDT → SUSDE** (通过 1inch 获取汇率)
2. **SUSDE → USDE** (通过智能合约解质押)
3. **USDE → USDT** (通过 1inch 获取汇率)

## 环境变量配置

在 Railway 或本地环境中设置以下环境变量：

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
INFURA_URL=https://eth.llamarpc.com/
```

### 获取 Telegram Bot Token

1. 在 Telegram 中找到 @BotFather
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称
4. 获取 Bot Token

### 获取 Chat ID

1. 启动机器人后，向机器人发送任意消息
2. 访问 `https://api.telegram.org/bot<YourBOTToken>/getUpdates`
3. 在返回的 JSON 中找到 `chat.id`

## 部署到 Railway

1. Fork 这个仓库
2. 在 Railway 中连接你的 GitHub 仓库
3. 设置环境变量
4. 部署应用

## Telegram 机器人命令

- `/start` - 启动机器人
- `/check` - 立即检查套利机会
- `/monitor` - 开始自动监控
- `/stop` - 停止自动监控
- `/status` - 查看监控状态

## Web API 接口

- `GET /` - 健康检查
- `GET /check?amount=100000` - 手动检查套利机会
- `GET /status` - 获取机器人状态

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 设置环境变量
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id

# 运行应用
python main_enhanced.py
```

## 监控逻辑

- 每小时自动检查一次套利机会
- 如果年化收益率超过 20%，立即发送告警
- 每 6 小时发送一次定期报告
- 所有告警记录保存到 `alerts.json` 文件

## 注意事项

- 数据仅供参考，不构成投资建议
- 实际交易存在滑点和手续费
- 价格影响为估算值
- 建议在实际使用前进行充分测试

## 技术栈

- Python 3.11
- Flask (Web API)
- Playwright (网页自动化)
- Web3.py (区块链交互)
- python-telegram-bot (Telegram API)
- Railway (部署平台)
