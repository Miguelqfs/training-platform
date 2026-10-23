// O OpenSpec valida a estrutura; estas regras completam as convenções da disciplina.
export function validateSpecs(documents) {
  const errors = [];
  const identifiers = new Set();
  if (!documents.length) return ['Nenhuma especificação em vigor encontrada.'];

  for (const { path, text } of documents) {
    const requirements = [...text.matchAll(/^### Requirement: (.+)\r?$/gm)];
    if (!requirements.length) errors.push(`${path}: nenhum requisito encontrado.`);
    for (const [index, requirement] of requirements.entries()) {
      const title = requirement[1].trim();
      const identifier = title.match(/^(RF\d{2,}|NF-[A-Z]{3}-\d{2,}) — \S.*$/)?.[1];
      const end = requirements[index + 1]?.index ?? text.length;
      const block = text.slice(requirement.index, end);
      const label = `${path}: ${identifier ?? title}`;
      if (!identifier) errors.push(`${label}: use ID e título no formato da disciplina.`);
      else if (identifiers.has(identifier)) errors.push(`${label}: ID duplicado nas specs em vigor.`);
      else identifiers.add(identifier);

      if (!/^\*\*Prioridade:\*\* (Essencial|Importante|Desejável)\s*$/m.test(block)) {
        errors.push(`${label}: prioridade ausente ou inválida.`);
      }
      if (!/^\*\*Casos? de uso:\*\* UC\d{2,}(?:, UC\d{2,})*\s*$/m.test(block)) {
        errors.push(`${label}: informe os casos de uso no formato UCnn.`);
      }
    }
  }
  return errors;
}
