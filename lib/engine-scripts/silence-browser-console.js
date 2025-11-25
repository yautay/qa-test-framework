module.exports = async (page /*, scenario, vp */) => {
    await page.addInitScript(() => {
        const noop = () => {};
        ['log', 'info', 'warn', 'error', 'debug', 'trace'].forEach(fn => {
            try { window.console[fn] = noop; } catch (e) {}
        });
    });
};
