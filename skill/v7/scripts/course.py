# -*- coding: utf-8 -*-
"""课程表读取器：把 weeks.yaml 读成 dict，并推导每周的形态。

为什么自己写解析器：这是个给学生用的脚本，`pip install pyyaml` 本身就是一道门槛，
而且 Windows 上 pip 还经常被墙。weeks.yaml 的格式是本项目自己定的子集，
六十行足够，且出问题时能一眼看懂。

只支持这四种行：
    profiles:              区段标题
    weeks:                 区段标题
    - name: crypto         新记录（缩进 2 个空格的破折号）
      key: value           记录内的字段（缩进 4 个空格）
    # 注释
其它写法一律报错——宁可报错，也不要"看起来读进去了其实读错了"。
"""
import io
import os
import re

SECTION_RE = re.compile(r'^([a-z_]+):\s*$')
SCALAR_RE = re.compile(r'^([a-z_]+):\s*(\S.*)$')
ITEM_RE = re.compile(r'^  - \s*(?:([a-zA-Z_]+):\s*(.*))?$')
FIELD_RE = re.compile(r'^    ([a-zA-Z_]+):\s*(.*)$')


def load(path):
    if not os.path.exists(path):
        raise SystemExit('找不到课程表：%s' % path)
    out = {}
    section = None
    cur = None
    for no, raw in enumerate(io.open(path, encoding='utf-8'), 1):
        line = raw.rstrip('\n').rstrip()
        if not line or line.lstrip().startswith('#'):
            continue
        m = SECTION_RE.match(line)
        if m:
            section = m.group(1)
            out.setdefault(section, [])
            cur = None
            continue
        m = SCALAR_RE.match(line)
        if m and not line.startswith(' '):
            out[m.group(1)] = m.group(2).strip()
            continue
        m = ITEM_RE.match(line)
        if m:
            if section is None:
                raise SystemExit('weeks.yaml:%d 记录不在任何区段里' % no)
            cur = {}
            out[section].append(cur)
            if m.group(1):
                cur[m.group(1)] = m.group(2).strip()
            continue
        m = FIELD_RE.match(line)
        if m:
            if cur is None:
                raise SystemExit('weeks.yaml:%d 字段没有归属的记录' % no)
            cur[m.group(1)] = m.group(2).strip()
            continue
        raise SystemExit('weeks.yaml:%d 看不懂这一行：%r' % (no, line))
    return out


def _chapters(s):
    out = []
    for part in (s or '').split(','):
        part = part.strip()
        if not part:
            continue
        name, _, grade = part.partition('|')
        out.append({'name': name.strip(), 'grade': grade.strip()})
    return out


class Course(object):
    def __init__(self, base):
        self.base = base
        self.path = os.path.join(base, 'skill', 'v7', 'weeks.yaml')
        data = load(self.path)
        self.profiles = {}
        for p in data.get('profiles', []):
            name = p.get('name')
            if not name:
                raise SystemExit('profiles 里有一条没写 name')
            self.profiles[name] = {
                'algs': [x for x in p.get('algs', '').split(',') if x],
                'skeleton': [x for x in p.get('skeleton', '').split(',') if x],
                'logdir': p.get('logdir') or None,
                'source': p.get('source') or r'.',
                'unit': p.get('unit') or r'\d+',
                'strict': (p.get('strict', 'false').lower() == 'true'),
            }
        self.weeks = {}
        for w in data.get('weeks', []):
            n = int(w.get('week', '0'))
            self.weeks[n] = {
                'week': n,
                'theme': w.get('theme', ''),
                'experiment': w.get('experiment', 'none'),
                'chapters': _chapters(w.get('chapters')),
            }

    # ------------------------------------------------------------------ 推导

    def week(self, n):
        if n not in self.weeks:
            raise SystemExit('课程表里没有第 %d 周' % n)
        return self.weeks[n]

    def profile_of(self, n):
        """形态不是写在代码里的常量，是从章节构成推出来的。

        没有章节 → 报错；只有 Head First C → c-only；
        只有教材 → crypto（有实验）或 crypto（无实验，靠 logdir 空不空区分）；
        两边都有 → c-crypto。
        """
        ch = self.week(n)['chapters']
        if not ch:
            raise SystemExit('第 %d 周没有章节，课程表不完整' % n)
        has_c = any(c['name'].startswith('Head First C') for c in ch)
        has_p = any(c['name'].startswith('教材') for c in ch)
        if has_c and has_p:
            return 'c-crypto'
        if has_c:
            return 'c-only'
        return 'crypto'

    def cfg(self, n):
        """给 check.py 用的那份配置：形态参数 + 本周的分级要求。"""
        prof = self.profile_of(n)
        cfg = dict(self.profiles[prof])
        cfg['profile'] = prof
        w = self.week(n)
        cfg['week'] = n
        cfg['grades'] = {c['name']: c['grade'] for c in w['chapters'] if c['grade']}
        cfg['experiment'] = w['experiment']
        cfg['need_experiment'] = (w['experiment'] != 'none')
        if w['experiment'] == 'none':
            cfg['logdir'] = None
        return cfg

    def material_path(self, n):
        return os.path.join(self.base, 'skill', 'v7', 'material', 'w%02d.md' % n)

    def missing_material(self, n):
        """素材够不够。返回缺的东西列表，空列表 = 够了。

        为什么要有这一步：v6 的检查器分不出"写空了"和"没给素材"，
        人会白改一轮。素材不够时 generate 直接停下（退出码 2），不产半成品。
        """
        miss = []
        path = self.material_path(n)
        if not os.path.exists(path):
            miss.append('素材文件 %s' % os.path.relpath(path, self.base))
            return miss
        text = io.open(path, encoding='utf-8').read()
        for c in self.week(n)['chapters']:
            if c['name'] not in text:
                miss.append('素材里没有写「%s」' % c['name'])
        if self.week(n)['experiment'] != 'none':
            logdir = os.path.join(self.base, 'handmade', 'lab', 'logs')
            if not os.path.isdir(logdir) or not [x for x in os.listdir(logdir) if x.endswith('.log')]:
                miss.append('这周有实验，但 handmade/lab/logs 里没有日志')
        return miss


def open_course(base):
    return Course(base)