module.exports = function filterScenarios(scenarios, filter) {
    if (!Array.isArray(scenarios)) return [];
    if (!filter) return scenarios;

    console.log(`Total scenarios before filtering: ${scenarios.length}`);

    const tokens = String(filter)
        .trim()
        .split(/\s+/)
        .map(t => t.toLowerCase())
        .filter(Boolean);

    console.log(`Filter tokens:`, tokens);

    if (tokens.length === 0) {
        console.log('No filters applied, returning all scenarios.');
        return scenarios;
    }

    const includeTokens = tokens.filter(t => !(t.startsWith('!')));
    const excludeTokens = tokens
        .filter(t => t.startsWith('!'))
        .map(t => t.slice(1));

    const segmentsOf = str =>
        String(str || '')
            .toLowerCase()
            .split(/\s+/)
            .map(s => s.trim())
            .filter(Boolean);

    const matchesToken = (scenario, token) => {
        const labelSeg = segmentsOf(scenario.label);
        const idSeg = segmentsOf(scenario.id);
        return labelSeg.includes(token) || idSeg.includes(token);
    };

    // 1) apply include tokens (if any)
    let filtered = includeTokens.length
        ? scenarios.filter(s => includeTokens.every(tok => matchesToken(s, tok)))
        : scenarios.slice();

    console.log(`Scenarios after applying include tokens: ${filtered.length}`);

    // 2) apply exclude tokens (remove scenarios containing any exclude token)
    if (excludeTokens.length) {
        filtered = filtered.filter(s => excludeTokens.every(tok => !matchesToken(s, tok)));
    }
    console.log(`Scenarios after applying exclude tokens: ${filtered.length}`);

    console.log(`Total scenarios after filtering: ${filtered.length}`);
    return filtered;
};
