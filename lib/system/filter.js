module.exports = function filterScenarios(scenarios, filter) {
    if (!filter || !Array.isArray(scenarios)) return scenarios || [];
    console.log(`Total scenarios before filtering: ${scenarios.length}`);
    let tokens = String(filter)
        .split(' ')            // separator to wyłącznie spacja
        .map(t => t.trim())
        .filter(Boolean);      // usuwamy puste ciągi

    console.log(`Filter tokens:`, tokens);

    if (tokens.length === 0) {
        console.log('No filters applied, returning all scenarios.');
        return scenarios;
    }

    let filtered = scenarios.filter(scenario => {
        const label = String(scenario.label || '').toLowerCase();

        return tokens.every(token => {
            return label.includes(token.toLowerCase());
        });
    });
    console.log(`Total scenarios after filtering: ${filtered.length}`);
    return filtered;
};
