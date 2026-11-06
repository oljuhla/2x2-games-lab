#!/usr/bin/env python3
"""Generate data/games-2x2.json: the 144 strict ordinal 2x2 games of the
Robinson-Goforth topology, in Bryan Bruns' chart layout and naming.

Everything except the names, notes and Rapoport-Guyer numbers is derived from
first principles (payoff patterns, equilibria, families, swaps). Names and RG
numbers are transcribed from Bruns' 2011 chart (2x2chart110602.pdf); the
binomial codes follow Bruns (2015), "Names for Games", Games 6, 495-520.

Run:  python3 tools/generate_games.py            (writes data/games-2x2.json)
      python3 tools/generate_games.py --check    (only verifies invariants)
"""
import json, sys, os
from collections import deque, Counter, defaultdict

# --- Payoff patterns ------------------------------------------------------
# Matrices are [[TL, TR], [BL, BR]]; Row picks the row (Top/Bottom),
# Column picks the column (Left/Right). Orientation "Right-Up":
# Row's 4 is in the right column, Column's 4 is in the top row.
ROW_TOP = {1: [[1, 3], [2, 4]], 2: [[2, 3], [1, 4]], 3: [[3, 2], [1, 4]],
           4: [[3, 1], [2, 4]], 5: [[2, 1], [3, 4]], 6: [[1, 2], [3, 4]]}   # Row's 4 bottom-right
ROW_BOT = {k: [v[1], v[0]] for k, v in ROW_TOP.items()}                     # Row's 4 top-right
def anti(R):  # Column's pattern that mirrors a Row pattern (players swapped)
    return [[R[1][1], R[0][1]], [R[1][0], R[0][0]]]
COL_RIGHT = {k: anti(v) for k, v in ROW_TOP.items()}   # Column's 4 top-left  (layers 1, 2)
COL_LEFT = {k: anti(v) for k, v in ROW_BOT.items()}    # Column's 4 top-right (layers 3, 4)
def patterns(L):
    return (ROW_TOP if L in (1, 4) else ROW_BOT), (COL_RIGHT if L in (1, 2) else COL_LEFT)

# --- Names from Bruns' 2011 chart (layer, row pattern, column pattern) ------
NAMES_TXT = """
421 Hg Hegemony|426 Sd Samaritan's Dilemma|425 Qt Quasi-Altruist Type|424 Bc Biased Cycle|423 Ic Inferior Cycle|422 En Endless
431 Sn Samson|436 Ge Generous|435 Ge Generous|434 Qc Quasi Cycle|433 Tc Tragic Cycle|432 In Inspector
441 Dh Delilah|446 Ge Generous|445 Ge Generous|444 Pc Pursuit Cycle|443 Fs Fixed Sum|442 Mc Missile Crisis
451 Hs Hostage|456 Be Benevolent|455 Su Subsymmetric Benevolent|454 Se Second Best|453 Se Second Best|452 Bb Big Bully
461 Mt Blackmail Type|466 Bt Benevolent Type|465 Be Benevolent|464 Se Second Best|463 Se Second Best|462 Ha Hamlet
411 Ht Hegemony Type|416 At Altruist Type|415 Au Altruist|414 Re Revelation|413 Ai Alibi|412 Ap Asymmetric Prisoner's Dilemma
121 Cb Called Bluff|126 Bu Bully|125 Ut Unfair Type|124 Sb Skewed Battle|123 Ab Asymmetric Battle|122 Ch Chicken
131 Pn Patron|136 Pr Protector|135 Pr Protector|134 Qb Quasi-Battle|133 Ba Battle of the Sexes|132 Ab Asymmetric Battle
141 Pn Patron|146 Pr Protector|145 Pr Protector|144 Hr Hero|143 Qb Quasi-Battle|142 Sb Skewed Battle
151 Tr Tragedy|156 Ad Asymmetric Deadlock|155 De Prisoner's Delight|154 Pr Protector|153 Pr Protector|152 Ut Unfair Type
161 Tc Total Conflict|166 Dl Deadlock|165 Ad Asymmetric Deadlock|164 Pr Protector|163 Pr Protector|162 Bu Bully
111 Pd Prisoner's Dilemma|116 Tc Total Conflict|115 Tr Tragedy|114 Pn Patron|113 Pn Patron|112 Cb Called Bluff
321 Lc Low Conflict|326 Al Aligned|325 Pl Pure Aligned|324 Ac Asymmetric Coordination|323 Aa Asymmetric Assurance|322 Sh Stag Hunt
331 Mu Mutual|336 Pv Privileged|335 Pv Privileged|334 Po Pure Coordination|333 Ar Assurance|332 Aa Asymmetric Assurance
341 Mu Mutual|346 Pv Privileged|345 Pv Privileged|344 Co Coordination|343 Po Pure Coordination|342 Ac Asymmetric Coordination
351 Al Aligned|356 Ah Asymmetric Harmony|355 Mh Mixed Harmony|354 Pv Privileged|353 Pv Privileged|352 Pl Pure Aligned
361 Pl Pure Aligned|366 Hm Harmony|365 Ah Asymmetric Harmony|364 Pv Privileged|363 Pv Privileged|362 Al Aligned
311 Nc No Conflict|316 Pl Pure Aligned|315 Al Aligned|314 Mu Mutual|313 Mu Mutual|312 Lc Low Conflict
221 Ap Asymmetric Prisoner's Dilemma|226 Ha Hamlet|225 Bb Big Bully|224 Mc Missile Crisis|223 In Inspector|222 En Endless
231 Ai Alibi|236 Se Second Best|235 Se Second Best|234 Fs Fixed Sum|233 Tc Tragic Cycle|232 Ic Inferior Cycle
241 Re Revelation|246 Se Second Best|245 Se Second Best|244 Pc Pursuit Cycle|243 Qc Quasi Cycle|242 Bc Biased Cycle
251 Au Altruist|256 Be Benevolent|255 Su Subsymmetric Benevolent|254 Ge Generous|253 Ge Generous|252 Qt Quasi-Altruist Type
261 At Altruist Type|266 Bt Benevolent Type|265 Be Benevolent|264 Ge Generous|263 Ge Generous|262 Sd Samaritan's Dilemma
211 Ht Hegemony Type|216 Mt Blackmail Type|215 Hs Hostage|214 Dh Delilah|213 Sn Samson|212 Hg Hegemony
"""
NAMES = {}
for line in NAMES_TXT.strip().splitlines():
    for item in line.split('|'):
        n, a, nm = item.strip().split(' ', 2)
        NAMES[int(n)] = (a, nm)

# --- Rapoport-Guyer numbers, read from panel h of the 2011 chart -----------
# Rows top to bottom are row patterns 2,3,4,5,6,1; columns left to right are
# column patterns 1,6,5,4,3,2 for the left quadrant, then the same for the right.
RG_TOP = ["55 50 49 70 78 72 39 35 36 65 67 66", "56 52 51 74 76 71 37 31 32 64 68 67",
          "44 41 40 73 75 77 38 33 34 69 64 65", "18 16 15 53 42 45 10 8 7 34 32 36",
          "17 14 13 54 43 46 11 9 8 33 31 35", "21 19 20 57 47 48 12 11 10 38 37 39"]   # layers 4 | 1
RG_BOT = ["26 22 23 58 62 61 48 46 45 77 71 72", "27 24 25 59 63 62 47 43 42 75 76 78",
          "30 28 29 60 59 58 57 54 53 73 74 70", "2 4 5 29 25 23 20 13 15 40 51 49",
          "1 3 4 28 24 22 19 14 16 41 52 50", "6 1 2 30 27 26 21 17 18 44 56 55"]        # layers 3 | 2
ROWS_ORDER = [2, 3, 4, 5, 6, 1]
COLS_ORDER = [1, 6, 5, 4, 3, 2]
RG = {}
for lines, layers in ((RG_TOP, (4, 1)), (RG_BOT, (3, 2))):
    for i, line in enumerate(lines):
        vals = list(map(int, line.split()))
        for j in range(12):
            L = layers[0] if j < 6 else layers[1]
            RG[L * 100 + ROWS_ORDER[i] * 10 + COLS_ORDER[j % 6]] = vals[j]

# --- Binomial codes (Bruns 2015): Row's symmetric pattern then Column's -----
SYM1 = {1: ('Pd', "Prisoner's Dilemma"), 2: ('Ch', 'Chicken'), 3: ('Ba', 'Battle of the Sexes'),
        4: ('Hr', 'Hero'), 5: ('Cm', "Prisoner's Delight"), 6: ('Dl', 'Deadlock')}
SYM3 = {1: ('Nc', 'No Conflict'), 2: ('Sh', 'Stag Hunt'), 3: ('As', 'Assurance'),
        4: ('Co', 'Coordination'), 5: ('Pc', 'Mixed Harmony'), 6: ('Ha', 'Harmony')}

NOTES = {
    '111': "Both players prefer mutual cooperation (3,3), but each has a dominant strategy to defect, so they end at (2,2), their second-worst outcome.",
    '122': "Hawk–Dove. Mutual Hawk is the worst outcome for both (1,1); mutual Dove gives both second-best (3,3). The two equilibria are very unequal: one swerves, one doesn't.",
    '133': "A couple wants to do something together, but each has a different first choice. Two equilibria, each favouring one player.",
    '144': "A Battle-type game with two equilibria, each giving one player their best outcome and the other their second-best.",
    '155': "Called Anti-Chicken on the chart. Dominant strategies lead both players to their second-best outcome (3,3).",
    '166': "Called Anti-Prisoner's Dilemma on the chart. Incentives lead to the second-best outcome (3,3) for both.",
    '322': "Cooperating on the stag gives both their best outcome; hunting hare is the safe choice. Two equilibria: (4,4) and (2,2).",
    '333': "Two equilibria, but both players prefer the same one (4,4); the risk is failing to coordinate on it.",
    '344': "Pure coordination problem: two equilibria, with both preferring (4,4) over (3,3).",
    '355': "Interests mostly aligned; dominant strategies lead to win-win (4,4).",
    '366': "Either player's choice benefits the other, and incentives lead to win-win (4,4).",
    '311': "The best outcomes coincide and dominant strategies lead straight there.",
    '443': "Ordinal equivalent of zero-sum: gains for one are losses for the other. Cyclic, since one player always wants to move; maximin strategies avoid the worst payoff.",
    '234': "Ordinal equivalent of zero-sum: gains for one are losses for the other. Cyclic, since one player always wants to move; maximin strategies avoid the worst payoff.",
    '262': "One player could do fine alone; the other wants to help whatever happens, while the helped player most prefers to be helped and do less.",
    '426': "One player could do fine alone; the other wants to help whatever happens, while the helped player most prefers to be helped and do less.",
    '216': "A Jekyll-Hyde type game: incentives make one player kind and the other cruel.",
    '461': "A Jekyll-Hyde type game: incentives make one player kind and the other cruel.",
    '412': "One high swap from Prisoner's Dilemma; a second high swap for the other player turns it into Stag Hunt.",
    '221': "One high swap from Prisoner's Dilemma; a second high swap for the other player turns it into Stag Hunt.",
}

CELLS = ['TL', 'TR', 'BL', 'BR']
flat = lambda M: [M[0][0], M[0][1], M[1][0], M[1][1]]

GAMES = {}
for L in (1, 2, 3, 4):
    RP, CP = patterns(L)
    for r in range(1, 7):
        for c in range(1, 7):
            GAMES[L * 100 + r * 10 + c] = (RP[r], CP[c])

def lookup(R, C):
    """Normalise to Right-Up orientation and return the game number."""
    R = [row[:] for row in R]; C = [row[:] for row in C]
    if R[0][0] == 4 or R[1][0] == 4:   # Row's 4 must be in the right column
        R = [[x[1], x[0]] for x in R]; C = [[x[1], x[0]] for x in C]
    if C[1][0] == 4 or C[1][1] == 4:   # Column's 4 must be in the top row
        R = [R[1], R[0]]; C = [C[1], C[0]]
    for n, (r, c) in GAMES.items():
        if r == R and c == C:
            return n
    raise ValueError('pattern not found')

def swap(M, a, b):
    return [[(b if x == a else a if x == b else x) for x in row] for row in M]

def analyze(n):
    R, C = GAMES[n]; r = flat(R); c = flat(C)
    ralt = {0: 2, 2: 0, 1: 3, 3: 1}; calt = {0: 1, 1: 0, 2: 3, 3: 2}
    ne = [i for i in range(4) if r[i] > r[ralt[i]] and c[i] > c[calt[i]]]
    rowdom = 'Top' if (r[0] > r[2] and r[1] > r[3]) else 'Bottom' if (r[2] > r[0] and r[3] > r[1]) else ''
    coldom = 'Left' if (c[0] > c[1] and c[2] > c[3]) else 'Right' if (c[1] > c[0] and c[3] > c[2]) else ''
    pareto = [i for i in range(4) if not any(r[j] >= r[i] and c[j] >= c[i] and (r[j] > r[i] or c[j] > c[i]) for j in range(4))]
    if not ne:
        fam, sub = 'Cyclic', 'Cyclic'
    else:
        best = max(ne, key=lambda i: (r[i] + c[i], min(r[i], c[i])))
        pr = tuple(sorted((r[best], c[best]), reverse=True))
        if pr == (4, 4):
            fam, sub = 'Win-win', 'Stag Hunt' if len(ne) == 2 else 'Harmonious'
        elif pr == (4, 3):
            fam = 'Biased'
            if len(ne) == 2:
                sub = 'Battle'
            else:   # Altruistic if the player getting 3 has a dominant strategy
                sub = 'Altruistic' if (rowdom if r[best] == 3 else coldom) else 'Self-serving'
        elif pr == (3, 3):
            fam, sub = 'Second Best', 'Second Best'
        elif pr == (4, 2):
            fam, sub = 'Unfair', 'Unfair'
        else:
            fam = 'PD Family'
            sub = "Prisoner's Dilemma" if pr == (2, 2) else ('Alibi' if best not in pareto else 'Tragic')
    return dict(ne=ne, rowdom=rowdom, coldom=coldom, pareto=pareto, fam=fam, sub=sub, r=r, c=c)

def mirror(n):
    L, r, c = n // 100, (n // 10) % 10, n % 10
    return {1: 1, 3: 3, 2: 4, 4: 2}[L] * 100 + c * 10 + r

def build():
    A = {n: analyze(n) for n in GAMES}
    nbr = {}
    for n, (R, C) in GAMES.items():
        d = {}
        for a, b in ((1, 2), (2, 3), (3, 4)):
            d[f'r{a}{b}'] = lookup(swap(R, a, b), C)
            d[f'c{a}{b}'] = lookup(R, swap(C, a, b))
        nbr[n] = d
    winwin = {n for n in GAMES if A[n]['fam'] == 'Win-win'}
    dist = {n: 0 for n in winwin}; q = deque(winwin)
    while q:
        u = q.popleft()
        for v in nbr[u].values():
            if v not in dist:
                dist[v] = dist[u] + 1; q.append(v)
    rows = []
    for n in sorted(GAMES):
        a = A[n]; ab, nm = NAMES[n]; L = n // 100; ri = (n // 10) % 10; ci = n % 10
        rs = (SYM1 if L in (1, 4) else SYM3)[ri]; cs = (SYM1 if L in (1, 2) else SYM3)[ci]
        sym = mirror(n) == n
        rows.append(dict(
            game=str(n), layer=L, row=ri, col=ci, abbr=ab, name=nm,
            rowPay=','.join(map(str, a['r'])), colPay=','.join(map(str, a['c'])),
            family=a['fam'], subfamily=a['sub'], nashCount=len(a['ne']),
            nash=' '.join(CELLS[i] for i in a['ne']),
            nashPayoffs=' '.join(f"{a['r'][i]},{a['c'][i]}" for i in a['ne']),
            rowDominant=a['rowdom'], colDominant=a['coldom'],
            dominance={2: 'Both', 1: 'Row' if a['rowdom'] else 'Column', 0: 'Neither'}[bool(a['rowdom']) + bool(a['coldom'])],
            paretoOptimal=' '.join(CELLS[i] for i in a['pareto']),
            symmetric=sym, mirror=str(mirror(n)), swapsToWinWin=dist[n],
            **{k: str(v) for k, v in nbr[n].items()},
            note=NOTES.get(str(n), ''),
            binomial=rs[0] if sym else rs[0] + cs[0],
            binomialName=rs[1] if sym else rs[1] + ' × ' + cs[1],
            rapoportGuyer=RG[n]))
    return rows

def check(rows):
    G = {x['game']: x for x in rows}
    assert len(rows) == 144
    assert sum(x['symmetric'] for x in rows) == 12
    assert len({tuple(sorted((x['game'], x['mirror']))) for x in rows}) == 78
    # Mirror pairs share name abbreviation and Rapoport-Guyer number
    assert all(G[x['mirror']]['abbr'] == x['abbr'] for x in rows)
    assert all(G[x['mirror']]['rapoportGuyer'] == x['rapoportGuyer'] for x in rows)
    rg_orbits = defaultdict(set)
    for x in rows: rg_orbits[x['rapoportGuyer']].add(tuple(sorted((x['game'], x['mirror']))))
    assert sorted(rg_orbits) == list(range(1, 79)) and all(len(v) == 1 for v in rg_orbits.values())
    # Well-known games
    for g, ab, rg, ne in (('111', 'Pd', 12, '2,2'), ('122', 'Ch', 66, '2,4 4,2'), ('133', 'Ba', 68, '3,4 4,3'),
                          ('144', 'Hr', 69, '3,4 4,3'), ('166', 'Dl', 9, '3,3'), ('322', 'Sh', 61, '4,4 2,2')):
        assert G[g]['abbr'] == ab and G[g]['rapoportGuyer'] == rg, g
        assert sorted(G[g]['nashPayoffs'].split()) == sorted(ne.split()), g
    assert G['262']['binomial'] == 'HaCh'   # Samaritan's Dilemma = Harmony x Chicken (Bruns 2015)
    # Counts quoted by Bruns (2015)
    fam = Counter(x['family'] for x in rows); sub = Counter(x['subfamily'] for x in rows)
    assert fam['Win-win'] == 36 and fam['Cyclic'] == 18
    assert fam['Win-win'] + fam['Biased'] + fam['Second Best'] == 92
    assert sub["Prisoner's Dilemma"] + sub['Alibi'] == 7 and sub['Stag Hunt'] == 9
    assert Counter(x['nashCount'] for x in rows) == {1: 108, 2: 18, 0: 18}
    assert sum(x['dominance'] == 'Neither' for x in rows) == 36
    # Every swap is symmetric (an involution) and each game has 6 distinct neighbours
    for x in rows:
        for k in ('r12', 'r23', 'r34', 'c12', 'c23', 'c34'):
            assert G[x[k]][k] == x['game'], (x['game'], k)
    # Row and Column high swaps commute: 36 linking squares (24 pipes, 12 hotspots)
    squares = set()
    for x in rows:
        a = G[G[x['game']]['r34']]['c34']; b = G[G[x['game']]['c34']]['r34']
        assert a == b
        squares.add(frozenset([x['game'], x['r34'], x['c34'], a]))
    assert len(squares) == 36
    kinds = Counter(len({G[g]['layer'] for g in s}) for s in squares)
    assert kinds == {4: 24, 2: 12}
    return True

if __name__ == '__main__':
    rows = build()
    check(rows)
    if '--check' not in sys.argv:
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'games-2x2.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print('wrote', os.path.normpath(out), len(rows), 'games')
    print('all invariants hold')
