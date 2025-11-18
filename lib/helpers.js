function normalizeXPath(xpath) {
    return xpath.startsWith('xpath=') ? xpath : `xpath=${xpath}`;
}

async function isVisibleXPath(page, xpath, timeout = 10000) {
    const selector = normalizeXPath(xpath);

    try {
        await page.waitForSelector(selector, { timeout });
        console.log('element pojawił się:', selector);

        await page.locator(selector).waitFor({ state: 'visible', timeout });
        return true;
    } catch (err) {
        console.log('element nie pojawił się lub nie jest widoczny:', err.message);
        return false;
    }
}

async function clickXPath(page, xpath, timeout = 10000) {
    const selector = normalizeXPath(xpath);

    if (!await isVisibleXPath(page, xpath, timeout)) {
        return false;
    }

    try {
        await page.locator(selector).click({ timeout });
        console.log(`>>> Clicked XPath: ${xpath}`);
        return true;
    } catch (e) {
        console.log(`>>> XPath not clickable: ${xpath}`);
        return false;
    }
}

module.exports = {
    clickXPath,
    isVisibleXPath
};