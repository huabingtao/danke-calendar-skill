---
name: danke-daily-reminder-skill
description: "专为《弹壳特攻队》每日活动倒计时与打卡提醒打造的专属创作技能。100%严格依据后台/danke-mcp-server查询出来的规则事实(statusText + digestNote)生成极简清单（单行展示），并在文末随机精选推荐3篇往期攻略以自然达标微信文中广告字数门槛，封面统一使用全特工专属底图并渲染「弹壳特攻队 今日提醒」。输出路径规范为 project/danke-creator/my-articles-md/提醒/YY.M.D/YY.M.D.md。当用户说'生成每日提醒'、'写提醒文章'、'今天的提醒'、'daily reminder'、'生成今日打卡'时触发。"
---

# danke-daily-reminder-skill

专为《弹壳特攻队》自媒体运营打造的**每日玩法倒计时与打卡提醒**内容创作 Skill。
全自动对接数据中心（`danke-mcp-server` / `danke-core`），动态计算当天全部活动规则状态，按统一规范生成客观、真实、无 AI 编造内容的极简每日打卡提醒初稿。

---

## 🎯 触发词

- "生成今天的每日提醒"
- "写一篇每日提醒公众号"
- "生成今日打卡"
- "查询今天有什么活动提醒并生成文章"
- "daily reminder"
- "/danke-daily-reminder-skill"

---

## ⚠️ 核心铁律与事实准则

1. **【100% 严格基于后台事实】**：
   - 文章正文的各规则描述与备注，**必须 100% 严格使用后台/API 查询返回的实际文案与备注（即 `statusText` 与 `digestNote`）**；
   - **严禁 AI 擅自扩写、推测或编造任何非后台配置的打卡建议/游戏攻略！**
2. **【单行紧凑清单格式】**：
   - 简短开篇后，直接使用数字序号列出玩法名称、倒计时状态与备注（单行紧凑括号包裹），**不使用 `>` 引用块**，例如：
     ```markdown
     1. **神秘商人**：离本轮【神秘商人】结束还剩 3 天（记得助力后及时购买）
     ```
3. **【Frontmatter 元数据纯自动驱动（废弃正文宏占位符）】**：
   - 往期推荐与二维码完全由 Frontmatter 中的 `recommendations:` 与 `qrcode_image:` 元数据声明；
   - **正文中严禁书写 `{{往期推荐}}` 或 `{{扫码获取更多精彩}}` 等已废弃的旧版手工占位符**，排版编译引擎会自动在免责声明前注入对应模块。
4. **【专属封面固化规范】**：
   - 封面底图统一使用全特工紫光专属原图（`assets/reminder_cover_bg.jpg`）；
   - 封面文字统一渲染为双行居中：`弹壳特攻队\n今日提醒`。
5. **【目录与文件命名规范】**：
   - 必须按短格式日期目录存放：`project/danke-creator/my-articles-md/提醒/YY.M.D/YY.M.D.md`（例如 `26.9.5/26.9.5.md`）。
6. **【专有名词宏自动标注】**：
   - 自动挂载 `auto_tag.py`，为游戏实体包裹 `{{...}}` 宏标签。

---

## 📝 标准 Frontmatter 与正文结构模板

```yaml
---
title: "【每日提醒】[M]月[D]日全玩法倒计时与打卡清单"
social_title: "[M]月[D]日全玩法打卡提醒"
summary: "[M]月[D]日《弹壳特攻队》全量[N]大玩法倒计时与打卡提醒汇总。"
tags:
  - 弹壳特攻队
  - 游戏攻略
  - 每日提醒
cover: "./cover.png"
cover_vertical: "./cover_vertical.png"
author: "弹壳呱呱"
date: YYYY-MM-DD
lastmod: YYYY-MM-DD
qrcode_image: "img://弹壳呱呱微信公众号二维码"
recommendations:
  - title: "【推荐文章一标题】"
    url: ""
  - title: "【推荐文章二标题】"
    url: ""
  - title: "【推荐文章三标题】"
    url: ""
---
```

### 正文模板

```markdown
![article-top](img://article-top){type=banner}

# 🔔 [M] 月 [D] 日全玩法倒计时与打卡提醒

各位特工大家早上好，我是呱呱！

今天（[M] 月 [D] 日）游戏内各玩法的最新倒计时与打卡提醒如下：

1. **[玩法名称1]**：[statusText1]（[digestNote1]）
2. **[玩法名称2]**：[statusText2]
3. **[玩法名称3]**：[statusText3]（[digestNote3]）

---

攻略创作不易，如果帮到了你，请大家多多**转发、点赞和关注**！你们的支持是呱呱持续输出干货的最大动力！

【免责声明】本攻略纯属个人**经验分享**，**仅供参考**，不构成任何消费建议。游戏版本更新较快，具体数值以游戏内实际表现为准。本攻略所引用的美术图片及游戏内截图版权均归 Habby 公司所有。
```

---

## 🛠️ 自动化执行命令

```bash
# 生成今日提醒（自动拉取数据、制作封面、生成文章并宏标注）
python3 .agents/skills/danke-daily-reminder-skill/scripts/generate_reminder.py

# 指定日期生成
python3 .agents/skills/danke-daily-reminder-skill/scripts/generate_reminder.py --date 2026-09-05
```
