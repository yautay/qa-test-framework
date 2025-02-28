// config/generateConfig.js
const fs = require('fs');
const path = require('path');
const urls = require('./urls');

function loadScenarios(site) {
    const siteDir = path.join(__dirname, '..', 'tests', site);

    // konfiguracja projektu
    const siteConfig = require(path.join(siteDir, 'config.json'));
    const channel = siteConfig.channel;

    let scenarios = [];

    // kontekst testów
    const contexts = fs.readdirSync(siteDir).filter(item => {
        const itemPath = path.join(siteDir, item);
        return fs.statSync(itemPath).isDirectory();
    });

    contexts.forEach(context => {
        const contextDir = path.join(siteDir, context);
        const files = fs.readdirSync(contextDir).filter(file => path.extname(file) === '.json');
        files.forEach(file => {
            const suitePath = path.join(contextDir, file);
            const suiteConfig = require(suitePath);

            let defaultResource = null;
            let suiteScenarios = [];
            if (Array.isArray(suiteConfig)) {
                suiteScenarios = suiteConfig;
            } else if (typeof suiteConfig === 'object' && suiteConfig !== null) {
                defaultResource = suiteConfig.defaultResource || null;
                suiteScenarios = suiteConfig.scenarios || [];
            }

            suiteScenarios.forEach(scenario => {
                scenario.label = scenario.label ? `${context} - ${scenario.label}` : context;

                let { testUrl, referenceUrl } = urls.buildUrl(channel);

                let resource = scenario.resource || defaultResource;
                if (resource) {
                    resource = resource.startsWith('/') ? resource : '/' + resource;
                    testUrl += resource;
                    referenceUrl += resource;
                }

                scenario.url = testUrl;
                scenario.referenceUrl = referenceUrl;
                scenarios.push(scenario);
            });
        });
    });

    return scenarios;
}

const komputronikPl_scenarios = loadScenarios('komputronik_pl');
// const dktr_scenarios = loadScenarios('dktr');
// const b2c_scenarios = loadScenarios('techrol_b2c');

module.exports = {
    id: "backstop_default",
    viewports: [
        { label: "desktop", width: 1200, height: 800 },
        { label: "tablet", width: 768, height: 1024 },
        { label: "mobile", width: 375, height: 667 }
    ],
    scenarios: [
        ...komputronikPl_scenarios,
        // ...dktr_scenarios,
        // ...b2c_scenarios
    ],
    paths: {
        bitmaps_reference: "backstop_data/bitmaps_reference",
        bitmaps_test: "backstop_data/bitmaps_test",
        html_report: "backstop_data/html_report",
        ci_report: "backstop_data/ci_report"
    },
    engine: "puppeteer",
    report: ["CI"],
    debug: false,
    debugWindow: false,
};
