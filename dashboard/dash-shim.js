/* dash-shim.js: a minimal local stand-in for the claude.ai dashboard runtime.
 *
 * The published page (index.html) talks to its host only through:
 *   dash.calc(id, { inputs, title, description, fn })  -> registers a derived table
 *   dash.data(id) -> { status, data }                   -> status: loading | ok | error | missing
 *   dash.onData(callback)                               -> called on load, data change and resize
 * This shim implements exactly that, loading datasets from local JSON files.
 * Keep the page free of anything the real runtime doesn't provide.
 */
(function () {
  const DATASETS = { games: '../data/games-2x2.json' };
  const store = {};
  const calcs = new Map();
  const callbacks = [];

  Object.keys(DATASETS).forEach((id) => { store[id] = { status: 'loading', data: null }; });

  function computeCalcs() {
    for (const [id, def] of calcs) {
      const inputs = (def.inputs || []).map((i) => store[i] || { status: 'missing', data: null });
      if (inputs.every((s) => s.status === 'ok')) {
        try { store[id] = { status: 'ok', data: def.fn(...inputs.map((s) => s.data)) }; }
        catch (err) { console.error('dash.calc ' + id + ' failed:', err); store[id] = { status: 'error', data: null }; }
      } else {
        store[id] = { status: inputs.some((s) => s.status === 'error') ? 'error' : 'loading', data: null };
      }
    }
  }
  function fire() {
    computeCalcs();
    callbacks.forEach((cb) => { try { cb(); } catch (err) { console.error('dash.onData callback threw:', err); } });
  }

  window.dash = {
    calc(id, def) { calcs.set(id, def); store[id] = { status: 'loading', data: null }; },
    data(id) { return store[id] || { status: 'missing', data: null }; },
    onData(cb) { callbacks.push(cb); try { cb(); } catch (err) { console.error(err); } },
    setParams() { /* no parameters are used by this page yet */ },
    params() { return {}; },
  };

  Object.entries(DATASETS).forEach(([id, url]) => {
    fetch(url).then((r) => { if (!r.ok) throw new Error(r.status + ' ' + url); return r.json(); })
      .then((rows) => { store[id] = { status: 'ok', data: rows }; fire(); })
      .catch((err) => { console.error('Could not load dataset ' + id + ':', err); store[id] = { status: 'error', data: null }; fire(); });
  });

  let t = null;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(fire, 150); });
})();
