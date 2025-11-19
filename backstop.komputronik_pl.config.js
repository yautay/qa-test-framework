// backstop.komputronik-pl.config.js
const config = require('./config/generate-config');

// Filtrowanie scenariuszy tylko dla "komputronik-pl"
// Upewnij się, że etykiety scenariuszy zawierają ciąg "komputronik-pl"
config.scenarios = config.scenarios.filter(scenario =>
    scenario.label.includes('komputronik-pl')
);
config.paths = {
    ...config.paths,
    engine_scripts: 'tests/komputronik-pl/scripts'
};

module.exports = config;
