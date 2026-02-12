# Deployment Guide

## 目标选择
你有两条主路线：

1. 网页直接玩（推荐给网友最方便）
2. 下载应用后玩（桌面安装包）

## 路线 A：网页直接玩（浏览器）
当前项目是 `pygame` 桌面程序，直接部署到普通网页不行，需要一层转换。

### 方案 A1：用 pygbag 打包成 WebAssembly（最快）
- 适合：个人作品展示、轻量分享
- 优点：用户打开网页就能玩
- 缺点：对 pygame 功能有兼容限制，性能略低于桌面版

步骤：
1. 安装 `pygbag`
2. 调整入口以适配 pygbag（通常改为 `asyncio` 事件循环风格）
3. `pygbag` 打包出 `index.html + wasm` 静态文件
4. 部署到静态站点：GitHub Pages / Netlify / Vercel

### 方案 A2：重写前端版（长期最稳）
- 技术：`Phaser` / `PixiJS` / `Godot Web`
- 优点：浏览器兼容最好，后期可做联机和账号
- 缺点：需要重写，不是“直接迁移”

## 路线 B：下载应用后玩（桌面）
### 方案 B1：PyInstaller 打包 exe（Windows）
- 适合：不想改现有 pygame 代码
- 优点：实现快，几乎不改逻辑
- 缺点：包体较大

示例命令：
```powershell
py -3 -m pip install pyinstaller
py -3 -m PyInstaller --noconfirm --windowed --onefile tank_battle.py
```
产物在 `dist/` 下，可直接发给用户运行。

## 数据与排行榜说明
当前排行榜是本地 SQLite（`game_stats.db`）：
- 网页版：通常改为后端数据库（Supabase/PostgreSQL）
- 桌面版：继续本地 SQLite 即可

## 推荐路线（按你的当前项目）
1. 先做桌面版发布：最快给网友试玩
2. 再尝试 pygbag 网页版验证可行性
3. 如果要长期运营，再规划前端重写 + 云端排行榜
