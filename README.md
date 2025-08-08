# SusDE 套利监控系统

这是一个自动监控 SusDE 套利机会的系统，提供 Web API 接口和 Telegram 机器人功能，能够定期计算 USDT → SUSDE → USDE → USDT 的套利路径收益率，并将数据持久化存储到 Supabase 数据库。

## 🚀 功能特性

- 🔄 **自动监控**：系统启动时自动开启监控（默认每2分钟检查一次）
- 📊 **收益计算**：实时计算年化收益率和盈亏分析
- 🚨 **智能告警**：高收益机会自动告警（默认阈值 20%）
- 📱 **Telegram 集成**：机器人消息推送和交互
- 🌐 **Web API**：完整的 RESTful API 接口
- 💾 **数据持久化**：Supabase 数据库存储所有记录
- 📈 **统计分析**：历史数据统计和趋势分析
- ☁️ **云端部署**：支持 Railway 一键部署

## 💰 套利路径

1. **USDT → SUSDE** (通过 1inch DEX 获取汇率)
2. **SUSDE → USDE** (通过智能合约解质押获得收益)
3. **USDE → USDT** (通过 1inch DEX 回到USDT)

## ⚙️ 环境变量配置

复制 `.env.example` 文件为 `.env` 并配置以下变量：

### 基础配置
```bash
# Telegram 机器人配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# 以太坊节点配置
INFURA_URL=https://mainnet.infura.io/v3/your_project_id

# 监控配置
ALERT_THRESHOLD=20.0
PORT=8081
```

### Supabase 数据库配置
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
```

## 🗄️ 数据库设置

1. 在 [Supabase](https://supabase.com) 创建新项目
2. 在 SQL 编辑器中执行 `database_schema.sql` 创建表结构
3. 复制 API 密钥到环境变量

### 数据库表结构
- `arbitrage_checks` - 套利检查记录
- `alerts` - 告警记录
- 包含索引、视图和存储过程

## 📡 Web API 接口

### 监控管理
- `GET /` - 健康检查和API文档
- `GET /arbitrage/status` - 获取监控状态
- `POST /monitoring/start` - 启动定期监控
- `POST /monitoring/stop` - 停止定期监控
- `GET/POST /monitoring/config` - 监控配置管理

### 套利检查
- `GET/POST /arbitrage/check` - 手动检查套利机会

### 告警管理
- `GET /alerts/recent` - 获取最近告警
- `GET /alerts/history` - 获取告警历史
- `POST /alerts/clear` - 清空告警历史

### 数据库查询
- `GET /database/checks` - 获取检查记录
- `GET /database/alerts` - 获取数据库告警
- `GET /database/opportunities` - 获取盈利机会
- `GET /database/statistics` - 获取统计数据
- `POST /database/cleanup` - 清理旧数据
- `GET /database/status` - 数据库连接状态

## 🤖 Telegram 机器人命令

- `/start` - 启动机器人
- `/check` - 立即检查套利机会
- `/monitor` - 开始自动监控
- `/stop` - 停止自动监控
- `/status` - 查看监控状态

## 🚀 部署到 Railway

1. Fork 这个仓库
2. 在 Railway 中连接你的 GitHub 仓库
3. 设置所有必要的环境变量
4. 部署应用

Railway 会自动：
- 安装依赖 (`uv` 包管理器)
- 安装 Playwright 浏览器
- 启动 Web 服务

## 💻 本地开发

```bash
# 克隆仓库
git clone <your-repo-url>
cd railway_demo

# 安装依赖 (推荐使用 uv)
pip install uv
uv sync

# 或使用传统方式
pip install -e .

# 安装 Playwright 浏览器
playwright install chromium

# 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件，填入您的配置

# 运行应用
python main_backend.py
```

## 📊 监控配置

### 默认配置（自动启动）
- **自动启动**: ✅ 系统启动时自动开启监控
- **检查频率**: 每2分钟 (`*/2 * * * *`)
- **告警阈值**: 年化收益率 20%
- **检查金额**: 100,000 USDT
- **历史记录**: 最多保存100条告警

### 手动控制
虽然系统默认自动启动监控，但您仍可以通过API手动控制：
- `POST /monitoring/stop` - 停止监控
- `POST /monitoring/start` - 重新启动监控
- `POST /monitoring/config` - 修改监控配置

### Cron 表达式示例
- `*/2 * * * *` - 每2分钟
- `*/5 * * * *` - 每5分钟
- `*/15 * * * *` - 每15分钟
- `0 * * * *` - 每小时
- `0 9 * * *` - 每天9点
- `0 9 * * 1-5` - 工作日9点

## 📈 数据统计

系统提供丰富的统计功能：
- 检查成功率
- 平均年化收益率
- 最高收益记录
- 盈利机会频率
- 历史趋势分析

## ⚠️ 注意事项

- 📊 **数据仅供参考**：不构成投资建议
- 💸 **交易成本**：实际交易存在滑点和手续费
- 🔍 **价格影响**：大额交易可能产生价格影响
- 🧪 **充分测试**：建议在实际使用前进行测试
- 🔐 **安全性**：妥善保管所有密钥和环境变量

## 🛠️ 技术栈

- **后端**: Python 3.11+, Flask
- **数据库**: Supabase (PostgreSQL)
- **浏览器自动化**: Playwright
- **区块链交互**: Web3.py
- **消息推送**: python-telegram-bot
- **任务调度**: APScheduler
- **包管理**: uv
- **部署平台**: Railway

## 📝 更新日志

### v2.1.0
- ✅ **默认启动监控**：系统启动时自动开启监控功能
- ✅ 改进日志输出，显示监控状态和配置信息
- ✅ 更新健康检查接口，显示自动启动状态

### v2.0.0
- ✅ 集成 Supabase 数据库
- ✅ 调整默认监控频率为2分钟
- ✅ 新增数据库相关 API 接口
- ✅ 添加统计和分析功能
- ✅ 改进错误处理和日志记录
