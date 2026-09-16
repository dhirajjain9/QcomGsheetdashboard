"""Inject the platform's data JSON into the template and write the output files.
Run after build_dashboard_data.py.

Default (PLATFORM=blinkit): dashboard_data.json -> dashboard.html + index.html
(the Vercel root). PLATFORM=instamart/zepto: <platform>_dashboard_data.json ->
<platform>.html (a standalone page that leaves index.html untouched)."""
import os, json
PLATFORM = os.environ.get('PLATFORM', 'blinkit').lower()
data_file = 'dashboard_data.json' if PLATFORM == 'blinkit' else f'{PLATFORM}_dashboard_data.json'
outputs = ('dashboard.html', 'index.html') if PLATFORM == 'blinkit' else (f'{PLATFORM}.html',)

data = open(data_file).read()
html = open('dashboard_template.html').read()

# --- month-label tokens (derived from the data so they never go stale) ---
_MS = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
_ML = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July',
       'August', 'September', 'October', 'November', 'December']
_meta = json.loads(data)['meta']
def _mo(iso):  # '2026-08-01' -> month int
    return int(iso[5:7])
_cur, _prev = _mo(_meta['latest']), _mo(_meta['prev'])
_cur_y, _prev_y = _meta['latest'][:4], _meta['prev'][:4]
tokens = {
    '{{CUR}}': _MS[_cur], '{{PREV}}': _MS[_prev],
    '{{CURL}}': _ML[_cur], '{{PREVL}}': _ML[_prev],
    '{{CURY}}': f'{_MS[_cur]} {_cur_y}', '{{PREVY}}': f'{_MS[_prev]} {_prev_y}',
}
for k, v in tokens.items():
    html = html.replace(k, v)
assert '{{' not in html, f'unfilled month token remains: {html[html.find("{{"):html.find("{{")+12]}'

out = html.replace('/*__DATA__*/', data)
assert '/*__DATA__*/' not in out, 'data placeholder not replaced'
for f in outputs:
    open(f, 'w').write(out)
print(f'[{PLATFORM}] Wrote {", ".join(outputs)} ({len(out)//1024} KB each)')
