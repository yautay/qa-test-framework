// backstop.komputronik_pl.config.js
const config = require('./config/generateConfig');

// Filtrowanie scenariuszy tylko dla "komputronik_pl"
// Upewnij się, że etykiety scenariuszy zawierają ciąg "komputronik_pl"
config.scenarios = config.scenarios.filter(scenario =>
    scenario.label.includes('komputronik_pl')
);

module.exports = config;
