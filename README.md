# 欢乐斗地主辅助程序

基于Windows PC的欢乐斗地主辅助程序，通过图像识别提供记牌功能和最优出牌建议。

## 功能特性

- ✅ **记牌器**: 实时统计对手剩余牌
- ✅ **智能出牌**: AI算法推荐最优出牌方案
- ✅ **图形界面**: 简洁直观的PyQt6界面
- ✅ **屏幕捕捉**: 自动识别游戏画面

## 项目结构

```
ddj_test/
├── run.py                 # 主入口
├── requirements.txt       # 依赖包
├── config/                # 配置
│   ├── settings.py       # 配置文件
│   └── templates/        # 卡片模板
├── src/
│   ├── capture/          # 屏幕捕捉
│   ├── ocr/              # 图像识别
│   ├── game/             # 游戏逻辑
│   ├── ai/               # AI算法
│   └── gui/              # 图形界面
├── tools/                # 工具
└── tests/                # 测试
```

## 安装步骤

### 1. 安装Python

需要Python 3.11或更高版本。

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows激活
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装Tesseract OCR (可选)

如需使用文字识别功能，下载并安装 Tesseract：
https://github.com/UB-Mannheim/tesseract/wiki

## 使用说明

### 首次使用

1. **创建卡片模板**
   - 打开欢乐斗地主游戏
   - 截图并裁剪每张卡片
   - 保存到 `config/templates/cards/` 目录
   - 命名格式: `3_spade.png`, `10_heart.png`, `joker_small.png`

2. **配置游戏区域**
   - 运行校准工具: `python tools/calibration_tool.py`
   - 或直接编辑 `config/config.json`

3. **运行程序**
   ```bash
   python run.py
   ```

### 游戏中使用

1. 打开微信 → 欢乐斗地主小程序
2. 启动辅助程序，点击"校准"设置游戏区域
3. 点击"启动"开始识别
4. 程序会自动显示:
   - 对手剩余牌统计
   - 推荐出牌方案

## 运行测试

```bash
# 游戏逻辑测试
python tests/test_game_logic.py

# AI模块测试
python tests/test_ai.py
```

## 牌型说明

程序支持以下牌型：

- 单张、对子、三张
- 三带一、三带二
- 顺子(≥5张)、连对(≥3对)
- 飞机、飞机带单/双
- 四带二
- 炸弹、王炸

## 注意事项

- ⚠️ 仅供学习交流使用
- ⚠️ 请遵守游戏规则和平台规定
- ⚠️ 使用风险自负

## 技术栈

- **GUI**: PyQt6
- **图像处理**: OpenCV, Pillow
- **屏幕捕捉**: MSS
- **语言**: Python 3.11+
