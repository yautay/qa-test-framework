function normalizeXPath(xpath) {
    return xpath.startsWith('xpath=') ? xpath : `xpath=${xpath}`;
}

async function isVisibleXPath(page, xpath, timeout = 5000) {
    try {
        const selector = normalizeXPath(xpath);
        const locator = page.locator(selector);
        await locator.waitFor({ state: 'visible', timeout });
        return true;
    } catch (e) {
        return false;
    }
}

async function clickXPath(page, xpath, timeout = 0) {
    console.log(`>>> Trying to click XPath: ${xpath}`);

    const visible = await isVisibleXPath(page, xpath);
    if (!visible) {
        console.log(`>>> XPath not visible: ${xpath}`);
        return false;
    }

    try {
        const selector = normalizeXPath(xpath);
        const locator = page.locator(selector);
        await locator.click({ timeout });
        console.log(`>>> Clicked XPath: ${xpath}`);
        return true;
    } catch (e) {
        console.log(`>>> XPath not clickable after visible: ${xpath}`);
        return false;
    }
}

module.exports = {
    clickXPath,
    isVisibleXPath
};