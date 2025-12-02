module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings producer-category-listing asus html_cache",
            resource: "/category/1251/monitory,asus.html",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },

        {
            label: "komputronik-pl listings producer-category-listing asus no_html_cache",
            resource: "/category/1251/monitory,asus.html?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};

