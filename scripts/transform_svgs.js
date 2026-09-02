#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const chartsRoot = path.join(root, 'charts');

const replacements = new Map([
  ['#f3e7cf', '#fbf3de'],
  ['#fbf4e5', '#fff9ed'],
  ['#ddc98f', '#ead49a'],
  ['#1e1b17', '#181a1b'],
  ['#51483d', '#47433b'],
  ['#6a5f51', '#655f53'],
  ['#b8aa91', '#c8b990'],
  ['#194d78', '#0069a6'],
  ['#c84a3a', '#e24832'],
  ['#b53c31', '#b83326'],
  ['#4e7256', '#3a8a5c'],
  ['#b97832', '#e2a228'],
  ['#755a78', '#8d4b8e'],
  ['#c9a64a', '#e0b53a'],
  ['#8faec0', '#8cc7df'],
  ['#d88a73', '#f5a08b'],
  ['#c6d2c1', '#9ed0ab'],
  ['#f3e6c6', '#fbf3de'],
  ['#e2cfa1', '#ead49a'],
  ['#28231b', '#181a1b'],
  ['#594a35', '#47433b'],
  ['#736249', '#655f53'],
  ['#c4a971', '#c8b990'],
  ['#c44530', '#e24832'],
  ['#e48f75', '#f5a08b'],
  ['#006f91', '#0069a6'],
  ['#55b9c1', '#8cc7df'],
  ['#c7e9d8', '#9ed0ab'],
  ['#2f8456', '#3a8a5c'],
  ['#b97a12', '#e2a228'],
  ['#704c99', '#8d4b8e'],
]);

const style = `:root{--paper:#fbf3de;--ink:#181a1b;--muted:#655f53;--rule:#c8b990;--vermilion:#e24832;--aizuri:#0069a6;--rokusho:#3a8a5c;--kuchiba:#e2a228;--fuji:#8d4b8e;--gold:#e0b53a}
*{vector-effect:non-scaling-stroke}
text{font-family:"Source Han Sans SC","Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif;fill:var(--ink)}
.label,.value,.value-light,.big-value,.note,.tick,.axis-title{font-size:12px}
.value,.big-value{font-weight:700;font-variant-numeric:tabular-nums}.big-value{font-size:18px}
.value-light{font-weight:700;fill:var(--paper)}.tick,.axis-title{fill:var(--muted)}
.axis{stroke:var(--ink);stroke-width:1}.grid{stroke:var(--rule);stroke-width:.8;stroke-dasharray:2 5;opacity:.7}
.reference,.stem{stroke:var(--ink);stroke-width:1.1}.red{stroke:var(--vermilion);stroke-width:2.5;stroke-dasharray:8 5}.blue{stroke:var(--aizuri);stroke-width:2.5}.green{stroke:var(--rokusho);stroke-width:2.5;stroke-dasharray:2 4}.gold{stroke:var(--kuchiba);stroke-width:2.5;stroke-dasharray:1 4}
[fill="#0069a6"],[fill="#e24832"],[fill="#3a8a5c"],[fill="#e2a228"],[fill="#8d4b8e"],[fill="#8cc7df"],[fill="#f5a08b"],[fill="#9ed0ab"]{stroke:var(--ink);stroke-width:.65;stroke-linejoin:round;paint-order:stroke fill}
[stroke="#e24832"]{stroke-dasharray:8 5}[stroke="#3a8a5c"]{stroke-dasharray:2 4}[stroke="#e2a228"]{stroke-dasharray:1 4}
path,polyline,line{stroke-linecap:round;stroke-linejoin:round}`;

function walk(dir) {
  return fs.readdirSync(dir, {withFileTypes:true}).flatMap(entry => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? walk(full) : [full];
  });
}

const svgFiles = walk(chartsRoot).filter(file => file.endsWith('.svg') && !file.includes(`${path.sep}en${path.sep}`) && !file.includes(`${path.sep}ja${path.sep}`));
if (svgFiles.length !== 67) throw new Error(`Expected 67 SVGs, found ${svgFiles.length}`);

for (const file of svgFiles) {
  let source = fs.readFileSync(file, 'utf8');
  for (const [from, to] of replacements) source = source.replaceAll(from, to).replaceAll(from.toUpperCase(), to);
  source = source.replace(/<style>[\s\S]*?<\/style>/, `<style>${style}</style><rect class="ukiyo-paper" x="0" y="0" width="360" height="190" fill="#fbf3de"/>`);
  source = source.replace('<svg class="chart-svg"', '<svg class="chart-svg woodblock-chart" data-style="kinpeki-ukiyo"');
  source = source.replace(/<\?xml version='1\.0' encoding='utf-8'\?>/, '<?xml version="1.0" encoding="utf-8"?>');
  fs.writeFileSync(file, source);
}

const manifestPath = path.join(chartsRoot, 'manifest.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
manifest.project = 'Kinpeki Ukiyo Chart Vocabulary';
manifest.version = '1.0.0';
manifest.design_language = 'Contemporary synthesis inspired by Kano-school kinpeki screens and ukiyo-e woodblock print grammar';
manifest.palette = 'tokens/kinpeki-ukiyo-colors.json';
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');

console.log(`Transformed ${svgFiles.length} SVG charts into the Kinpeki Ukiyo visual grammar.`);
