# 坦克大战 - 用户手册

## 1. 游戏简介
这是一款基于 Python + pygame 的本地单机坦克小游戏，支持：
- 难度选择（简单 / 中等 / 困难）
- 5 关递进挑战
- 3 条命机制
- 砖墙/钢墙障碍
- 本地排行榜与评分系统（SQLite）

## 2. 运行环境
- Windows（推荐）
- Python 3.10+

## 3. 安装与启动
在项目目录 `d:\PycharmProjects\practice` 下执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python tank_battle.py
```

如果激活虚拟环境被策略拦截：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 4. 菜单流程
游戏启动后是 **两步流程**：

### Step 1/2 输入玩家名
- 直接键盘输入名字（最多 16 字符）
- `Backspace` 删除
- `N` 生成随机名字
- `Enter` 进入下一步

### Step 2/2 选择难度
- `1` 选择简单
- `2` 选择中等
- `3` 选择困难
- `Enter` 开始游戏

菜单会显示当前难度对应的排行榜。

## 5. 游戏操作
- 移动：`WASD` 或方向键
- 开火：`Space`
- 返回菜单：`R`

## 6. 玩法说明
- 每局共 5 关，逐关增强敌人数量与压力。
- 玩家初始 3 条命，被击中或撞敌会掉命。
- 掉命后会在出生点复活，并有短暂无敌闪烁时间。
- 清空当前关敌人进入下一关。
- 第 5 关通关触发庆祝动画。

## 7. 障碍物规则
- **砖墙（Brick）**：可被子弹打碎（多次命中后消失）
- **钢墙（Steel）**：不可破坏，只会挡子弹
- 坦克无法穿过障碍物

## 8. 评分系统与排行榜
每局结束会写入本地数据库 `game_stats.db`，记录：
- 玩家名
- 难度
- 到达关卡
- 是否通关
- 游玩时长
- 击杀数
- 死亡数
- 子弹消耗
- 评分

评分综合考虑：
- 击杀效率
- 命中效率（击杀/开火）
- 用时
- 生存情况
- 是否通关奖励

不同难度评分上限不同：
- 简单：最高 7.5
- 中等：最高 9.0
- 困难：最高 10.0

## 9. 可配置项（给运营/开发）
主要配置在 `tank_game/config.py`：
- 窗口尺寸、FPS
- 难度参数（移动速度、开火冷却、敌人数等）
- 评分权重与目标参数
- 难度评分上限
- 排行榜条数与数据库路径

## 10. 常见问题
### Q1: 按键没反应？
请先点击游戏窗口确保焦点在窗口内，再进行操作。

### Q2: 能清空排行榜吗？
可删除项目根目录的 `game_stats.db`，下次启动会自动重建。

### Q3: 能改窗口大小吗？
可以，在 `tank_game/config.py` 里修改 `SCREEN_WIDTH` 和 `SCREEN_HEIGHT`。

## 11. 项目结构
```text
practice/
├─ tank_battle.py
├─ tank_game/
│  ├─ game.py
│  ├─ entities.py
│  ├─ input_state.py
│  ├─ scoring.py
│  ├─ storage.py
│  ├─ namegen.py
│  └─ config.py
├─ README.md
└─ USER_MANUAL.md
```

## 12. 部署说明
如果你想给网友玩，请看 `DEPLOYMENT_GUIDE.md`（包含网页玩和下载玩两条路线）。
