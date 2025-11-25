// file: config/apply-filter-if-available.js

function applyFilterIfAvailable(scenarios, filter) {
    console.log("Filters: ", filter)
    console.log("Loaded scenarios: ", scenarios.length)

    if (!filter) return scenarios;
    try {
        const filterFn = require('./filter');
        if (typeof filterFn === 'function') {
            return filterFn(scenarios, filter);
        }
    } catch (e) {
        // brak filter.js — fallback na prosty filter: tokeny rozdzielone spacją, wykluczenie prefiksem - lub !
        const groups = String(filter).split(',').map(g => g.trim()).filter(Boolean);
        return scenarios.filter(s => {
            return groups.some(group => {
                const tokens = group.split(/\s+/).filter(Boolean);
                return tokens.every(tok => {
                    const isExclude = tok.startsWith('-') || tok.startsWith('!');
                    const raw = isExclude ? tok.slice(1) : tok;
                    const ok = String(s.label || '').includes(raw);
                    return isExclude ? !ok : ok;
                });
            });
        });
    }
    return scenarios;
}

module.exports = applyFilterIfAvailable;
