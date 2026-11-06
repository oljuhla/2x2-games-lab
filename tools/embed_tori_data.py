#!/usr/bin/env python3
"""Refresh the compact games array embedded in tori/four-tori.html from data/games-2x2.json.
The 3D page is a standalone file, so it carries its own copy of the data."""
import json, os, re
here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, '..', 'data', 'games-2x2.json'), encoding='utf-8'))
compact = [{'g': x['game'], 'L': x['layer'], 'r': x['row'], 'c': x['col'], 'a': x['abbr'], 'n': x['name'],
            'f': x['subfamily'], 'r34': x['r34'], 'c34': x['c34'], 's': x['symmetric']} for x in rows]
path = os.path.join(here, '..', 'tori', 'four-tori.html')
html = open(path, encoding='utf-8').read()
new, n = re.subn(r'const GAMES = \[.*?\];', lambda m: 'const GAMES = ' + json.dumps(compact, ensure_ascii=False, separators=(',', ':')) + ';', html, count=1, flags=re.S)
assert n == 1, 'GAMES array not found'
open(path, 'w', encoding='utf-8').write(new)
print('updated', os.path.normpath(path))
