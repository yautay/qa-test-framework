module.exports = function filterScenarios(scenarios, filter) {
    if (!filter || !Array.isArray(scenarios)) return scenarios || [];
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

    const filtered = scenarios.filter(scenario => {
        const label = String(scenario.label || '').toLowerCase();
        const labelSegments = label
            .split(/\s+/)
            .map(s => s.trim())
            .filter(Boolean);

        return tokens.every(token => labelSegments.includes(token));
    });

    console.log(`Total scenarios after filtering: ${filtered.length}`);
    return filtered;
};
