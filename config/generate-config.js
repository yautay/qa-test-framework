// config/generate-config.js
const fs = require('fs');
const path = require('path');
const urls = require('./urls');
const findChrome = require('../lib/find-chrome');
const chromePath = findChrome();

function loadScenarios(site) {
    const siteDir = path.join(__dirname, '..', 'tests', site);
    const testsRootDir = path.join(siteDir, 'tests');

    const siteConfig = require(path.join(siteDir, 'config.json'));
    const channel = siteConfig.channel;

    let scenarios = [];

    const contexts = fs.readdirSync(testsRootDir).filter(item => {
        const itemPath = path.join(testsRootDir, item);
        return fs.statSync(itemPath).isDirectory();
    });

    contexts.forEach(context => {
        const contextDir = path.join(testsRootDir, context);

        // zaakceptuj .json i .js
        const files = fs.readdirSync(contextDir).filter(file => {
            const ext = path.extname(file).toLowerCase();
            return ext === '.json' || ext === '.js';
        });

        files.forEach(file => {
            const suitePath = path.join(contextDir, file);

            try {
                delete require.cache[require.resolve(suitePath)];
            } catch (e) {
                // ignore if not resolvable
            }

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

                let {testUrl, referenceUrl} = urls.buildUrl(channel);

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


const komputronikPl_scenarios = loadScenarios('komputronik-pl');
// const dktr_scenarios = loadScenarios('dktr');
// const b2c_scenarios = loadScenarios('techrol_b2c');

const baseArgs = [
    '--no-sandbox',
    '--disable-web-security',
    '--allow-running-insecure-content',
    '--disable-features=IsolateOrigins,site-per-process'
];

module.exports = {
    id: "backstop_default",
    viewports: [
        {label: "desktop", width: 1920, height: 1080},
        {label: "tabletL", width: 1200, height: 800},
        {label: "tabletM", width: 768, height: 1024},
        {label: "mobile", width: 375, height: 667}
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
    engine: "playwright",
    engineOptions: chromePath
        ? {
            executablePath: chromePath,
            headless: true,
            args: baseArgs
        }
        : {
            launchOptions: {
                channel: 'chrome',
                headless: true,
                args: baseArgs
            }
        },
    report: ["CI"],
    debug: false,
    debugWindow: false,
};
