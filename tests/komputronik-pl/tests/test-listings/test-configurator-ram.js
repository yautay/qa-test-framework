module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings configurator configurator-ram html_cache",
            resource: "/advanced-configurator/dram_memory",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-ram no_html_cache",
            resource: "/advanced-configurator/dram_memory?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings configurator configurator-ram disabled-js",
            resource: "/advanced-configurator/dram_memory",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"]
        }
    ]
};
