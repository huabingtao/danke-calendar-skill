#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_reminder.py - 每日玩法倒计时与打卡提醒文章自动生成工具
专为《弹壳特攻队》自媒体打造，100%严格依据后台/数据中心返回的实际规则与备注生成极简清单。
输出路径规范: project/danke-creator/my-articles-md/提醒/YY.M.D/YY.M.D.md
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path


def find_workspace_root() -> Path:
    """自动向上查找工作区根目录"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "project" / "danke-creator").is_dir():
            return parent
    return Path("/home/guagua/workspace")


def to_short_date_str(date_obj: datetime.date) -> str:
    """将日期转换为短格式字符串，例如 2026-09-05 -> 26.9.5"""
    yy = date_obj.year % 100
    m = date_obj.month
    d = date_obj.day
    return f"{yy}.{m}.{d}"


def fetch_daily_digest(target_date: str, api_base: str = "http://localhost:3000") -> dict:
    """从 danke-core API 获取指定日期的提醒聚合数据"""
    url = f"{api_base}/reminders/daily-digest?date={target_date}"
    req = urllib.request.Request(url, headers={"User-Agent": "danke-daily-reminder-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data
    except Exception as e:
        print(f"⚠️ 无法从 API ({url}) 获取提醒数据: {e}")
        print("🔄 尝试直接连接本地 SQLite 数据库进行计算...")
        return compute_from_sqlite(target_date)

    return {"date": target_date, "totalActiveItems": 0, "items": []}


def compute_from_sqlite(target_date_str: str) -> dict:
    """本地 SQLite 兜底计算纯函数"""
    try:
        import sqlite3
        ws = find_workspace_root()
        db_path = ws / "project" / "danke-core" / "data" / "danke.db"
        if not db_path.exists():
            return {"date": target_date_str, "items": []}

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, category, ruleType, startDate, durationDays, cycleDays, hasRedeemDay, digestNote, digestTemplate, redeemTemplate, enabled FROM ReminderRule WHERE enabled = 1")
        rows = cursor.fetchall()
        conn.close()

        target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
        items = []

        for row in rows:
            (rule_id, name, cat, rule_type, start_date_str, duration_days, cycle_days, has_redeem, digest_note, digest_tmpl, redeem_tmpl, enabled) = row
            if not start_date_str or not duration_days:
                continue

            start_date = datetime.datetime.fromisoformat(start_date_str.replace("Z", "+00:00")).date()
            diff_days = (target_date - start_date).days
            if diff_days < 0:
                continue

            cycle = cycle_days or duration_days
            day_in_cycle = diff_days % cycle

            if day_in_cycle < duration_days:
                days_left = duration_days - day_in_cycle
                is_first = (day_in_cycle == 0)
                status_text = f"离本轮【{name}】结束还剩 {days_left} 天"
                if digest_tmpl:
                    status_text = digest_tmpl.replace("{name}", name).replace("{days}", str(days_left))
                
                full_text = f"{status_text}（{digest_note}）" if digest_note else status_text
                items.append({
                    "id": rule_id,
                    "name": name,
                    "daysRemaining": days_left,
                    "isFirstDay": is_first,
                    "isRedeemDay": False,
                    "statusText": status_text,
                    "digestNote": digest_note,
                    "fullText": full_text,
                })
            elif has_redeem and day_in_cycle == duration_days:
                status_text = f"今日是【{name}】专属兑换日，请尽快兑换！"
                if redeem_tmpl:
                    status_text = redeem_tmpl.replace("{name}", name).replace("{days}", "0")
                full_text = f"{status_text}（{digest_note}）" if digest_note else status_text
                items.append({
                    "id": rule_id,
                    "name": name,
                    "daysRemaining": 0,
                    "isFirstDay": False,
                    "isRedeemDay": True,
                    "statusText": status_text,
                    "digestNote": digest_note,
                    "fullText": full_text,
                })

        return {"date": target_date_str, "totalActiveItems": len(items), "items": items}
    except Exception as e:
        print(f"❌ SQLite 兜底计算失败: {e}")
        return {"date": target_date_str, "items": []}


RECOMMENDED_ARTICLES_POOL = [
    {
        "title": "【新手进阶】高频问答FAQ第一弹：特工选择、狼马对比与配件过载全指南",
        "url": "",
    },
    {
        "title": "【资源精算】公会商店买空要78万？！月度全兑换精算与收益实测",
        "url": "",
    },
    {
        "title": "【道具评测】日常挑战新增芯片与载具核心兑换深度解析",
        "url": "",
    },
    {
        "title": "【高难通关】新版区域行动全关卡通关攻略与词条克制技巧",
        "url": "",
    },
    {
        "title": "【特工评测】SP特工伏尔甘全方位实战测评与养成建议",
        "url": "",
    },
    {
        "title": "【爬塔冲榜】试炼之路高层爬塔通关思路与技能流派盘点",
        "url": "",
    },
]


def build_reminder_article(data: dict) -> str:
    """严格基于后台数据组装极简清单 Markdown 文章，往期推荐使用 Frontmatter recommendations 元数据"""
    import random
    date_str = data.get("date", datetime.date.today().strftime("%Y-%m-%d"))
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    month = dt.month
    day = dt.day

    items = data.get("items") or data.get("reminders") or []
    # 按照结束时间/剩余天数从小到大排序
    items = sorted(items, key=lambda x: (x.get("daysRemaining", 9999), x.get("name", "")))
    count = len(items)

    # 随机挑选 3 篇推荐文章（使用目标日期作为随机种子以保证同一天生成的幂等性）
    random.seed(int(dt.strftime("%Y%m%d")))
    selected_articles = random.sample(RECOMMENDED_ARTICLES_POOL, min(3, len(RECOMMENDED_ARTICLES_POOL)))

    lines = []
    lines.append("---")
    lines.append(f'title: "【每日提醒】{month}月{day}日全玩法倒计时与打卡清单"')
    lines.append(f'social_title: "{month}月{day}日全玩法打卡提醒"')
    lines.append(f'summary: "{month}月{day}日《弹壳特攻队》全量{count}大玩法倒计时与打卡提醒汇总。"')
    lines.append("tags:")
    lines.append("  - 弹壳特攻队")
    lines.append("  - 游戏攻略")
    lines.append("  - 每日提醒")
    lines.append('cover: "./cover.png"')
    lines.append('cover_vertical: "./cover_vertical.png"')
    lines.append('author: "弹壳呱呱"')
    lines.append(f"date: {date_str}")
    lines.append(f"lastmod: {date_str}")
    lines.append('qrcode_image: "img://弹壳呱呱微信公众号二维码"')
    lines.append("recommendations:")
    for article in selected_articles:
        lines.append(f'  - title: "{article["title"]}"')
        lines.append(f'    url: "{article.get("url", "")}"')
    lines.append("---")
    lines.append("")
    lines.append("![article-top](img://article-top){type=banner}")
    lines.append("")
    lines.append(f"# 🔔 {month} 月 {day} 日全玩法倒计时与打卡提醒")
    lines.append("")
    lines.append("各位特工大家早上好，我是呱呱！")
    lines.append("")
    lines.append(f"今天（{month} 月 {day} 日）游戏内各玩法的最新倒计时与打卡提醒如下：")
    lines.append("")

    for idx, item in enumerate(items, 1):
        name = item.get("name", "")
        status_text = item.get("statusText", "")
        note = item.get("digestNote")
        
        # 单行展示：序号 + 玩法名称 + 状态文案（备注）
        if note and note.strip():
            lines.append(f"{idx}. **{name}**：{status_text}（{note.strip()}）")
        else:
            lines.append(f"{idx}. **{name}**：{status_text}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("攻略创作不易，如果帮到了你，请大家多多**转发、点赞和关注**！你们的支持是呱呱持续输出干货的最大动力！")
    lines.append("")
    lines.append("【免责声明】本攻略纯属个人**经验分享**，**仅供参考**，不构成任何消费建议。游戏版本更新较快，具体数值以游戏内实际表现为准。本攻略所引用的美术图片及游戏内截图版权均归 Habby 公司所有。")
    lines.append("")

    return "\n".join(lines)


def auto_tag_file(file_path: Path):
    """自动调用 auto_tag.py 进行专有名词宏标签标注"""
    ws = find_workspace_root()
    auto_tag_script = ws / "skill" / "danke-strategy-skill" / "scripts" / "auto_tag.py"
    if auto_tag_script.exists():
        try:
            subprocess.run([sys.executable, str(auto_tag_script), str(file_path)], check=True)
        except Exception as e:
            print(f"⚠️ 自动宏标注跳过: {e}")


def generate_covers(out_dir: Path):
    """使用全特工专属底图与固定文案生成封面"""
    ws = find_workspace_root()
    make_cover_script = ws / ".agents" / "skills" / "wechat-cover-generator" / "scripts" / "make_cover.py"
    bg_img = ws / ".agents" / "skills" / "danke-daily-reminder-skill" / "assets" / "reminder_cover_bg.jpg"

    if make_cover_script.exists() and bg_img.exists():
        try:
            cmd = [
                sys.executable,
                str(make_cover_script),
                "-i", str(bg_img),
                "-t", "弹壳特攻队\n今日提醒",
                "-o", str(out_dir / "cover.png"),
                "--style", "horizontal",
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"🖼️ 专属封面已自动生成: {out_dir / 'cover.png'}")
        except Exception as e:
            print(f"⚠️ 封面生成异常: {e}")


def main():
    parser = argparse.ArgumentParser(description="自动生成《弹壳特攻队》每日玩法提醒文章")
    parser.add_argument("--date", help="指定生成日期 (YYYY-MM-DD)，默认为当天", default=datetime.date.today().strftime("%Y-%m-%d"))
    parser.add_argument("--api-base", help="danke-core API 地址", default="http://localhost:3000")
    parser.add_argument("--output-dir", help="自定义输出目录")

    args = parser.parse_args()
    target_date_str = args.date
    target_date_obj = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()

    print(f"📡 正在拉取 {target_date_str} 提醒规则数据...")
    digest_data = fetch_daily_digest(target_date_str, api_base=args.api_base)

    items = digest_data.get("items") or digest_data.get("reminders") or []
    total_rules = len(items)
    print(f"✅ 成功获取 {total_rules} 项生效规则（100% 严格使用后台配置文案）")

    article_content = build_reminder_article(digest_data)

    # 确定短格式输出目录：project/danke-creator/my-articles-md/提醒/YY.M.D/YY.M.D.md
    ws = find_workspace_root()
    short_date = to_short_date_str(target_date_obj)

    if args.output_dir:
        out_dir = Path(args.output_dir)
    else:
        out_dir = ws / "project" / "danke-creator" / "my-articles-md" / "提醒" / short_date

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{short_date}.md"

    out_file.write_text(article_content, encoding="utf-8")
    print(f"💾 文章已写入: {out_file}")

    # 自动生成专属封面
    generate_covers(out_dir)

    # 自动宏标注
    auto_tag_file(out_file)

    print(f"🎉 【{short_date} ({target_date_str}) 每日提醒极简打卡文章生成完毕】！")


if __name__ == "__main__":
    main()
