module.exports = {
    scenarios: [
        {
            label: "komputronik-pl listings producer-category-listing apple html_cache",
            resource: "/category/5022/laptopy,apple.html",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings producer-category-listing apple no_html_cache",
            resource: "/category/5022/laptopy,apple.html?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        },
        {
            label: "komputronik-pl listings producer-category-listing apple disabled-js",
            resource: "/category/5022/laptopy,apple.html?test=1",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
        },
        {
            label: "komputronik-pl listings producer-category-listing apple no_html_cache",
            resource: "/category/5022/laptopy,apple.html?p=2",
            selectors: [],
            delay: 500,
            misMatchThreshold: 1,
            requireSameDimensions: true,
            report: ["browser"],
            onReadyScript: "./../../tests/komputronik-pl/scripts/close-cookies.js"
        }
    ]
};
