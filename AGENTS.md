# AGENTS.md — 2×2 Games Lab: a visual compendium

Guide for coding agents (and humans) extending this project. Read it fully before changing code: most bugs here come from breaking a convention silently, not from hard algorithms.

## 1. What this is

An interactive explorer of the 144 strict ordinal 2×2 games, laid out as Robinson and Goforth's "periodic table" in Bryan Bruns' 2011 chart arrangement, with:

- the 12×12 table, colour modes (family, Nash equilibria, dominance, swaps to win-win, layer), search, two orderings, and a fold to the 78 distinct games with Rapoport–Guyer numbers;
- a side panel per game: payoff matrix, payoff-space graph, facts, the six one-swap neighbours, and an **Evolutionary dynamics** view (five dynamics, payoff sliders, an "equilibrium mix" mode that solves for payoffs);
- a mixed-equilibrium view of the 36 games without a dominant strategy;
- a separate 3D page showing the four layers as tori joined by the 36 high-ties "junction" games.

It began as a claude.ai dashboard artifact. The same files run locally through a small shim (§3).

**Planned next:** stochastic stability, stationary distributions of finite-population processes, supermodular (strategic-complements) structure, and games on networks. §9 describes the target architecture that makes these plug-ins rather than rewrites. **Do Phase 0 (restructure) before adding any of them.**

## 2. Quick start

```bash
# from the project root
python3 tools/generate_games.py --check   # verify the data invariants (no write)
python3 tools/generate_games.py           # regenerate data/games-2x2.json
python3 tools/embed_tori_data.py          # refresh the data copy inside tori/four-tori.html
node tests/check_scripts.mjs              # parse-check every inline <script>
python3 -m http.server 8000               # then open:
#   http://localhost:8000/dashboard/local.html   (the table and side panel)
#   http://localhost:8000/tori/four-tori.html    (the 3D tori)
```

Pages must be served over http; opening the files directly fails because the shim fetches JSON. Third-party code loads from CDNs (d3 7.9.0 and three.js r128 from cdnjs), so the browser needs network access.

## 3. Repository layout

```
AGENTS.md                 this guide
CLAUDE.md                 pointer to this guide
index.html                landing page for GitHub Pages, links to the two pages below
.nojekyll                 tells GitHub Pages to serve files as-is (no Jekyll build)
data/games-2x2.json       the 144 games: the single source of truth for game facts
tools/generate_games.py   builds the data from first principles + transcribed names; asserts invariants
tools/embed_tori_data.py  copies a compact version of the data into the 3D page
dashboard/index.html      the dashboard page fragment (style + markup + one script), as published
dashboard/dash-shim.js    local stand-in for the dashboard runtime (dash.calc / dash.data / dash.onData)
dashboard/local.html      local launcher: theme tokens, d3, the shim, then injects index.html
tori/four-tori.html       standalone 3D page (three.js), carries its own data copy
tests/check_scripts.mjs   syntax check for the inline scripts
```

### Two runtimes, one page

`dashboard/index.html` is a *fragment* written for the claude.ai dashboard runtime. That runtime provides:

- a `dash` global: `dash.calc(id, {inputs, title, description, fn})`, `dash.data(id) → {status, data}`, `dash.onData(cb)`;
- `d3` v7 as a global;
- theme CSS variables (`--color-*`, `--cds-*`, `--font-anthropic-*`).

It does **not** allow network requests, ES modules or frameworks. Scripts run in order, each in its own scope.

`dash-shim.js` + `local.html` reproduce exactly that surface locally. Rules that keep both working:

- Only use `dash.calc`, `dash.data`, `dash.onData` (and `d3`). If you need more from the host, add it to the shim *and* confirm the real runtime offers it.
- Use the theme variables rather than hard-coded chrome colours. Data-encoding colours (family palette, Row red / Column blue) are fixed hex values and must read well on light and dark backgrounds.
- `onData` re-runs on load, on data changes and on resize. Callbacks must be idempotent and must handle `status !== 'ok'` (loading/error) without leaving stale output.
- Numbers shown in the dashboard should come from the dataset or a `dash.calc`. Inside the dashboard, figures are traced back to their source through `data-source` / `data-field` attributes; keep these accurate when you edit markup.
- If the page is redeployed to claude.ai, the dataset URL is an uploaded asset rather than `../data/…`. The page itself never hard-codes the URL.

## 4. Domain model and conventions (do not change without a migration plan)

### Payoffs, cells, orientation

- Each player ranks the four outcomes 1 (worst) … 4 (best), no ties.
- Cells are `TL, TR, BL, BR`. Row chooses Top/Bottom; Column chooses Left/Right. Payoff strings (`rowPay`, `colPay`) list ranks in that cell order, e.g. Prisoner's Dilemma `rowPay "1,3,2,4"`, `colPay "4,3,2,1"`.
- **Right-Up orientation** (Robinson–Goforth): Row's 4 is in the right column; Column's 4 is in the top row. Every game has exactly one such drawing. Any transformation (swaps) must re-normalise to Right-Up before looking a game up (`lookup()` in the generator).

### Game numbers `L R C`

- `L` = layer (alignment of the two 4s), `R` = Row's pattern 1–6, `C` = Column's pattern 1–6.

| Layer | Row's 4 | Column's 4 | Meaning |
|---|---|---|---|
| 1 | bottom-right | top-left | 4s in opposite corners (discord; Prisoner's Dilemma, Chicken, Battle) |
| 2 | top-right | top-left | 4s share the top row |
| 3 | top-right | top-right | 4s in the same cell (win-win) |
| 4 | bottom-right | top-right | 4s share the right column |

- Row patterns are defined in `ROW_TOP` (layers 1, 4) and `ROW_BOT = vertical flip` (layers 2, 3). Column patterns are the *anti-transpose* of a Row pattern: `C[r][c] = R[1-c][1-r]` (`COL_RIGHT` for layers 1, 2; `COL_LEFT` for layers 3, 4). This anti-transpose is what makes a game with the same Row and Column index on layers 1 or 3 symmetric.
- Within a layer, patterns `{1,2}`, `{3,4}`, `{5,6}` are linked by 1↔2 swaps (tiles).

### Table layout

- Quadrants: layer 4 top-left, layer 1 top-right, layer 3 bottom-left, layer 2 bottom-right.
- **Chart order** (default, Prisoner's Dilemma at the centre): rows top→bottom `[2,3,4,5,6,1]`, columns left→right `[1,6,5,4,3,2]`, in every quadrant.
- **Tiles grouped**: rows `[6,5,4,3,2,1]`, columns `[1,2,3,4,5,6]`.
- In both orders the symmetric games lie on the bottom-left → top-right diagonal, at in-quadrant positions with `rowIndex + colIndex = 5`.
- On the 12×12 grid in chart order, every pair of edge-adjacent cells (with wrap-around) is exactly one swap apart: 288 of the 432 swap links. Each layer on its own is a 6×6 torus containing all its 1↔2 and 2↔3 swaps.

### Mirror (players swapped)

- `mirror(L R C)`: layer `1→1, 3→3, 2↔4`, and `R C → C R`. The 12 fixed points are the symmetric games; the other 132 form 66 pairs (78 distinct games).
- The *fold* keeps all of layer 2, plus the diagonal and lower-right half of layers 1 and 3 in chart order (`rowIndex + colIndex ≥ 5`). This is Bruns' "right-hand forms". It keeps exactly one game from each mirror pair. Folding is defined only for chart order.

### Swaps and neighbours

- Fields `r12, r23, r34, c12, c23, c34` hold the game reached by swapping that player's ranks `a↔b`, re-normalised to Right-Up. Each swap is an involution.
- High swaps (3↔4) move a 4 and so change layer. Row's and Column's high swaps commute: they group the 144 games into **36 squares**. 24 squares span all four layers (6 "pipes"); 12 squares span two layers (6 "hotspots", one per pair of layers). The centre of each square is the game where *both* players tie their two best payoffs.

### Families (computed, see `analyze()`)

- Family by the payoffs at the best pure Nash equilibrium: Win-win (4,4), Biased (4,3), Second Best (3,3), Unfair (4,2), PD family (3,2 or 2,2), Cyclic (no pure equilibrium).
- Subfamilies:
  - Win-win: *Stag Hunt* if two equilibria, else *Harmonious*.
  - Biased: *Battle* if two equilibria; otherwise *Altruistic* if the player receiving 3 has a dominant strategy, else *Self-serving*.
  - PD family: *Prisoner's Dilemma* at (2,2); at (3,2) *Alibi* if the equilibrium is Pareto-deficient, else *Tragic*.
- Bruns (2015) renames *Tragic* as "Sad" and calls Pd/Alibi "Traps"; the partition is the same.
- Checked counts (asserted in the generator): 36 win-win, 18 cyclic, 92 win-win+biased+second best, 7 traps, 9 stag hunts, 108 / 18 / 18 games with 1 / 2 / 0 pure equilibria, 36 with no dominant strategy.

### Names and numbers

- `abbr`/`name`: Bruns' 2011 chart (the user prefers these to the 2015 names).
- `binomial`: Bruns (2015) code, Row's symmetric pattern then Column's (e.g. Samaritan's Dilemma 262 = `HaCh`, Harmony × Chicken). It uses 2015 symbols: `Cm` = Prisoner's Delight, `Pc` = Mixed Harmony, `As` = Assurance, `Ha` = Harmony (not Hamlet).
- `rapoportGuyer`: transcribed from panel h of the 2011 chart; one number 1–78 per mirror pair (asserted).
- `swapsToWinWin`: breadth-first distance to the nearest win-win game.

### Evolutionary dynamics conventions (dashboard script)

- **State** `(u, w)`: `u` = share of Column players choosing **Right** (horizontal axis), `w` = share of Row players choosing **Top** (vertical axis). The square's corners sit where the matrix cells sit. The mixed-equilibrium cards report Column's chance of **Left**, i.e. `1 − u`.
- **Cardinal payoffs** from ranks: worst = 0, best = 1, and ranks 2 and 3 map to slider values `P.r2 < P.r3` (Row) and `P.c2 < P.c3` (Column). The default ⅓, ⅔ is equivalent to using the ranks as payoffs. Ordinal facts (which outcomes are strict equilibria, existence of an interior equilibrium) never depend on these values; positions, basins and selection do.
- **Mixed equilibrium** (only when `dominance === 'Neither'`), with payoff vectors in cell order `[TL, TR, BL, BR]`:
  - `pTop = (c3 − c2)/(c0 − c1 − c2 + c3)`
  - `qLeft = (r3 − r1)/(r0 − r1 − r2 + r3)`
  - `u* = 1 − qLeft`, `w* = pTop`
- **Dynamics** are written as `g(x, d)`: the change in share `x` of a population's first strategy, given that strategy's payoff advantage `d`.

| id | dynamic | g(x, d) |
|---|---|---|
| `rep` | replicator | `x(1−x)d` |
| `br` | best response | `BR(d) − x` (BR = 1, 0, or x when d = 0) |
| `logit` | logit, noise η | `σ(d/η) − x` |
| `bnn` | Brown–von Neumann–Nash | `(1−x)² d` if d > 0, else `x² d` |
| `smith` | Smith (pairwise comparison) | `(1−x) d` if d > 0, else `x d` |

  - Row's advantage: `dRow(u) = [(1−u)r0 + u·r1] − [(1−u)r2 + u·r3]`.
  - Column's advantage: `dCol(w) = [w·c1 + (1−w)c3] − [w·c0 + (1−w)c2]`.
- **One population** (symmetric games only): strategy A = Row's Top = Column's Right. Share `s` playing A; advantage `(s·r1 + (1−s)r0) − (s·r3 + (1−s)r2)`.
- **Basins** are found numerically:
  1. 36×36 grid (22×22 while a slider is dragged); RK4 with step 0.08 for up to 1500 steps.
  2. A point has settled when it moves < 0.003 over 40 steps.
  3. Snap to a strict-equilibrium corner within 0.08, or to the interior Nash point within 0.06 (not for logit).
  4. Cluster endpoints within 0.04.
  5. Keep only resting points that survive ±0.03 pushes in four directions.
  6. Games without a pure equilibrium use one long run instead: spirals in vs. cycles.
- The replicator's dashed separatrix is exact: the stable eigenvector of the saddle's Jacobian `[[0, β], [α, 0]]`, integrated backwards. Other dynamics get no line, because their mixed point is a kink or jump.
- **Mix → payoffs solver**: each player's mix is set by the *other* player's payoffs, and the indifference condition is a line in that player's `(rank-2, rank-3)` values. The solver takes the point on that line, inside `0.01 ≤ a`, `a + 0.01 ≤ b ≤ 0.99`, closest to the current values. Reachable ranges are the extremes over the triangle's vertices. Hero's reachable mix, for example, is about 1–49%.

## 5. Invariants and tests

Run before every commit:

```bash
python3 tools/generate_games.py --check
node tests/check_scripts.mjs
```

The generator asserts: 144 games, 12 symmetric, 78 mirror orbits; mirrors share abbreviation and RG number; RG numbers cover 1–78 once per orbit; known games (Pd 111 = RG 12 with NE (2,2); Ch 122 = 66; Ba 133 = 68; Hr 144 = 69; Dl 166 = 9; Sh 322 = 61); the published family counts; swaps are involutions; high swaps commute into 36 squares (24 four-layer, 12 two-layer).

When you add dynamics or solvers, add **known-answer tests**. These values were checked during development:

- At equal spacing every dynamic splits Stag Hunt (322) evenly, saddle at 50% / 50%. Coordination (344) and Hero (144) have their saddle at 25% / 25%; Pure Coordination (334) at 25% Top / 50% Right.
- Stag Hunt with both middle values near 0.75: saddle and one-population threshold near 75%.
- Cyclic games: replicator orbits are closed; best response, logit, BNN and Smith spiral in (BNN and Smith slowly, distance ~1/t).
- Chicken, one population: the mixed point is stable under all five dynamics. With two populations it is a saddle.
- Bruns (2015): in 5 of the 9 cyclic mirror pairs some outcome beats the mixed equilibrium for both players, and maximin reaches it in 2 of those 5. This is reproduced with ranks as payoffs.

## 6. Known pitfalls (learned the hard way)

- **Selector scoping.** A query for `.tg-sl-row` once caught newly added mix sliders, threw at load time, and froze the page. Scope queries to their container (`#tg-payset .tg-sl-row`) or use data attributes. A thrown error in top-level script stops everything after it.
- **Slow and chattering dynamics.** BNN approaches corners algebraically. Best response chatters around interior points with a fixed step. Detect settling by displacement over a window, not by speed, and snap knowingly.
- **Ordinal vs cardinal claims.** Never state basin sizes, thresholds or selection results as properties of the ordinal game. They depend on payoff values. Say what was assumed.
- **Generated text must be computed.** Summaries such as "spirals in", "two stable outcomes" or "threshold at 75%" are derived from the simulation result, never hard-coded per game.
- **Column's mix wording.** Cards say "Left", plots say "Right". Keep both, but label them.
- **The 3D page has its own data copy.** Run `tools/embed_tori_data.py` after regenerating data.
- **Typography.** User-facing text uses ’ and “ ”, not straight quotes (code and data stay straight). Data `name` values keep straight apostrophes.

## 7. UX conventions

- Row = red (`--tg-row`), Column = blue (`--tg-col`) everywhere: labels, arrows, payoff numbers.
- Family palette (subfamily → colour) is defined once (`FAMILY_COLORS`); reuse it in new views.
- Prose, not bullet-heavy panels. Every control has a visible label; sliders show their value; selections are reachable by keyboard (arrow keys move around the table, wrapping).
- Heavy computations: draw a coarse version while dragging, refine on release.

## 8. Current code map (dashboard script)

One script in `dashboard/index.html`, roughly in this order:

| Area | Contents |
|---|---|
| calcs | `summary`, `legend_counts` (per colour mode, for full and folded scope), `mixed` |
| constants | colour modes `MODES`, orders, quadrant map, `isKept` (fold), `repId` |
| table | `build`, `paint`, `drawLegend`, `showTip`, keyboard navigation |
| side panel | `drawMatrix`, `drawGraph`, `drawDetail`, neighbour buttons |
| mixed view | `mixedCard`, `drawMixed` |
| dynamics | `DYNAMICS` registry, `P` (payoff values / mode / dynamic / η), `dynModel`, mix solver (`mixLine`, `mixOf`, `mixReach`, `mixSolve`, `setMix`), `interior`, `drawDynamics`, `drawOnePop`, slider and mode wiring |
| entry | `dash.onData(...)` |

## 9. Target architecture (Phase 0 refactor)

Goal: stochastic, network and supermodularity work become **additions** (new registry entries and views), not edits across the file.

### Split into files

The runtime loads several scripts that share one namespace, `window.TG`. Load order:

| File | Role | Uses the page? |
|---|---|---|
| `core.js` | `TG` namespace, a small store `{get, set, subscribe}` with change events, registries, parameter-schema helpers | no |
| `game.js` | Game model: ranks → payoff matrices via a realisation (`equalSpacing`, `middleRanks{r2,r3,c2,c3}`, later arbitrary values); general m×n arrays even though data is 2×2; normalisation and lookup | no |
| `analysis.js` | Pure functions: pure and mixed Nash, dominance, Pareto, families, swaps and squares, interaction terms (§10.2) | no |
| `protocols.js` | Revision protocols and noise wrappers (§9.3) | no |
| `populations.js` | Population structures: `oneWellMixed`, `twoWellMixed`, `finite(N)`, `network(graph, roles)` | no |
| `processes.js` | Builds a model from protocol + population: mean dynamic (ODE), finite Markov chain, agent-based simulation | no |
| `solvers.js` | RK4 integrator and basin finder (existing), stationary distribution (birth–death closed form; power iteration or sparse solve), stochastic-stability analysis, Monte Carlo | no |
| `views/*.js` | One file per panel or page: `table`, `payoffs`, `dynamics`, `mixed`; later `stochastic`, `network` | yes |
| `index.html` | Layout, theme hooks, script tags; nothing else | yes |

Everything except `views/*` must be pure, DOM-free and runnable in Node, so the maths can be tested outside the browser (and later moved to a worker or precomputed).

### Registries

Each extension registers a descriptor:

```js
TG.protocols.register({
  id: 'pairwiseImitation', label: 'Imitation (replicator)',
  params: [],                                  // schema, see below
  rate: (i, j, payoffs, x, p) => x[j] * Math.max(payoffs[j] - payoffs[i], 0),   // switch rate i → j
});
TG.views.register({
  id: 'dynamics', label: 'Evolutionary dynamics',
  appliesTo: (game) => true,
  params: ['protocol', 'noise', 'realisation'],
  render: (el, ctx) => { /* draws from ctx.results */ },
});
```

The dynamic picker, panel tabs and colour modes are generated from registries. Adding a model must not require editing existing views.

### Revision protocols are the core abstraction

- A protocol gives switch rates `ρ_ij(π, x)` from strategy i to j.
- **Mean dynamic** (infinite population): `ẋ_i = Σ_j x_j ρ_ji − x_i Σ_j ρ_ij`. All five current dynamics are of this form:

| Dynamic | Protocol `ρ_ij` |
|---|---|
| Replicator | pairwise proportional imitation: `x_j [π_j − π_i]₊` |
| Best response | `1{j ∈ BR(π)}` |
| Logit | logit choice with η |
| BNN | excess payoff: `[π_j − π̄]₊` |
| Smith | pairwise comparison: `[π_j − π_i]₊` |

  With two strategies these reduce exactly to the `g(x, d)` table in §4. Phase 0 must re-derive them through the protocol layer and verify they match the current formulas numerically.
- **Finite populations** (size N) use the same `ρ` to give a Markov chain on population counts. In one population, use payoffs that exclude self-matching: `π_A(i) = ((i−1)a_AA + (N−i)a_AB)/(N−1)`.
- **Noise wrappers** compose with any protocol: uniform mistakes with probability ε (Kandori–Mailath–Rob, Young), logit noise η, sampling (Young's adaptive play, sample size k).
- **Networks**: the same protocol, applied by each node against its neighbours.

### Parameter schema

Modules declare parameters:

```js
{ id: 'N', label: 'Population size', type: 'int', min: 2, max: 200, default: 50 }
```

Controls are generated from these declarations and bound to the store. No hand-wired sliders.

### Result types

Solvers return typed results that views know how to draw:

- `VectorField`, `Basins`, `RestPoints`
- `StationaryDistribution` (over a 1D or 2D state grid), `StochasticallyStable` (states plus method and limits)
- `TimeSeries`, `NetworkSnapshot`, `Classification`

### Caching and responsiveness

- Key results by `(game, realisation, protocol, noise, population, params)`.
- Render a coarse version while dragging and refine on release (as now).
- Anything over ~100 ms belongs in a pure function that can move to a worker.

### Phase 0 acceptance

No visible change. All current behaviour is reproduced through the new layers. Known-answer tests (§5) run in Node, and the five dynamics derived from protocols match the current `g(x, d)` to 1e-12 on a grid.

## 10. Roadmap after Phase 0

### 10.1 Stochastic stability and stationary distributions

- **Processes:** finite N, one or two populations, protocol + noise.
- **State space:** one population, `N+1` states (birth–death chain); the stationary distribution has a closed form, `μ(i) ∝ Π_{k<i} p⁺(k)/p⁻(k+1)`. Two populations, `(N+1)²` states; use power iteration or a sparse solve (fine at N ≈ 50–100).
- **Stochastic stability:** the ε → 0 limit. Compute it numerically (a sequence of decreasing ε, extrapolating the limiting support) and cross-check with resistances: the minimum number of mistakes needed to leave each basin (Young's radius/coradius, or minimum-resistance trees for more than two absorbing states).
- **View:** a heat map of the stationary distribution on the same square as the phase diagram (a bar chart for one population); stochastically stable states marked; ε, N and the noise model as parameters.
- **Benchmarks to test against** (verify against the literature, and watch finite-N effects):
  - In symmetric 2×2 coordination games, uniform-mistakes models with best response select the risk-dominant equilibrium for large N.
  - Logit selects the potential maximiser, which is risk-dominant in 2×2.
  - Stag Hunt at equal spacing is exactly on the risk-dominance tie, so a payoff slider should flip the selection. Use this as a regression test and as a demonstration.

### 10.2 Supermodularity (strategic complements and substitutes)

- **Interaction terms:**
  - Row: `ΔR = (R_TR − R_BR) − (R_TL − R_BL)`, how Row's advantage for Top changes as Column moves Left → Right.
  - Column: `ΔC = (C_TR − C_TL) − (C_BR − C_BL)`, how Column's advantage for Right changes as Row moves Bottom → Top.
- **Classification:** reversing either player's strategy order flips the sign of both terms, so the game is supermodular under *some* ordering iff `ΔR · ΔC > 0`. This product has the same sign as `αβ` in the replicator Jacobian, so for games without a dominant strategy it separates two-equilibrium games (supermodular) from cyclic games (not). For games with a dominant strategy the sign can depend on payoff values. Treat it as a property of the realisation, not of the ordinal game. Re-derive and test this before relying on it.
- **Deliverables:** a colour mode, an analysis field, and annotations in the dynamics view (monotone convergence of best response in supermodular games; comparative statics).

### 10.3 Games on networks

- **Population:** `network(graph, roles)`. Generators: ring, lattice (with wrap-around), Erdős–Rényi, Watts–Strogatz, two-sided (bipartite) for asymmetric games where Row players meet Column players.
- **Process:** agent-based. Each node revises with a protocol against its neighbours' strategies; synchronous or asynchronous updating; optional noise.
- **Results:** time series of shares, snapshots, absorbing configurations; contagion tests (can a strategy spread from a small seed? compare with Morris' contagion threshold; Ellison's local-interaction results for coordination games).
- **View:** a network drawing coloured by strategy, a share-over-time chart, and Monte Carlo summaries. It probably needs its own page rather than the side panel.

### 10.4 Later

Games with ties (half-swaps, Bruns 2015 preference classes; 726 distinct ordinal games), larger strategy sets, more protocols (sampling, aspiration, reinforcement learning), and an export of results (CSV/JSON).

## 11. Open decisions (ask the user)

- Stochastic and network views: a separate "lab" page opened from the selected game, or more tabs in the side panel? (The panel is already crowded.)
- Default noise model for stochastic stability: uniform mistakes or logit?
- Merge the 3D tori into the dashboard as a page, or keep it standalone with a data copy?
- Keep the dashboard-runtime compatibility (no modules or network) as a hard constraint, or develop locally with modules and a build step that emits the dashboard bundle?

## 12. References

- Robinson, D. and Goforth, D. (2005). *The Topology of the 2×2 Games: A New Periodic Table*. Routledge.
- Bruns, B. (2011). *2×2 Games* chart (2x2chart110602.pdf): the layout, names and Rapoport–Guyer panel used here. www.BryanBruns.com/2x2chart.html
- Bruns, B. R. (2015). Names for Games: Locating 2×2 Games. *Games* 6, 495–520.
- Rapoport, A. and Guyer, M. (1966). A taxonomy of 2×2 games. *General Systems* 11.
- Sandholm, W. H. (2010). *Population Games and Evolutionary Dynamics*. MIT Press. (Revision protocols, mean dynamics, stochastic stability.)
- Kandori, M., Mailath, G. and Rob, R. (1993). Learning, mutation, and long run equilibria in games. *Econometrica* 61.
- Young, H. P. (1993). The evolution of conventions. *Econometrica* 61.
- Ellison, G. (1993). Learning, local interaction, and coordination. *Econometrica* 61.
- Morris, S. (2000). Contagion. *Review of Economic Studies* 67.
- Topkis, D. (1998). *Supermodularity and Complementarity*. Princeton.
