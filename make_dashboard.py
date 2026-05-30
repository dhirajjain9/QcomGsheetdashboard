"""Inject dashboard_data.json into the template and write the output files.
Run after build_dashboard_data.py. Writes dashboard.html (download) and
index.html (Vercel root)."""
data = open('dashboard_data.json').read()
html = open('dashboard_template.html').read()
out = html.replace('/*__DATA__*/', data)
assert '/*__DATA__*/' not in out, 'data placeholder not replaced'
for f in ('dashboard.html', 'index.html'):
    open(f, 'w').write(out)
print(f'Wrote dashboard.html + index.html ({len(out)//1024} KB each)')
