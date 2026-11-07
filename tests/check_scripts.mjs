// Parse-check every inline <script> in the HTML pages without running them.
// Usage: node tests/check_scripts.mjs
import { readFileSync } from 'node:fs';
const files = ['dashboard/index.html'];
let failed = 0;
for (const f of files) {
  const html = readFileSync(new URL('../' + f, import.meta.url), 'utf8');
  const blocks = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  blocks.forEach((code, i) => {
    try { new Function(code); console.log('ok   ', f, 'script', i + 1); }
    catch (err) { failed++; console.error('FAIL ', f, 'script', i + 1, '-', err.message); }
  });
}
process.exit(failed ? 1 : 0);
