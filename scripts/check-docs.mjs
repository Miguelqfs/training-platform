import { execFileSync, spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { validateSpecs } from './check-specs.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const tools = process.env.DOCS_TOOLS_DIR;
if (!tools) {
  console.error('Defina DOCS_TOOLS_DIR conforme as instruções do README.');
  process.exit(1);
}
const require = createRequire(import.meta.url);
const { parse } = require(join(resolve(tools), 'yaml'));
const errors = [];
const nonempty = (value) => typeof value === 'string' && value.trim().length > 0;

try {
  const config = parse(readFileSync(join(root, 'openspec/config.yaml'), 'utf8'));
  if (config?.schema !== 'spec-driven') errors.push('schema deve ser spec-driven');
  if (!nonempty(config?.context)) errors.push('context deve ser texto não vazio');
  for (const artifact of ['proposal', 'specs', 'design', 'tasks']) {
    const rules = config?.rules?.[artifact];
    if (!Array.isArray(rules) || !rules.length || !rules.every(nonempty)) {
      errors.push(`rules.${artifact} deve ser lista não vazia de textos`);
    }
  }
} catch (error) {
  errors.push(`Configuração YAML inválida: ${error.message}`);
}

const files = new Set(execFileSync('git', [
  'ls-files', '--cached', '--others', '--exclude-standard', '-z',
], { cwd: root, encoding: 'utf8' }).split('\0').filter(Boolean));
const specs = [...files]
  .filter(file => file.startsWith('openspec/specs/') && file.endsWith('/spec.md') && existsSync(join(root, file)))
  .map(path => ({ path, text: readFileSync(join(root, path), 'utf8') }));
errors.push(...validateSpecs(specs));
let documents = 0;
for (const file of files) {
  const path = join(root, file);
  if (!file.endsWith('.md') || !existsSync(path)) continue;
  documents += 1;
  const markdown = readFileSync(path, 'utf8').replace(/^(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\1\s*$/gm, '');
  for (const match of markdown.matchAll(/!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)/g)) {
    const target = match[1].replace(/^<|>$/g, '');
    if (/^(?:[a-z][a-z0-9+.-]*:|#|\/\/)/i.test(target)) continue;
    try {
      const local = decodeURIComponent(target.split(/[?#]/)[0]);
      if (local && !existsSync(resolve(dirname(path), local))) {
        errors.push(`${file}: link local ausente: ${target}`);
      }
    } catch {
      errors.push(`${file}: link local inválido: ${target}`);
    }
  }
}
if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(`YAML e metadados das specs válidos; links locais de ${documents} documentos conferidos.`);
const result = spawnSync(join(resolve(tools), '.bin/openspec'), ['validate', '--all'], {
  cwd: root, stdio: 'inherit', env: { ...process.env, CI: 'true', OPENSPEC_TELEMETRY: '0' },
});
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);
