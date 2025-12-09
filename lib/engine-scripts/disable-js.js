module.exports = async (page, scenario, vp, isReference) => {
    await page.setJavaScriptEnabled(false);
    console.debug('🚫 JavaScript DISABLED via page.setJavaScriptEnabled(false)');
};