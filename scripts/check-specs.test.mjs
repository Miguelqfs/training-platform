import assert from 'node:assert/strict';
import test from 'node:test';

import { validateSpecs } from './check-specs.mjs';

const valid = `# Capacidade
## Purpose
Explicar a capacidade.
## Requirements
### Requirement: RF08 — Cadastrar treino
O sistema DEVE cadastrar um treino.
**Prioridade:** Essencial
**Caso de uso:** UC03
#### Scenario: Cadastro válido
- **GIVEN** um usuário
- **WHEN** cadastra um treino
- **THEN** registra 1 treino
`;
const document = (text, path = 'treinos/spec.md') => ({ text, path });

test('aceita metadados da disciplina e múltiplos casos de uso', () => {
  const text = valid.replace('**Caso de uso:** UC03', '**Casos de uso:** UC03, UC04');
  assert.deepEqual(validateSpecs([document(text)]), []);
});

test('aceita título curto sem impor um tamanho novo', () => {
  assert.deepEqual(validateSpecs([document(valid.replace('Cadastrar treino', 'X'))]), []);
});

test('aceita IDs não funcionais e prioridades previstas', () => {
  for (const priority of ['Essencial', 'Importante', 'Desejável']) {
    const text = valid.replace('RF08', 'NF-CON-05').replace('Essencial', priority);
    assert.deepEqual(validateSpecs([document(text)]), []);
  }
});

test('rejeita árvore sem specs e documento sem requisitos', () => {
  assert.match(validateSpecs([]).join('\n'), /Nenhuma especificação/);
  assert.match(validateSpecs([document('# Vazio')]).join('\n'), /nenhum requisito/);
});

test('rejeita requisito sem ID e ID duplicado em capacidades diferentes', () => {
  assert.match(validateSpecs([document(valid.replace('RF08 — ', ''))]).join('\n'), /use ID e título/);
  const errors = validateSpecs([document(valid), document(valid, 'outro/spec.md')]);
  assert.match(errors.join('\n'), /ID duplicado/);
});

test('rejeita prioridade ausente ou fora do vocabulário', () => {
  for (const text of [valid.replace('**Prioridade:** Essencial', ''), valid.replace('Essencial', 'Alta')]) {
    assert.match(validateSpecs([document(text)]).join('\n'), /prioridade ausente ou inválida/);
  }
});

test('rejeita caso de uso ausente ou malformado', () => {
  for (const text of [valid.replace('**Caso de uso:** UC03', ''), valid.replace('UC03', 'UC3')]) {
    assert.match(validateSpecs([document(text)]).join('\n'), /casos de uso/);
  }
});
