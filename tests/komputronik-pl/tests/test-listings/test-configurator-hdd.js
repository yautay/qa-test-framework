module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings configurator configurator-hdd html_cache",
            resource: "/advanced-configurator/hdd",
            selectors: [],
            delay: 3000,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },

        {
            label: "komputronik-pl listings configurator configurator-hdd no_html_cache",
            resource: "/advanced-configurator/hdd?test=1",
            selectors: [],
            delay: 3000,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};

