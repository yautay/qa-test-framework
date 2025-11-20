function isXPath(selector) {
    return selector.startsWith('//') || selector.startsWith('.//');
}

function normalizeSelector(selector) {
    if (isXPath(selector)) {
        return selector.startsWith('xpath=') ? selector : `xpath=${selector}`;
    }

    return selector;
}

async function isVisible(page, selector, timeout = 10000) {
    const norm = normalizeSelector(selector);

    try {
        await page.waitForSelector(norm, { timeout });
        await page.locator(norm).waitFor({ state: 'visible', timeout });
        console.log('Element visible:', norm);
        return true;
    } catch (err) {
        console.log('Element not visible:', norm, err.message);
        return false;
    }
}

async function click(page, selector, timeout = 10000) {
    const norm = normalizeSelector(selector);

    if (!await isVisible(page, selector, timeout)) {
        console.log(`Element not visible: ${selector}`);
        return false;
    }

    try {
        await page.locator(norm).click({ timeout });
        console.log(`>>> Clicked: ${selector}`);
        return true;
    } catch (err) {
        console.log(`>>> Is element clickable? No: ${selector}, error: ${err.message}`);
        return false;
    }
}

module.exports = {
    isVisible,
    click
};
