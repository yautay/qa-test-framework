module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings configurator configurator-main html_cache smoke",
            resource: "/advanced-configurator",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-main no_html_cache",
            resource: "/advanced-configurator?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-main disabled-js",
            resource: "/advanced-configurator",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"]
        }
    ]
};
