"""Inject the platform's data JSON into the template and write the output files.
Run after build_dashboard_data.py.

Default (PLATFORM=blinkit): dashboard_data.json -> dashboard.html + index.html
(the Vercel root). PLATFORM=instamart/zepto: <platform>_dashboard_data.json ->
<platform>.html (a standalone page that leaves index.html untouched)."""
import os
PLATFORM = os.environ.get('PLATFORM', 'blinkit').lower()
data_file = 'dashboard_data.json' if PLATFORM == 'blinkit' else f'{PLATFORM}_dashboard_data.json'
outputs = ('dashboard.html', 'index.html') if PLATFORM == 'blinkit' else (f'{PLATFORM}.html',)

data = open(data_file).read()
html = open('dashboard_template.html').read()
out = html.replace('/*__DATA__*/', data)
assert '/*__DATA__*/' not in out, 'data placeholder not replaced'
for f in outputs:
    open(f, 'w').write(out)
print(f'[{PLATFORM}] Wrote {", ".join(outputs)} ({len(out)//1024} KB each)')
