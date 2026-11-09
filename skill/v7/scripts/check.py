#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""密码系统设计-预习报告 验收器（v6）

用法：
    python skill/v6/scripts/check.py --report output/v6/generated.md --profile c-only
    python skill/v6/scripts/check.py --report X.md --json
    python skill/v6/scripts/check.py --coverage      # 规则表 vs 实现，缺了就报"未实现"
    python skill/v6/scripts/check.py --self-test     # 坏样本必须被抓住

退出码：0 无 FAIL（N/A 不算失败）；1 有 FAIL；2 用法或文件错误。

v6 与 v5 的差别只有一件事：**周的形状不再写死在代码里**。算法表、骨架概念、
日志目录、出处写法都从 PROFILES 里取；某一周根本没有这种东西时，
规则要报 N/A 并说清"本 profile 不要求"，而不是判 PASS（假装检查过）
或判 FAIL（冤枉作者）。

设计约束（来自 feedback/v4-to-v5.md）：
  V1 一条命令跑完，不用每轮重写；
  V2 --self-test 能证明它会失败，不是只会点头；
  V3 规则与函数一一对应，未实现的规则要明说；
  V4 FAIL 必须给 文件:行号，不给"第几项不合格"这种没法定位的话；
  V5 只用标准库；
  V6 规则编号从 skill.md 解析，不在这里硬编码。
"""
import argparse
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import course  # noqa: E402

try:  # Windows 控制台默认 cp936，中文提示会变乱码
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ---------------------------------------------------------------- 基础工具

CJK = re.compile(r'[\u4e00-\u9fff]')
FORBIDDEN_TOPICS = ['综上所述', '收获颇丰', '深入理解', '具有重要意义']
ALIAS = ['散列函数', '杂凑', '摘要函数', '非对称密码', '非对称加密', '块密码', '单钥',
         '报文鉴别码', '秘钥', '密匙', '混乱', '散布', '密钥集', '威胁模型', '混合体制']
ANALOGY = r'类似于|相当于|差不多|可以说就是|本质上就是'

# 算法名 -> 首现句必须包含的词（C16）
#
# v7 把 v6 的 ALG_CRYPTO / ALG_C / PROFILES 三张硬编码表**全删了**。
# 理由：那三张表正是 feedback/v6-to-v7.md 里说的"形态写在代码里"。
# 现在术语从 weeks.yaml 的 profiles 段读，规则只剩一条：
# 首现句里必须有数字 + 单位（`unit` 给正则）。

TOPICS = ['学习内容', 'AI 对学习内容的总结', '对 AI 总结的反思与补充', '学习思维导图',
          '基于 AI 的学习', '学习实践过程遇到的问题与解决方式', '作业提交要求']


def cjk_count(s):
    return len(CJK.findall(s))


def strip_notes(lines):
    """去掉审阅批注：`> [批注] …` 是写给人看的痕迹，不是报告正文。

    v4 的 C2 把批注也算进字数，同一份正文在 generated 里 1253 字、
    在 human-edited 里 1512 字——规则把审阅痕迹当成了内容。
    """
    return [l for l in lines if not l.strip().startswith('> [批注')]


def norm(s):
    """去掉空白与反引号，用于跨格式比较。"""
    return re.sub(r'[\s`]', '', s)


class Report(object):
    def __init__(self, text, path, base):
        self.text = text
        self.path = path
        self.base = base
        self.lines = text.splitlines()
        self.secs, self.sec_line = self._sections()
        self.appendix = self._appendix()

    def _sections(self):
        """按 `## ` 切节；遇到 `---` 就停（附录的 ### 不算节）。"""
        secs, line_of, cur, buf = {}, {}, None, []
        for i, l in enumerate(self.lines, 1):
            if l.startswith('## ') and not l.startswith('###'):
                if cur:
                    secs[cur] = buf
                cur, buf = l[3:].strip(), []
                line_of[cur] = i
            elif cur is not None:
                if l.strip() == '---':
                    secs[cur], cur, buf = buf, None, []
                    continue
                buf.append(l)
        if cur:
            secs[cur] = buf
        return secs, line_of

    def _appendix(self):
        out, cur, buf = {}, None, []
        for l in self.lines:
            m = re.match(r'### 附录 ([A-Z])', l)
            if m:
                if cur:
                    out[cur] = buf
                cur, buf = m.group(1), []
            elif cur is not None:
                buf.append(l)
        if cur:
            out[cur] = buf
        return out

    def body(self, name):
        return '\n'.join(strip_notes(self.secs.get(name, [])))

    def raw_body(self, name):
        return '\n'.join(self.secs.get(name, []))

    def line_of(self, needle, start=1):
        """返回 needle 第一次出现的行号（1 基），找不到给 0。"""
        for i, l in enumerate(self.lines, 1):
            if i >= start and needle in l:
                return i
        return 0

    def quote_lines(self):
        return [l for l in self.lines if l.strip().startswith('> AI 原话')]

    def no_quote_text(self):
        head = self.text.split('### 附录 A')[0]
        return '\n'.join(l for l in head.splitlines()
                         if not l.strip().startswith(('> AI 原话', '> [批注')))


class Ctx(object):
    def __init__(self, rep, cfg):
        self.rep = rep
        self.cfg = cfg
        self.week = cfg['week']
        self.profile = cfg['profile']
        self.algs = cfg['algs']
        self.skeleton = cfg['skeleton']
        self.grades = cfg['grades']
        self.source = re.compile(cfg['source'])
        self.s3 = rep.body('对 AI 总结的反思与补充')
        self.s2 = rep.body('AI 对学习内容的总结')
        self.problems = re.split(r'\*\*问题 \d+。\*\*', self.s3)[1:]
        self.quotes = [re.findall(r'"([^"\n]{4,200})"', p) for p in self.problems]
        self.mermaid = self._mermaid()

    def _mermaid(self):
        m = re.search(r'```mermaid\n(.*?)```', self.rep.text, re.S)
        if not m:
            return []
        return [l for l in m.group(1).splitlines() if l.strip()]


# ---------------------------------------------------------------- 规则实现

def c1_structure(c):
    got = [l[3:].strip() for l in c.rep.lines
           if l.startswith('## ') and not l.startswith('###')]
    if got != TOPICS:
        miss = [t for t in TOPICS if t not in got]
        extra = [g for g in got if g not in TOPICS]
        return False, '缺失 %s；多余 %s；共 %d 个' % (miss, extra, len(got)), 1
    return True, '7 节顺序一致', 0


def c2_length(c):
    bad, detail = [], []
    for name in TOPICS:
        body = c.rep.body(name)
        m = re.search(r'<!--\s*目标字数[:：]\s*([^>]*?)-->', body)
        if not m:
            bad.append('%s: 缺 <!-- 目标字数 --> 标记' % name)
            continue
        rng = re.search(r'(\d+)\s*[–—\-~]\s*(\d+)\s*(字|行)', m.group(1))
        if not rng:
            detail.append('%s=无硬区间' % name)
            continue
        lo, hi, unit = int(rng.group(1)), int(rng.group(2)), rng.group(3)
        clean = re.sub(r'<!--.*?-->', '', body, flags=re.S)
        if unit == '字':
            n = cjk_count(re.sub(r'```.*?```', '', clean, flags=re.S))
        else:
            n = len([l for l in clean.splitlines() if l.strip()])
        detail.append('%s=%d%s' % (name[:4], n, unit))
        if not lo <= n <= hi:
            bad.append('%s: %d%s 不在 %d–%d' % (name, n, unit, lo, hi))
    if bad:
        return False, '；'.join(bad), c.rep.line_of('目标字数')
    return True, ', '.join(detail), 0


def c3_depth(c):
    mm = c.mermaid
    if not mm:
        return False, '没有 mermaid 块', 0
    idx = next((i for i, l in enumerate(mm) if 'root(' in l), None)
    if idx is None:
        return False, '没有 root(...) 节点', 0
    i0 = len(mm[idx]) - len(mm[idx].lstrip())
    lv = [1 + (len(l) - len(l.lstrip()) - i0) // 2 for l in mm[idx:]]
    if max(lv) > 4:
        return False, '最大层级 %d（>4）' % max(lv), c.rep.line_of('root(')
    return True, '最大层级 %d' % max(lv), 0


def c4_nodes(c):
    mm = c.mermaid
    idx = next((i for i, l in enumerate(mm) if 'root(' in l), 0)
    bad_symbol = [l.strip() for l in mm[idx + 1:] if re.search(r'[/+()]', l.strip())]
    too_long = ['%s(%d字)' % (l.strip(), cjk_count(l)) for l in mm[idx:] if cjk_count(l) > 12]
    if bad_symbol or too_long:
        msg = []
        if bad_symbol:
            msg.append('含禁用符号 %s' % bad_symbol)
        if too_long:
            msg.append('超 12 字 %s' % too_long)
        return False, '；'.join(msg), c.rep.line_of('root(')
    return True, '%d 个节点' % (len(mm) - idx - 1), 0


def c5_cite(c):
    if len(c.problems) != 3:
        return False, '§3 问题数 %d（要求 3）' % len(c.problems), c.rep.line_of('## 对 AI 总结的反思与补充')
    miss = []
    for i, qs in enumerate(c.quotes, 1):
        if not qs:
            miss.append('问题%d 无引号原句' % i)
        elif not any(norm(q) in norm(c.s2) for q in qs):
            miss.append('问题%d 引句在 §2 找不到' % i)
    if miss:
        return False, '；'.join(miss), c.rep.line_of('## 对 AI 总结的反思与补充')
    return True, '3 条均命中 §2', 0


def c6_source(c):
    srcs = re.findall(r'来源：([^\n]+)', c.s3)
    bad = [s for s in srcs if not c.source.match(s.replace('`', '').strip())]
    if len(srcs) < 2:
        return False, '补充来源只有 %d 条（要求 ≥2）' % len(srcs), c.rep.line_of('来源：')
    if bad:
        return False, '来源不可核对 %s' % bad[:2], c.rep.line_of('来源：')
    return True, '%d 条来源可核对' % len(srcs), 0


def c7_dialog(c):
    tables = re.findall(r'\| 轮次 \| 谁 \| 内容 \|\n\|[-: |]+\|\n((?:\|.*\n)+)', c.rep.text)
    rows = [t.count('\n') for t in tables]
    if len(tables) < 2:
        return False, '对话表只有 %d 张（要求 2）' % len(tables), c.rep.line_of('| 轮次 |')
    if min(rows) < 8:
        return False, '最少一张只有 %d 行（要求 ≥8）' % min(rows), c.rep.line_of('| 轮次 |')
    n = c.rep.text.count('我答不上来')
    if n < 2:
        return False, '"我答不上来"只出现 %d 次（要求 ≥2）' % n, c.rep.line_of('我答不上来')
    return True, '表格 %d 张，行数 %s' % (len(tables), rows), 0


def c8_eval(c):
    evals = re.findall(r'\| \d+ \| AI \| ([^|]*评价[^|]*)\|', c.rep.text)
    if len(evals) < 2:
        return False, '带"评价"的 AI 行只有 %d 条' % len(evals), c.rep.line_of('评价')
    bad = []
    for e in evals:
        if not re.search(r'第 ?\d+ ?轮', e):
            bad.append('无"第 N 轮"')
        elif not re.search(r'补|对照|复习|重看|再跑|重做', e):
            bad.append('无下一步动作')
        elif re.search(r'继续加油|理解得不错|基本正确|可以再深入|很好', e):
            bad.append('含套话')
    if bad:
        return False, '评价缺成分：%s' % bad, c.rep.line_of('评价')
    return True, '%d 条评价三成分齐全' % len(evals), 0


def c9_cmd(c):
    blocks = re.findall(r'### 问题 \d：.*?\*\*排查\*\*\n(.*?)\*\*解决\*\*', c.rep.text, re.S)
    if len(blocks) < 2:
        return False, '§6 带四段式的问题只有 %d 个' % len(blocks), c.rep.line_of('**排查**')
    cmds = [len(re.findall(r'^\$ ', b, re.M)) for b in blocks]
    if min(cmds) < 2:
        return False, '排查段命令数 %s（每个问题要求 ≥2）' % cmds, c.rep.line_of('**排查**')
    return True, '命令数 %s' % cmds, 0


def c10a_shape(c):
    """现象段的结构：有代码块、代码块里有命令行或输出。"""
    blocks = re.findall(r'\*\*现象\*\*\n\n(.*?)\n\n\*\*排查\*\*', c.rep.text, re.S)
    if not blocks:
        return None, 'N/A：本周没有"现象"段（无实验）', 0
    empty = [i + 1 for i, b in enumerate(blocks) if not re.search(r'```', b)]
    if empty:
        return False, '第 %s 个现象段没有代码块' % empty, c.rep.line_of('**现象**')
    return True, '%d 段现象结构完整' % len(blocks), 0


def c10b_paste(c, logs=None):
    """现象段的每一行必须能在真实日志里原文命中（不许转述）。"""
    if not c.cfg['need_experiment']:
        return None, 'N/A：本 profile 无终端实验（logdir=None）', 0
    logs = logs if logs is not None else load_logs(c.rep.base)
    blocks = re.findall(r'\*\*现象\*\*\n\n(.*?)\n\n\*\*排查\*\*', c.rep.text, re.S)
    if not blocks:
        return False, '有实验要求但没有"现象"段', c.rep.line_of('**现象**')
    notfound = []
    for b in blocks:
        for code in re.findall(r'```.*?\n(.*?)```', b, re.S):
            for l in code.splitlines():
                s = l.strip()
                if s and s != '...' and not any(s in v for v in logs.values()):
                    notfound.append(s[:50])
    if notfound:
        return False, '这些行在日志里找不到（可能是转述）%s' % notfound, c.rep.line_of('**现象**')
    return True, '%d 段现象均能在日志中原文命中' % len(blocks), 0


def c11a_range(c):
    if not c.cfg['logdir']:
        return None, 'N/A：无终端实验，附录 A 不含日志行号', 0
    app = '\n'.join(c.rep.appendix.get('A', []))
    bad = []
    for m in re.finditer(r'`(handmade/lab/logs/[^`:]+):(\d+)(?:-(\d+))?`', app):
        fn, a, b = m.group(1), int(m.group(2)), m.group(3)
        path = os.path.join(c.rep.base, fn.replace('/', os.sep))
        if not os.path.exists(path):
            bad.append('%s 不存在' % fn)
            continue
        n = sum(1 for _ in io.open(path, encoding='utf-8'))
        if a > n or (b and int(b) > n):
            bad.append('%s:%s 超出 %d 行' % (fn, a, n))
    if bad:
        return False, '；'.join(bad), c.rep.line_of('### 附录 A')
    return True, '行号均在文件范围内', 0


def c11b_keyword(c):
    if not c.cfg['logdir']:
        return None, 'N/A：无终端实验，附录 A 不含日志行号', 0
    app = '\n'.join(c.rep.appendix.get('A', []))
    bad, hit = [], 0
    for row in app.splitlines():
        m = re.search(r'^\| (.+?) \| [^|]+ \| `(handmade/lab/logs/[^`:]+):(\d+)', row)
        if not m:
            continue
        kw, fn, a = m.group(1), m.group(2), int(m.group(3))
        path = os.path.join(c.rep.base, fn.replace('/', os.sep))
        if not os.path.exists(path):
            continue
        src = io.open(path, encoding='utf-8').read().splitlines()
        window = norm('\n'.join(src[max(0, a - 3):a + 2]))
        cands = re.findall(r'`([^`]+)`', kw) or [kw]
        for cand in cands:
            cc = re.sub(r'^[./]+', '', norm(cand))
            if len(cc) >= 4 and cc[:12] in window:
                hit += 1
                break
        else:
            bad.append('%s:%s 附近找不到「%s」' % (fn, a, kw[:24]))
    if bad:
        return False, '；'.join(bad[:3]), c.rep.line_of('### 附录 A')
    return True, '命中 %d 条' % hit, 0


def c12_cliche(c):
    body = re.sub(r'```.*?```', '', c.rep.text, flags=re.S)
    found = [w for w in FORBIDDEN_TOPICS if w in body]
    if found:
        return False, '套话 %s' % found, c.rep.line_of(found[0])
    return True, '无套话', 0


def c13_table(c):
    rows = [r for r in c.rep.appendix.get('C', [])
            if r.startswith('| ') and not r.startswith('|:')]
    if len(rows) < 11:
        return False, '术语表 %d 行（含表头，要求 ≥11）' % len(rows), c.rep.line_of('### 附录 C')
    bad_col, bad_src = [], []
    for r in rows[2:]:
        cells = [x.strip() for x in r.strip().strip('|').split('|')]
        if len(cells) != 4 or not cells[2] or not cells[3]:
            bad_col.append(r[:30])
        elif not c.source.search(cells[3]):
            bad_src.append(cells[3][:24])
    if bad_col or bad_src:
        return False, '列不全 %s；出处不合法 %s' % (bad_col[:2], bad_src[:2]), c.rep.line_of('### 附录 C')
    return True, '%d 行，出处全部合法' % len(rows), 0


def c14_unique(c):
    body = c.rep.no_quote_text()
    hits = {a: body.count(a) for a in ALIAS if body.count(a)}
    n = len(re.findall(r'(?<!消息)认证码', body))
    if n:
        hits['认证码(单独使用)'] = n
    if hits:
        return False, '别名命中 %s' % hits, 1
    return True, '无别名', 0


def c15_analogy(c):
    bad = []
    for i, l in enumerate(c.rep.lines, 1):
        if l.strip().startswith(('> AI 原话', '> [批注')):
            continue
        if re.search(ANALOGY, l) and re.search(r'是.*的(算法|机制|函数|方案|密码)', l):
            bad.append('第 %d 行: %s' % (i, l.strip()[:30]))
    if bad:
        return False, '；'.join(bad[:2]), 1
    return True, '无类比定义', 0


def c16_numbers(c):
    s2 = c.s2
    present = [n for n in c.algs if n in s2]
    if not present:
        return None, 'N/A：第 %d 周没有任何需要报尺寸的术语' % c.week, 0
    bad, absent = [], [n for n in c.algs if n not in s2]
    for name in present:
        idx = s2.find(name)
        start = max(s2.rfind('。', 0, idx), s2.rfind('\n', 0, idx), s2.rfind('；', 0, idx)) + 1
        end = s2.find('。', idx)
        sent = s2[start:end if end > 0 else len(s2)]
        if not re.search(c.cfg['unit'], sent):
            bad.append('%s 首现句没有数字+单位：%s' % (name, sent.strip()[:24]))
    if bad:
        return False, '；'.join(bad), 1
    if absent and c.cfg['strict']:
        return False, '本周要求但未出现：%s' % absent, 1
    note = '' if not absent else '；未出现（本周不强制）%s' % absent
    return True, '%d 个术语首现处数值齐全%s' % (len(present), note), 0


def c17_skeleton(c):
    if not c.skeleton:
        return None, 'N/A：本 profile 无骨架概念要求', 0
    app = '\n'.join(c.rep.appendix.get('C', []))
    miss = [w for w in c.skeleton if w not in app]
    if miss:
        return False, '术语表缺骨架概念 %s' % miss, c.rep.line_of('### 附录 C')
    return True, '骨架概念齐全', 0


def c19_grade(c):
    """章节分级：重点章 ≥400 字、了解章 150–250、参考章 ≤150。

    v7 与 v6 的差别：要不要分级、每章是哪一档，**不再从报告里读**，
    而是从 weeks.yaml 的 `章节分级` 拿。报告只负责把标记写对。
    这样"报告说自己是重点"和"课程表说它是了解"这种矛盾会被直接抓住。
    """
    if not c.grades:
        return None, 'N/A：第 %d 周课程表里没有分级要求' % c.week, 0
    s2 = c.s2
    marks = [(m.start(), m.group(1)) for m in re.finditer(r'<!--\s*分级[:：]\s*(\S+?)\s*-->', s2)]
    if not marks:
        return False, '课程表要求分级（%s），但 §2 一个分级标记都没有' % (
            '/'.join('%s=%s' % (k, v) for k, v in c.grades.items())), \
            c.rep.line_of('## AI 对学习内容的总结')
    LIM = {'重点': (400, 10 ** 6), '了解': (150, 250), '参考': (0, 150)}
    want = list(c.grades.values())
    got = [lvl for _, lvl in marks]
    if got != want:
        return False, '分级顺序与课程表不符：报告 %s，课程表 %s' % (got, want), c.rep.line_of('分级')
    bad, detail = [], []
    for i, (pos, lvl) in enumerate(marks):
        endp = marks[i + 1][0] if i + 1 < len(marks) else len(s2)
        n = cjk_count(re.sub(r'<!--.*?-->', '', s2[pos:endp], flags=re.S))
        detail.append('%s=%d' % (lvl, n))
        lo, hi = LIM.get(lvl, (0, 10 ** 6))
        if not lo <= n <= hi:
            bad.append('%s 章 %d 字（应在 %d–%s）' % (lvl, n, lo, hi if hi < 10 ** 6 else '∞'))
    if bad:
        return False, '；'.join(bad), c.rep.line_of('分级')
    return True, '分级字数 %s' % ', '.join(detail), 0


def c18_quote_only(c):
    bad = []
    for qs in c.quotes:
        for q in qs:
            q = q.strip()
            if not q:
                continue
            cnt = sum(1 for l in c.s2.splitlines()
                      if q in l and not l.strip().startswith('> AI 原话'))
            if cnt:
                bad.append(q[:30])
    if bad:
        return False, '被否定的原句仍以正常正文出现 %s' % bad, 1
    return True, '错句仅以引用块形式存在', 0


RULES = [('C1', c1_structure), ('C2', c2_length), ('C3', c3_depth), ('C4', c4_nodes),
         ('C5', c5_cite), ('C6', c6_source), ('C7', c7_dialog), ('C8', c8_eval),
         ('C9', c9_cmd), ('C10a', c10a_shape), ('C10b', c10b_paste),
         ('C11a', c11a_range), ('C11b', c11b_keyword),
         ('C12', c12_cliche), ('C13', c13_table), ('C14', c14_unique), ('C15', c15_analogy),
         ('C16', c16_numbers), ('C17', c17_skeleton), ('C18', c18_quote_only),
         ('C19', c19_grade)]


def load_logs(base):
    d = os.path.join(base, 'handmade', 'lab', 'logs')
    out = {}
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith('.log'):
                out[f] = io.open(os.path.join(d, f), encoding='utf-8').read()
    return out


def run(text, path, base, cfg):
    rep = Report(text, path, base)
    ctx = Ctx(rep, cfg)
    results = []
    for rid, fn in RULES:
        try:
            ok, msg, line = fn(ctx)
        except Exception as e:  # 规则自身崩了，要暴露而不是静默 PASS
            ok, msg, line = False, '规则抛异常: %r' % e, 0
        status = 'na' if ok is None else ('pass' if ok else 'fail')
        results.append({'id': rid, 'status': status, 'ok': ok is True, 'msg': msg,
                        'where': '%s:%d' % (os.path.basename(path), line) if line else ''})
    return results


# ---------------------------------------------------------------- 自测

def mutate(text, kind):
    if kind == 'structure':          # 删掉一个一级标题
        return text.replace('## 作业提交要求', '## 提交要求', 1)
    if kind == 'terms':              # 同概念改用别名
        return text.replace('消息认证码', '认证码')
    if kind == 'citation':           # 把一处行号改成不存在的
        return re.sub(r'(handmade/lab/logs/0[1-9][^`]*\.log):17', r'\1:9999', text)
    if kind == 'grade':              # 分级标记改错档：重点章变了解（字数超上限）
        return re.sub(r'<!-- 分级: 重点 -->', '<!-- 分级: 了解 -->', text, count=1)
    raise ValueError(kind)


# 每周的自测样本：v7 要求"12 周各有一个"，目前实到 3 个（第 1、4、9 周）
SAMPLES = {1: 'output/v7/generated.md',
           9: 'output/v7/w09.md'}
# 哪些变异样本适用于哪一周（c-only 没有术语别名、没有日志行号）
EXPECT = {1: ['structure', 'terms', 'citation', 'grade'],
          9: ['structure']}
# 第 4 周没有真报告（我没有教材第 14 章的原文，硬写就会编造出处），
# 只留一份"分级夹具"：正文是占位文字，唯一要求是 C19 能认对三档。
FIXTURES = {4: 'skill/v7/fixtures/w04-graded.md'}
RULE_OF = {'structure': 'C1', 'terms': 'C14', 'citation': 'C11a', 'grade': 'C19'}


def self_test(base, weeks=None):
    c = course.Course(base)
    weeks = weeks or sorted(w for w in SAMPLES
                            if os.path.exists(os.path.join(base, SAMPLES[w])))
    if not weeks:
        print('自测失败：一个样本都找不到')
        return 1
    fails = 0
    for w in weeks:
        path = os.path.join(base, SAMPLES[w])
        text = io.open(path, encoding='utf-8').read()
        cfg = c.cfg(w)
        res = run(text, path, base, cfg)
        bads = [r for r in res if r['status'] == 'fail']
        na = {r['id'] for r in res if r['status'] == 'na'}
        print('[自测] 第 %d 周（%s）好样本必须无 FAIL: %s（N/A %d 项）'
              % (w, cfg['profile'], 'PASS' if not bads else 'FAIL', len(na)))
        if bads:
            fails += 1
            for r in bads:
                print('        %s %s' % (r['id'], r['msg']))
        for kind in EXPECT.get(w, ['structure']):
            rid = RULE_OF[kind]
            if rid in na:
                print('[自测]   变异 %-9s 跳过：%s 在本周是 N/A' % (kind, rid))
                continue
            res = run(mutate(text, kind), path, base, cfg)
            caught = [r['id'] for r in res if r['status'] == 'fail']
            hit = rid in caught
            print('[自测]   变异 %-9s 必须被 %-5s 抓住: %s (实际 %s)'
                  % (kind, rid, 'PASS' if hit else 'FAIL', caught))
            if not hit:
                fails += 1

    for w, rel in sorted(FIXTURES.items()):
        path = os.path.join(base, rel)
        if not os.path.exists(path):
            print('[自测] 第 %d 周夹具缺失：%s' % (w, rel))
            fails += 1
            continue
        text = io.open(path, encoding='utf-8').read()
        cfg = c.cfg(w)
        res = run(text, path, base, cfg)
        one = [r for r in res if r['id'] == 'C19'][0]
        print('[自测] 第 %d 周分级夹具（%s）C19 必须 PASS: %s %s'
              % (w, cfg['profile'], 'PASS' if one['status'] == 'pass' else 'FAIL', one['msg']))
        if one['status'] != 'pass':
            fails += 1
        res2 = run(mutate(text, 'grade'), path, base, cfg)
        caught = [r['id'] for r in res2 if r['status'] == 'fail']
        ok = 'C19' in caught
        print('[自测]   变异 grade     必须被 C19 抓住: %s (实际 %s)'
              % ('PASS' if ok else 'FAIL', caught))
        if not ok:
            fails += 1

    print()
    print('自测结论：%s' % ('全部通过' if not fails else '%d 项失败' % fails))
    return 0 if not fails else 1


# ---------------------------------------------------------------- 覆盖率

def coverage(base):
    skill = os.path.join(base, 'skill', 'v7', 'skill.md')
    ids = []
    if os.path.exists(skill):
        for l in io.open(skill, encoding='utf-8'):
            m = re.match(r'\|\s*(C\d+[ab]?)\s*\|', l)
            if m:
                ids.append(m.group(1))
    seen, uniq = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    ids = uniq
    impl = [rid for rid, _ in RULES]
    missing = [i for i in ids if i not in impl]
    extra = [i for i in impl if i not in ids]
    print('skill.md 声明 %d 条，已实现 %d 条' % (len(ids), len(impl)))
    if missing:
        print('未实现：%s' % missing)
    if extra:
        print('脚本里有、skill.md 没声明：%s' % extra)
    if not missing and not extra:
        print('一字不差，规则表与实现一一对应')
    return 0 if not missing else 1


# ---------------------------------------------------------------- 入口

def main(argv=None):
    ap = argparse.ArgumentParser(description='预习报告验收器 v7（按周次取形态）')
    ap.add_argument('--report')
    ap.add_argument('--week', type=int, help='第几周；形态从 weeks.yaml 推')
    ap.add_argument('--base', default=os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--coverage', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    a = ap.parse_args(argv)

    c = course.Course(a.base)

    if a.coverage:
        return coverage(a.base)
    if a.self_test:
        return self_test(a.base)
    if not a.report or not a.week:
        ap.print_help()
        print('\n必须同时给 --week：形态、分级、术语都从 weeks.yaml 按周次取。')
        return 2
    if not os.path.exists(a.report):
        print('找不到报告：%s' % a.report)
        return 2

    cfg = c.cfg(a.week)
    text = io.open(a.report, encoding='utf-8').read()
    res = run(text, a.report, a.base, cfg)
    fails = [r for r in res if r['status'] == 'fail']
    nas = [r for r in res if r['status'] == 'na']

    if a.json:
        print(json.dumps({'report': a.report, 'week': a.week, 'profile': cfg['profile'],
                          'results': res, 'pass': not fails, 'na': len(nas)},
                         ensure_ascii=False, indent=1))
    elif not a.quiet:
        flag_of = {'pass': 'PASS', 'fail': 'FAIL', 'na': 'N/A '}
        for r in res:
            print('%s  %-5s %-14s %s' % (flag_of[r['status']], r['id'], r['where'], r['msg']))
        print()
        print('%d 项（第 %d 周，形态 %s），失败 %d 项，不适用 %d 项%s'
              % (len(res), a.week, cfg['profile'], len(fails), len(nas),
                 '：' + ','.join(r['id'] for r in fails) if fails else ''))
    return 0 if not fails else 1


if __name__ == '__main__':
    sys.exit(main())
