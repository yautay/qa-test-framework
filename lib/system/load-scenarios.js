const fs = require('fs');
const path = require('path');
const urls = require('./../../config/urls');

function loadScenarios(site) {
    const siteDir = path.join(__dirname, '..', '..', 'tests', site);
    const testsRootDir = path.join(siteDir, 'tests');

    const siteConfigPath = path.join(siteDir, 'config.json');
    const siteConfig = fs.existsSync(siteConfigPath) ? require(siteConfigPath) : {};
    const channel = siteConfig.channel;

    let scenarios = [];

    if (!fs.existsSync(testsRootDir)) return scenarios;

    const contexts = fs.readdirSync(testsRootDir).filter(item => {
        const itemPath = path.join(testsRootDir, item);
        return fs.statSync(itemPath).isDirectory();
    });

    function processSuiteFile(suitePath, labelPrefix) {
        try {
            delete require.cache[require.resolve(suitePath)];
        } catch (e) {}

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
            scenario.label = scenario.label ? `${labelPrefix} - ${scenario.label}` : labelPrefix;

            let { testUrl, referenceUrl } = urls.buildUrl(channel);

            let resource = scenario.resource || defaultResource;
            if (resource) {
                resource = resource.startsWith('/') ? resource : '/' + resource;
                testUrl += resource;
                referenceUrl += resource;
            }

            scenario.url = testUrl;
            scenario.referenceUrl = referenceUrl;
            scenario.onBeforeScript = scenario.onBeforeScript || './../../lib/engine-scripts/silence-browser-console.js';
            scenarios.push(scenario);
        });
    }

    contexts.forEach(context => {
        const contextDir = path.join(testsRootDir, context);

        const rootFiles = fs.readdirSync(contextDir).filter(file => {
            const filePath = path.join(contextDir, file);
            const ext = path.extname(file).toLowerCase();
            return fs.statSync(filePath).isFile() && (ext === '.json' || ext === '.js');
        });

        rootFiles.forEach(file => {
            processSuiteFile(path.join(contextDir, file), context);
        });

        const subdirs = fs.readdirSync(contextDir).filter(item => {
            const itemPath = path.join(contextDir, item);
            return fs.statSync(itemPath).isDirectory();
        });

        subdirs.forEach(sub => {
            const subDirPath = path.join(contextDir, sub);
            const subFiles = fs.readdirSync(subDirPath).filter(file => {
                const filePath = path.join(subDirPath, file);
                const ext = path.extname(file).toLowerCase();
                return fs.statSync(filePath).isFile() && (ext === '.json' || ext === '.js');
            });

            subFiles.forEach(file => {
                processSuiteFile(path.join(subDirPath, file), `${context}/${sub}`);
            });
        });
    });

    return scenarios;
}

module.exports = loadScenarios;
