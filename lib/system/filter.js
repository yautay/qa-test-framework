module.exports = function filterScenarios(scenarios, filter) {
    if (!filter || !Array.isArray(scenarios)) return scenarios || [];

    // Tokeny = dzielimy tylko po SPACJACH
    let tokens = String(filter)
        .split(' ')            // separator to wyłącznie spacja
        .map(t => t.trim())
        .filter(Boolean);      // usuwamy puste ciągi

    if (tokens.length === 0) {
        return scenarios;
    }

    return scenarios.filter(scenario => {
        const label = String(scenario.label || '').toLowerCase();

        // AND – każdy token musi wystąpić w labelu
        return tokens.every(token => {
            return label.includes(token.toLowerCase());
        });
    });
};
