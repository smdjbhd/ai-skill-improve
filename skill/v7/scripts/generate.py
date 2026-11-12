# -*- coding: utf-8 -*-
"""generate.py —— 按课程表生成一周报告的骨架。

它**不写正文**。原因写在 skill/v7/skill.md 里：正文必须由模型读素材后写，
脚本只负责两件模型最容易漏的事——
  1. 把这一周的"形状"摆对：7 节、每节的目标字数、每章的分级标记、附录 B 的输入卡片；
  2. 素材不够时**立刻停下**，退出码 2，把缺的逐条列出来，不许产半成品。

用法：
    python skill/v7/scripts/generate.py --week 1                 # 打到 stdout
    python skill/v7/scripts/generate.py --week 1 --out out.md
    python skill/v7/scripts/generate.py --all --dir tmp/scaffold  # 12 周回归
退出码：0 生成成功；2 素材不足；1 课程表本身有问题。
"""
import argparse
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import course  # noqa: E402

WEEK_CHARS = {'重点': '≥400 字', '了解': '150–250 字', '参考': '≤150 字'}

# 节名必须与 check.py 的 TOPICS 逐字一致：带"一、二、"的标题会让 C1 判成"多余章节"
SECTIONS = [
    ('学习内容', '8–15 行', '读完后用自己的话讲一遍这周讲了什么，不复制教材目录'),
    ('AI 对学习内容的总结', '900–1300 字', '把素材交给 AI，让它总结；这一节保留 AI 的原话，包括错的地方'),
    ('对 AI 总结的反思与补充', '300–900 字', '逐条挑 §2 的错与漏，引用原句再更正；至少 2 条补充要有出处'),
    ('学习思维导图', '8–20 行', '一个 mermaid mindmap 块，节点 ≤12 字，层级 ≤4'),
    ('基于 AI 的学习', '300–1500 字', '至少 2 个概念，每个概念一张对话表（≥8 轮）'),
    ('学习实践过程遇到的问题与解决方式', '300–1500 字', '至少 2 个真实卡住过的问题，现象/排查/解决三段'),
    ('作业提交要求', '20–400 字', '文件名、PDF、仓库链接三件事'),
]


def scaffold(cfg):
    """只产骨架：每个 `##` 节名来自 SECTIONS，正文留给人和素材。"""
    w = cfg['week']
    lines = []
    add = lines.append
    add('<!-- 本文件由 skill/v7/scripts/generate.py 生成骨架，正文需按 skill/v7/skill.md 填写 -->')
    add('')
    for i, (name, target, hint) in enumerate(SECTIONS):
        add('## %s' % name)
        add('<!-- 目标字数: %s -->' % target)
        add('')
        if name == '学习内容':
            add('> TODO：本周主题「%s」。%s' % (cfg.get('theme', ''), hint))
            add('')
        elif name == 'AI 对学习内容的总结':
            for ch in cfg['chapters']:
                grade = ch['grade'] or '重点'
                add('<!-- 分级: %s -->' % grade)
                add('### %s' % ch['name'])
                add('')
                add('> TODO：按素材写这一章（%s）。' % WEEK_CHARS.get(grade, ''))
                add('')
        elif name == '对 AI 总结的反思与补充':
            add('> TODO：**问题 1。** AI 原话"……"——更正：……')
            add('')
        elif name == '学习思维导图':
            add('```mermaid')
            add('mindmap')
            add('  root((第 %d 周))' % w)
            add('    待填')
            add('```')
            add('')
        elif name == '基于 AI 的学习':
            add('### 概念一：')
            add('')
            add('| 轮次 | 谁 | 内容 |')
            add('|---|---|---|')
            add('| 1 | 我 | |')
            add('')
        elif name == '学习实践过程遇到的问题与解决方式':
            add('### 问题 1：')
            add('')
            add('**现象**')
            add('')
            add('```text')
            add('')
            add('```')
            add('')
            add('**排查**')
            add('')
            add('```text')
            add('$ ')
            add('```')
            add('')
            add('**解决**')
            add('')
        elif name == '作业提交要求':
            add('> TODO：20241409 司马平珏《密码系统设计》第 %d 周.md / .pdf + 仓库链接' % w)
            add('')
    add('---')
    add('')
    add('### 附录 A：真实性对照表')
    add('')
    add('| 我写的内容 | 类型 | 来源 |')
    add('|---|---|---|')
    add('')
    add('### 附录 B：输入卡片')
    add('')
    add('```yaml')
    add('周次: %d' % w)
    add('主题: %s' % cfg.get('theme', ''))
    add('周形态: %s' % cfg.get('profile', ''))
    add('章节分级: %s' % '/'.join('%s=%s' % (c['name'], c['grade'] or '重点') for c in cfg['chapters']))
    add('实验: %s' % cfg.get('experiment', 'none'))
    add('真实日志: %s' % ('无' if not cfg.get('logdir') else cfg.get('logdir')))
    add('素材: %s' % cfg.get('material', ''))
    add('```')
    add('')
    return '\n'.join(lines) + '\n'


def build(c, week):
    cfg = c.cfg(week)
    cfg['base'] = c.base
    cfg['chapters'] = c.week(week)['chapters']
    cfg['theme'] = c.week(week)['theme']
    miss = c.missing_material(week)
    if miss:
        sys.stderr.write('第 %d 周素材不足，不生成（退出码 2）：\n' % week)
        for m in miss:
            sys.stderr.write('  - %s\n' % m)
        return None
    return scaffold(cfg)


def main(argv=None):
    ap = argparse.ArgumentParser(description='按课程表生成周报告骨架 v7')
    ap.add_argument('--week', type=int)
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--out')
    ap.add_argument('--dir')
    ap.add_argument('--base', default=os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    a = ap.parse_args(argv)

    if bool(a.week) == bool(a.all):
        ap.print_help()
        return 1

    c = course.Course(a.base)

    if a.week:
        text = build(c, a.week)
        if text is None:
            return 2
        if a.out:
            d = os.path.dirname(os.path.abspath(a.out))
            if d and not os.path.isdir(d):
                os.makedirs(d)
            io.open(a.out, 'w', encoding='utf-8', newline='\n').write(text + '\n')
            print('已写出 %s（%d 行）' % (a.out, text.count('\n') + 1))
        else:
            print(text)
        return 0

    # --all：12 周回归。缺素材的周**必须**失败，这是设计目标，不是意外。
    bad = 0
    ok = 0
    for n in sorted(c.weeks):
        text = build(c, n)
        if text is None:
            bad += 1
            continue
        ok += 1
        if a.dir:
            if not os.path.isdir(a.dir):
                os.makedirs(a.dir)
            io.open(os.path.join(a.dir, 'w%02d.md' % n), 'w',
                    encoding='utf-8', newline='\n').write(text + '\n')
    print()
    print('12 周回归：能生成 %d 周，素材不足 %d 周' % (ok, bad))
    return 0


if __name__ == '__main__':
    sys.exit(main())