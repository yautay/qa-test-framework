module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings configurator configurator-cpu html_cache",
            resource: "/advanced-configurator/cpu",
            selectors: [],
            delay: 3000,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },

        {
            label: "komputronik-pl listings configurator configurator-cpu no_html_cache",
            resource: "/advanced-configurator/cpu?test=1",
            selectors: [],
            delay: 3000,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};

