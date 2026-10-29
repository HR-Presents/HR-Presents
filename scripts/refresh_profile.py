#!/usr/bin/env python3
"""Refresh public GitHub facts and shared card data. Python standard library only."""
import argparse
import datetime as dt
import html
import json
import os
import re
import urllib.error
import urllib.request
from urllib.parse import quote
from pathlib import Path

ACCOUNT = os.environ.get('PROFILE_ACCOUNT', os.environ.get('GITHUB_REPOSITORY', 'HR-Presents/HR-Presents').split('/')[0])
ROOT = Path('.')
OUT = ROOT / 'assets/dynamic'
NOW = dt.datetime.now(dt.timezone.utc)
STAMP = NOW.strftime('%Y-%m-%d %H:%M UTC')
THEMES = {'HR-Presents': ('172126', 'A8CDB9', 'A3C9DA', 'CDD5D4'), 'HaziqBinAfzal': ('0B1220', '63B3FF', '60A5FA', 'CBD5E1'), 'ruveeha33': ('131426', 'C084FC', '22D3EE', 'C7C2D8')}
BG, ACCENT, SECOND, TEXT = THEMES[ACCOUNT]

def request(url, payload=None):
    headers = {'User-Agent': 'HR-Presents-profile-refresh', 'Accept': 'application/vnd.github+json'}
    if url.startswith('https://api.github.com/') and os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    data = None if payload is None else json.dumps(payload).encode()
    if data:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode()

def api(path):
    return json.loads(request('https://api.github.com' + path))

def pages(path):
    result = []
    for page in range(1, 21):
        rows = api(path + ('&' if '?' in path else '?') + f'per_page=100&page={page}')
        result.extend(rows)
        if len(rows) < 100:
            return result
    raise RuntimeError('Repository pagination exceeded configured limit')

def contributions():
    query = 'query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'
    try:
        result = json.loads(request('https://api.github.com/graphql', {'query': query, 'variables': {'login': ACCOUNT}}))
        calendar = result['data']['user']['contributionsCollection']['contributionCalendar']
        daily = [{'date': d['date'], 'count': d['contributionCount']} for w in calendar['weeks'] for d in w['contributionDays']]
        return {'total': calendar['totalContributions'], 'daily': daily, 'source': 'GitHub GraphQL contributionCalendar'}
    except (KeyError, TypeError, urllib.error.HTTPError):
        # Public HTML fallback needs no private-user scope and retains exact displayed counts.
        from html.parser import HTMLParser
        class Calendar(HTMLParser):
            def __init__(self):
                super().__init__(); self.cells = {}; self.labels = {}; self.target = None
            def handle_starttag(self, tag, attrs):
                a = dict(attrs)
                if a.get('data-date') and a.get('id'):
                    self.cells[a['id']] = a['data-date']
                if tag == 'tool-tip':
                    self.target = a.get('for'); self.labels.setdefault(self.target, '')
            def handle_data(self, data):
                if self.target:
                    self.labels[self.target] += data
            def handle_endtag(self, tag):
                if tag == 'tool-tip': self.target = None
        parser = Calendar()
        parser.feed(request(f'https://github.com/users/{ACCOUNT}/contributions'))
        daily = []
        for key, date in parser.cells.items():
            label = parser.labels.get(key, '').strip()
            match = re.match(r'([\d,]+) contribution', label)
            if label.startswith('No contributions'):
                count = 0
            elif match:
                count = int(match[1].replace(',', ''))
            else:
                raise RuntimeError('Contribution calendar count could not be parsed')
            daily.append({'date': date, 'count': count})
        if len(daily) < 300:
            raise RuntimeError('Contribution calendar incomplete; retaining previous generated assets')
        daily.sort(key=lambda x: x['date'])
        return {'total': sum(d['count'] for d in daily), 'daily': daily, 'source': 'GitHub public contribution calendar'}

def esc(value): return html.escape(str(value), quote=True)
def text(x, y, value, size=18, color=None, bold=False):
    return f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" fill="#{color or TEXT}"' + (' font-weight="700"' if bold else '') + f'>{esc(value)}</text>'
def svg(title, body, height):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}"><title>{esc(title)}</title><rect width="1200" height="{height}" rx="14" fill="#{BG}"/>{body}</svg>\n'
def save(name, content):
    path = OUT / name; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
def stat_card(data):
    cells = [(data['contributions']['total'], 'Contributions / rolling year'), (len(data['repos']), 'Public repositories'), (sum(r['stargazers_count'] for r in data['repos']), 'Stars / public repositories'), (sum(r['forks_count'] for r in data['repos']), 'Forks / public repositories'), (data['profile']['followers'], 'Followers'), (data['profile']['following'], 'Following')]
    body = text(28, 42, ACCOUNT + ' / GitHub statistics', 28, ACCENT, True) + text(28, 72, 'Automatically refreshed / ' + STAMP, 16)
    for i, (value, label) in enumerate(cells):
        x = 28 + i % 3 * 385; y = 94 + i // 3 * 107
        body += f'<rect x="{x}" y="{y}" width="369" height="93" rx="9" fill="#ffffff" fill-opacity=".055"/>' + text(x+18, y+42, value, 34, ACCENT, True) + text(x+18, y+73, label, 16)
    return svg('Automatically refreshed public statistics for ' + ACCOUNT, body, 318)


def calendar_card(data):
    import math
    months = {}
    for day in data['contributions']['daily']:
        key = day['date'][:7]
        months[key] = months.get(key, 0) + day['count']
    rows = sorted(months.items())
    maximum = max([v for _,v in rows] or [0])
    step = max(1, math.ceil(maximum / 4)); ceiling = step * 4
    body = text(28, 40, ACCOUNT + ' / development graph', 26, ACCENT, True)
    body += text(28, 70, 'Monthly GitHub contributions / rolling-year window / refreshed '+STAMP, 15)
    for i in range(5):
        y = 256-i*39
        body += f'<path d="M70 {y}H1160" stroke="#{TEXT}" stroke-opacity=".15"/>' + text(20,y+5,i*step,12,TEXT)
    points=[]
    for i,(month,count) in enumerate(rows):
        x = 88+i*1052/max(1,len(rows)-1); y = 256-count/ceiling*156
        points.append((x,y))
        label=dt.datetime.strptime(month,'%Y-%m').strftime('%b %y')
        body += text(x-18,279,label,11,TEXT)
    if points:
        path=' '.join(f'{x},{y}' for x,y in points)
        area=f'{points[0][0]},256 '+path+f' {points[-1][0]},256'
        body += f'<polygon points="{area}" fill="#{ACCENT}" fill-opacity=".10"/><polyline points="{path}" fill="none" stroke="#{ACCENT}" stroke-width="3"/>'
        for (x,y),(month,count) in zip(points,rows):
            body += f'<circle cx="{x}" cy="{y}" r="4" fill="#{SECOND}"><title>{month}: {count} contributions</title></circle>'
    body += text(28,315,'First and current months may be partial. GitHub activity counts are not a quality or proficiency score.',13,TEXT)
    return svg(ACCOUNT+' automatically refreshed monthly development graph',body,340)

def languages_card(data):
    languages = data['languages']; total = sum(languages.values())
    rows = sorted(languages.items(), key=lambda x: -x[1]); main = rows[:5]
    if len(rows) > 5: main.append(('Other', sum(v for _, v in rows[5:])))
    body = text(28, 40, ACCOUNT + ' / public code languages', 26, SECOND, True) + text(28, 70, 'Byte-weighted GitHub language data / public, non-fork repositories / ' + STAMP, 15)
    shades = [ACCENT, SECOND, 'D6BE92', 'C5BFDF', '88A2B6', '919B99']; x = 28
    for i, (name, value) in enumerate(main):
        width = value/total*1144 if total else 0
        body += f'<rect x="{x}" y="95" width="{width}" height="22" fill="#{shades[i]}"/>'; x += width
        body += text(28+(i%3)*385, 151+(i//3)*31, f'{name} {value/total*100:.1f}%', 18, shades[i])
    if not main: body += text(28, 150, 'No public code language bytes available', 18)
    body += text(28, 226, 'Private code and forks excluded / language share does not measure proficiency', 14)
    return svg(ACCOUNT + ' public language distribution', body, 250)

def card(title, category, lines):
    body = text(28, 38, category, 15, SECOND) + text(28, 92, title, 34, ACCENT, True)
    for i, line in enumerate(lines[:3]): body += text(28, 136+i*29, line, 19)
    return svg(title, body, 245)

def render(data, shared):
    OUT.mkdir(parents=True, exist_ok=True)
    # Validate all source data before replacing any of the previous cards.
    assert data['contributions']['daily'] and data['profile']['login'].lower() == ACCOUNT.lower()
    save('stats.svg', stat_card(data)); save('activity.svg', calendar_card(data)); save('languages.svg', languages_card(data))
    save('data.json', json.dumps(data, indent=2) + '\n')
    readme = Path('README.md').read_text()
    readme = readme.replace('## Development activity', '## Development graph').replace('## GitHub activity & languages', '## GitHub graphs & languages')
    readme = readme.replace('Contribution_calendar-', 'Development_graph-').replace('Automatically refreshed rolling-year GitHub contribution activity', 'Automatically refreshed monthly GitHub development graph').replace('Automatically refreshed rolling-year GitHub activity', 'Automatically refreshed monthly GitHub development graph')
    previous_path = OUT / 'shared-state.json'
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else shared
    for key, item in shared['items'].items():
        before = previous['items'].get(key, item)
        if before['url'] != item['url']: readme = readme.replace(before['url'], item['url'])
        if before['title'] != item['title']: readme = readme.replace(before['title'], item['title'])
        for path in item.get('cards', {}).get(ACCOUNT, []):
            target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                visual = target.read_text().replace(esc(before['title']), esc(item['title']))
                for old_line, new_line in zip(before['lines'], item['lines']):
                    visual = visual.replace(esc(old_line), esc(new_line))
                target.write_text(visual)
            else:
                target.write_text(card(item['title'], item['category'], item['lines']))
    save('shared-state.json', json.dumps(shared, indent=2)+'\n')
    release = data.get('release')
    if ACCOUNT == 'HR-Presents':
        portfolio = [(len(shared['founders']), 'Co-founders'), (sum('PRODUCT' in i['category'] for i in shared['items'].values()), 'Shared software products'), (sum('EDUCATION' in i['category'] for i in shared['items'].values()), 'Co-created courses'), (len(shared['projects']), 'Listed engineering projects')]
        body = text(28, 40, 'Company portfolio / shared source inventory', 26, ACCENT, True) + text(28, 70, 'profile-data.json / refreshed '+STAMP, 16)
        for i, (value, label) in enumerate(portfolio):
            x = 28+i*292; body += text(x, 125, value, 34, SECOND, True) + text(x, 157, label, 16)
        Path('assets/company/company-dashboard.svg').write_text(svg('Shared company portfolio inventory', body, 185))
        body = text(28, 40, 'Public repository status / AegisLog', 26, ACCENT, True) + text(28, 70, 'Automatically refreshed / ' + STAMP, 16)
        summary = data['product']
        for i, (value, label) in enumerate([(summary['stargazers_count'], 'Stars'), (summary['forks_count'], 'Forks'), (summary['open_issues_count'], 'Open issues / PRs'), ((release or {}).get('tag_name', 'No release'), 'Latest published release')]):
            x = 28+i*292; body += text(x, 125, value, 30, SECOND, True) + text(x, 157, label, 16)
        Path('assets/company/repository-stats.svg').write_text(svg('AegisLog current public metadata', body, 185))
        if release:
            readme = re.sub(r'https://github.com/HR-Presents/AegisLog/releases/tag/[^)\s"]+', release['html_url'], readme)
            readme = re.sub(r'/badge/Release-v[^?]+\?', '/badge/Release-'+release['tag_name']+'?', readme)
        Path('assets/company/release-badge.svg').write_text(status_badge('Release', (release or {}).get('tag_name', 'unavailable'), '426253'))
        for key in ['ci', 'security']:
            check = data.get('checks', {}).get(key, {})
            value = check.get('conclusion') or check.get('status', 'unknown')
            color = '426253' if value == 'success' else '9A5B58' if value == 'failure' else '80683E'
            Path('assets/company/'+key+'-badge.svg').write_text(status_badge('CI' if key == 'ci' else 'Security', value, color))
        status = data['workflow']
        url = status.get('html_url', 'https://github.com/HR-Presents/AegisLog/actions')
        result = status.get('conclusion') or status.get('status', 'unknown')
        block = '**Latest release workflow:** '+result+' · checked '+STAMP+'. Published-release availability is separate from a newer workflow result.\n\n[![Latest publishing run](https://img.shields.io/badge/Publishing_run-'+result+'-405D70?style=flat-square)]('+url+')\n\n'
        readme = re.sub(r'<!-- LIVE-WORKFLOW:START -->[\s\S]*?<!-- LIVE-WORKFLOW:END -->', '<!-- LIVE-WORKFLOW:START -->\n'+block+'<!-- LIVE-WORKFLOW:END -->', readme)
    # The generated section has one shared content source, while surrounding prose stays editable.
    overview = '\n'.join('**'+item['title']+'** — '+item['summary']+'  \n[![Open '+item['title']+'](https://img.shields.io/badge/'+quote(item['title'].replace('-', '--').replace('_', '__'))+'-'+ACCENT+'?style=flat-square)]('+item['url']+')\n' for item in shared['items'].values())
    readme = re.sub(r'<!-- SHARED-CONTENT:START -->[\s\S]*?<!-- SHARED-CONTENT:END -->', '<!-- SHARED-CONTENT:START -->\n'+overview+'<!-- SHARED-CONTENT:END -->', readme)
    Path('README.md').write_text(readme)


def status_badge(label, value, color):
    left = max(55, len(label)*7+18); right = max(65, len(str(value))*7+18)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{left+right}" height="22" role="img"><title>{esc(label)}: {esc(value)}</title><rect width="{left+right}" height="22" rx="3" fill="#35444B"/><path d="M{left} 0H{left+right}V22H{left}Z" fill="#{color}"/><text x="{left/2}" y="15" text-anchor="middle" fill="#F4F1E9" font-family="Arial" font-size="12">{esc(label)}</text><text x="{left+right/2}" y="15" text-anchor="middle" fill="#F4F1E9" font-family="Arial" font-size="12">{esc(value)}</text></svg>\n'

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--fixture'); args = parser.parse_args()
    if args.fixture:
        bundle = json.loads(Path(args.fixture).read_text()); render(bundle['data'], bundle['shared']); return
    shared = json.loads(Path('profile-data.json').read_text()) if ACCOUNT == 'HR-Presents' else json.loads(request('https://raw.githubusercontent.com/HR-Presents/HR-Presents/main/profile-data.json'))
    profile = api('/users/'+ACCOUNT)
    repos = [r for r in pages('/users/'+ACCOUNT+'/repos?type=owner') if not r['private']]
    languages = {}
    for repo in repos:
        if repo['fork']: continue
        for name, count in api('/repos/'+repo['full_name']+'/languages').items():
            languages[name] = languages.get(name, 0)+count
    data = {'account': ACCOUNT, 'updated_at': STAMP, 'profile': {key: profile[key] for key in ['login','followers','following','public_repos']}, 'repos': [{key:r[key] for key in ['full_name','html_url','description','stargazers_count','forks_count','language','fork']} for r in repos], 'languages': languages, 'contributions': contributions()}
    if ACCOUNT == 'HR-Presents':
        data['product'] = api('/repos/HR-Presents/AegisLog')
        try: data['release'] = api('/repos/HR-Presents/AegisLog/releases/latest')
        except urllib.error.HTTPError as exc:
            if exc.code != 404: raise
            data['release'] = None
        runs = api('/repos/HR-Presents/AegisLog/actions/runs?per_page=100')
        data['workflow'] = next((r for r in runs['workflow_runs'] if r['name'] == 'Publish reviewed release'), {})
        data['checks'] = {key: next((r for r in runs['workflow_runs'] if r.get('path') == '.github/workflows/'+key+'.yml'), {}) for key in ['ci','security']}
    render(data, shared)
    print('Refreshed public profile facts and shared cards for '+ACCOUNT)

if __name__ == '__main__': main()
