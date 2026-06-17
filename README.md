# 万象清算 Galgame

这是《万象清算：重生后我让天命退位》的本地 Galgame / Visual Novel 改编工程。

## 运行

双击 `run.bat`。它会先验证数据和图片资源，再启动本地服务器并自动打开浏览器。

```text
http://localhost:8787
```

如果 8787 被占用，启动器会自动切到后续可用端口，并把实际地址写入 `.last_server.json`。

不要直接双击 `index.html`，浏览器会阻止读取 `data/script.json`。

## 公网分享

双击 `share_public.bat` 可以创建一个 Cloudflare Quick Tunnel 公网地址。地址会写入：

```text
.public_tunnel.json
```

注意：

- 这是免账号临时公网地址，不保证长期固定。
- 电脑睡眠、关机、关闭 Python 服务或关闭 `cloudflared.exe` 后，公网地址会失效。
- 如果失效，重新双击 `share_public.bat` 获取新的地址。

## 还原策略

- 游戏文本来自 `..\rebirth_system_xuanhuan_1m\exports\novel_full.txt`。
- `tools/build_script.py` 会把原文按章节和段落转换为 `data/manifest.json` 和 `data/chapters/*.json`；`data/script.json` 保留为完整备份。
- 显示内容保留原文段落；背景、角色、说话人只作为附加元数据。
- `data/manifest.json` 中记录了源文件 SHA-256，可用于确认脚本来自同一份原文。
- 首页只加载轻量目录，正文按章节懒加载，适合公网隧道分享。

## 已接入资源

当前已接入 25 张背景和 8 张透明角色立绘。

- `assets/backgrounds/key_art.png`：标题和命运清算封面。
- `assets/backgrounds/sacrifice_hall.png`：第一章祭坛/鼎炉开场。
- `assets/backgrounds/rebirth_room.png`：重生雨夜房间。
- `assets/backgrounds/qinglan_city_night.png`：青岚城雨夜街道。
- `assets/backgrounds/lu_family_hall.png`：陆家族堂/族老审判。
- `assets/backgrounds/lin_family_hall.png`：林家退婚厅。
- `assets/backgrounds/clan_stage.png`：陆家大比演武场。
- `assets/backgrounds/qinglan_zong_gate.png`：青岚宗山门/考核。
- `assets/backgrounds/law_enforcement_hall.png`：青岚宗执法殿。
- `assets/backgrounds/sect_trial_realm.png`：宗门秘境/试炼。
- `assets/backgrounds/pill_pavilion.png`：丹阁/炼丹危机。
- `assets/backgrounds/royal_court.png`：大乾王朝朝堂。
- `assets/backgrounds/sacred_judgement_hall.png`：圣地审判厅。
- `assets/backgrounds/tianjiao_banquet.png`：九州天骄宴。
- `assets/backgrounds/ancient_world_gate.png`：古界之门。
- `assets/backgrounds/ancient_battlefield.png`：古战场/禁区。
- `assets/backgrounds/burial_emperor_plain.png`：葬帝原。
- `assets/backgrounds/outer_heaven_battlefield.png`：天外战场。
- `assets/backgrounds/return_zero_gate.png`：归零之门。
- `assets/backgrounds/system_interface.png`：系统通用界面。
- `assets/backgrounds/system_mission_panel.png`：任务/奖励界面。
- `assets/backgrounds/causality_debt_ledger.png`：因果债册。
- `assets/backgrounds/shock_value_surge.png`：震惊值/显圣值涌动。
- `assets/backgrounds/reverse_causality_space.png`：逆转因果空间。
- `assets/characters/lu_chenyuan.png`：陆沉渊透明立绘。
- `assets/characters/lin_qingxue.png`：林清雪透明立绘。
- `assets/characters/qin_wuque.png`：秦无缺透明立绘。
- `assets/characters/yunheng_zhenren.png`：云衡真人透明立绘。
- `assets/characters/xiaozhu.png`：小竹透明立绘。
- `assets/characters/shen_qingluan.png`：沈清鸾透明立绘。
- `assets/characters/lu_chuan.png`：陆川透明立绘。
- `assets/characters/lu_chengyuan.png`：陆承远透明立绘。

## 重新生成脚本

```powershell
python .\tools\build_script.py
```

## 验证

```powershell
python .\tools\validate_game.py
```

验证内容包括：

- 原文 SHA-256 对齐。
- `data/script.json` 的章节、段落、正文逐段等于源小说。
- 背景和立绘 PNG 存在且分辨率达标。
- 角色立绘为透明 PNG。

## 当前限制

- 音频未接入。
- 已完成开局、家族、退婚、宗门、丹阁、王朝、圣地、古界、天外战场、系统界面等关键图片资源；更多角色和场景提示词在 `data/asset_prompts.json`。
- 这是长篇原文播放型 Galgame，当前没有分支选项，以保证剧情不偏离原作。
