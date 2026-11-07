# 2×2 Games Lab

An interactive explorer of the 144 strict ordinal 2×2 games, laid out as Robinson and Goforth's periodic table in Bryan Bruns' 2011 chart arrangement.

## Features

| Feature | Derived from |
|---|---|
| 12×12 periodic table of the 144 games: four layers, Row/Column patterns, Right-Up orientation, `L R C` game numbers | Robinson & Goforth (2005) |
| Chart order with Prisoner's Dilemma at the centre, game names and abbreviations | Bruns (2011) chart |
| Alternative "tiles grouped" ordering; one-swap adjacency across the table (each layer a 6×6 torus) | Robinson & Goforth (2005) |
| Fold to the 78 distinct games (mirror pairs, Bruns' right-hand forms) with Rapoport–Guyer numbers | Rapoport & Guyer (1966); Bruns (2011) panel h |
| Colour modes: family, Nash equilibria, dominance, swaps to win-win, layer | Families and subfamilies from Bruns (2011, 2015); counts computed |
| Binomial game codes (e.g. Samaritan's Dilemma = `HaCh`) | Bruns (2015) |
| Search by name, abbreviation or number; keyboard navigation | — |
| Side panel per game: payoff matrix, payoff-space graph, facts, the six one-swap neighbours | Robinson & Goforth (2005) |
| Mixed-equilibrium view of the 36 games without a dominant strategy | Standard indifference conditions |
| Evolutionary dynamics: replicator, best response, logit, Brown–von Neumann–Nash, Smith; one- and two-population phase diagrams, basins, replicator separatrix | Sandholm (2010) |
| Payoff sliders (cardinal values for ranks 2 and 3) and an "equilibrium mix" mode that solves for payoffs | — |

All game facts come from `data/games-2x2.json`, generated from first principles by `tools/generate_games.py`, which asserts the published counts and known games.

## Run locally

```bash
python3 tools/generate_games.py --check   # verify data invariants
node tests/check_scripts.mjs              # parse-check inline scripts
python3 -m http.server 8000               # open http://localhost:8000/
```

Pages must be served over http. d3 loads from a CDN.

## Sources

- Robinson, D. and Goforth, D. (2005). *The Topology of the 2×2 Games: A New Periodic Table*. Routledge.
- Bruns, B. (2011). *2×2 Games* chart. www.BryanBruns.com/2x2chart.html
- Bruns, B. R. (2015). Names for Games: Locating 2×2 Games. *Games* 6, 495–520.
- Rapoport, A. and Guyer, M. (1966). A taxonomy of 2×2 games. *General Systems* 11.
- Sandholm, W. H. (2010). *Population Games and Evolutionary Dynamics*. MIT Press.
