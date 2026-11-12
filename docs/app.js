try {
    // Formatters
    const formatMoney = (val) => (val === -1 || val == null) ? 'N/A' : new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
    const formatPct = (val) => (val === -1 || val == null) ? 'N/A' : val.toFixed(1) + '%';
    const formatScore = (val) => (val === -999 || val == null) ? 'N/A' : val.toFixed(2);

    // State
    let filtered = [...districtsData];
    let sortCol = 'Current_3BR_Price_Mean';
    let sortAsc = true;
    let selected = [];

    // DOM Elements
    const tbody = document.getElementById('table-body');
    const resultCount = document.getElementById('result-count');
    const compareBtn = document.getElementById('compare-btn');
    const modal = document.getElementById('compare-modal');
    const closeModal = document.getElementById('close-modal');
    const compareGrid = document.getElementById('comparison-grid');

    // Inputs
    const filters = {
        abs: document.getElementById('filter-abs'),
        growth: document.getElementById('filter-growth'),
        asian: document.getElementById('filter-asian'),
        ba: document.getElementById('filter-ba'),
        dem: document.getElementById('filter-dem'),
        price: document.getElementById('filter-price'),
        commute: document.getElementById('filter-commute')
    };

    // Value displays
    const displays = {
        abs: document.getElementById('val-abs'),
        growth: document.getElementById('val-growth'),
        asian: document.getElementById('val-asian'),
        ba: document.getElementById('val-ba'),
        dem: document.getElementById('val-dem'),
        price: document.getElementById('val-price'),
        commute: document.getElementById('val-commute')
    };

    const keyToCol = {
        abs: 'SEDA_Absolute_Score',
        growth: 'SEDA_Growth_Score',
        asian: 'perasn',
        ba: 'baplusavgall',
        dem: 'Dem_Vote_Share_2020',
        price: 'Current_3BR_Price_Mean',
        commute: 'Drive_Mins_To_Manhattan'
    };

    function getPctileStr(col, value) {
        if (value == null || isNaN(value)) return '';
        let valid = districtsData.filter(d => d[col] != null && d[col] !== -999 && d[col] !== -1 && d[col] !== 999);
        if (valid.length === 0) return '';
        let count = valid.filter(d => d[col] <= value).length;
        let pct = Math.round((count / valid.length) * 100);
        
        let suffix = 'th';
        if (pct % 10 === 1 && pct % 100 !== 11) suffix = 'st';
        else if (pct % 10 === 2 && pct % 100 !== 12) suffix = 'nd';
        else if (pct % 10 === 3 && pct % 100 !== 13) suffix = 'rd';
        
        return ` | ${pct}${suffix} Pctile`;
    }

    function updateLabel(key, val) {
        let displayVal = key === 'price' ? Number(val).toLocaleString() : val;
        displays[key].innerText = `${displayVal}${getPctileStr(keyToCol[key], val)}`;
    }

    // Initialize
    function init() {
        // Add input listeners
        Object.keys(filters).forEach(key => {
            // Set initial label
            updateLabel(key, parseFloat(filters[key].value));
            
            filters[key].addEventListener('input', (e) => {
                updateLabel(key, parseFloat(e.target.value));
                applyFilters();
            });
        });

        // Add sort listeners
        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                const col = th.getAttribute('data-sort');
                if (sortCol === col) sortAsc = !sortAsc;
                else {
                    sortCol = col;
                    sortAsc = true;
                }
                renderTable();
            });
        });

        // Add compare listener
        compareBtn.addEventListener('click', openCompareModal);
        closeModal.addEventListener('click', () => modal.classList.add('hidden'));

        applyFilters();
    }

    function applyFilters() {
        try {
            const f_abs = parseFloat(filters.abs.value);
            const f_growth = parseFloat(filters.growth.value);
            const f_asian = parseFloat(filters.asian.value);
            const f_ba = parseFloat(filters.ba.value);
            const f_dem = parseFloat(filters.dem.value);
            const f_price = parseFloat(filters.price.value);
            const f_commute = parseFloat(filters.commute.value);

            filtered = districtsData.filter(d => {
                // Pin selected districts to bypass filters
                if (selected.includes(d.sedaadmin)) return true;

                if (d.SEDA_Absolute_Score != null && d.SEDA_Absolute_Score !== -999 && d.SEDA_Absolute_Score < f_abs) return false;
                if (d.SEDA_Growth_Score != null && d.SEDA_Growth_Score !== -999 && d.SEDA_Growth_Score < f_growth) return false;
                if (d.perasn != null && d.perasn !== -1 && d.perasn < f_asian) return false;
                if (d.baplusavgall != null && d.baplusavgall !== -1 && d.baplusavgall < f_ba) return false;
                if (d.Dem_Vote_Share_2020 != null && d.Dem_Vote_Share_2020 !== -1 && d.Dem_Vote_Share_2020 < f_dem) return false;
                if (d.Current_3BR_Price_Mean != null && d.Current_3BR_Price_Mean !== -1 && d.Current_3BR_Price_Mean > f_price) return false;
                if (d.Drive_Mins_To_Manhattan != null && d.Drive_Mins_To_Manhattan !== 999 && d.Drive_Mins_To_Manhattan > f_commute) return false;
                return true;
            });

            resultCount.innerText = filtered.length;
            renderTable();
        } catch(e) {
            document.querySelector('.table-container').innerHTML = `<div style="color:red; padding: 20px;">Error in applyFilters: ${e.message}</div>`;
        }
    }

    function renderTable() {
        try {
            filtered.sort((a, b) => {
                const aSelected = selected.includes(a.sedaadmin);
                const bSelected = selected.includes(b.sedaadmin);
                
                if (aSelected && !bSelected) return -1;
                if (!aSelected && bSelected) return 1;

                let valA = a[sortCol];
                let valB = b[sortCol];
                if (valA === valB) return 0;
                let diff = valA > valB ? 1 : -1;
                return sortAsc ? diff : -diff;
            });

            tbody.innerHTML = '';
            filtered.forEach(d => {
                const tr = document.createElement('tr');
                const isSelected = selected.includes(d.sedaadmin);
                
                tr.innerHTML = `
                    <td class="checkbox-cell">
                        <input type="checkbox" value="${d.sedaadmin}" ${isSelected ? 'checked' : ''}>
                    </td>
                    <td><strong>${d.District_Name}</strong></td>
                    <td>${formatMoney(d.Current_3BR_Price_Mean)}</td>
                    <td>${formatScore(d.SEDA_Absolute_Score)}</td>
                    <td>${formatPct(d.perasn)}</td>
                    <td>${formatPct(d.baplusavgall)}</td>
                    <td>${formatPct(d.Dem_Vote_Share_2020)}</td>
                    <td>${d.Drive_Mins_To_Manhattan === 999 || d.Drive_Mins_To_Manhattan == null ? 'N/A' : d.Drive_Mins_To_Manhattan + 'm'}</td>
                `;

                const cb = tr.querySelector('input');
                cb.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        if (selected.length >= 5) {
                            e.target.checked = false;
                            alert("You can only compare up to 5 districts at a time.");
                            return;
                        }
                        selected.push(d.sedaadmin);
                    } else {
                        selected = selected.filter(id => id !== d.sedaadmin);
                    }
                    updateCompareBtn();
                    // Re-render table so the row jumps to the pinned section or unpins immediately
                    applyFilters();
                });

                tbody.appendChild(tr);
            });
        } catch(e) {
            document.querySelector('.table-container').innerHTML = `<div style="color:red; padding: 20px;">Error in renderTable: ${e.message}</div>`;
        }
    }

    function updateCompareBtn() {
        compareBtn.innerText = `Compare Selected (${selected.length})`;
        compareBtn.disabled = selected.length === 0;
    }

    function openCompareModal() {
        if (selected.length === 0) return;
        
        const buildCard = (d) => `
            <div class="compare-card">
                <h3>${d.District_Name}</h3>
                
                <div class="stat-row">
                    <span class="stat-label">Average 3BR Home Price</span>
                    <span class="stat-value">${formatMoney(d.Current_3BR_Price_Mean)}</span>
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">SEDA Absolute Proficiency (Growth)</span>
                    <span class="stat-value">${formatScore(d.SEDA_Absolute_Score)} (${formatScore(d.SEDA_Growth_Score)})</span>
                </div>

                <div class="stat-row">
                    <span class="stat-label">Niche Grades</span>
                    <span class="stat-value">K8: ${d.Niche_K8_Grade || 'N/A'} | HS: ${d.Niche_HS_Grade || 'N/A'}</span>
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">% Asian / % White</span>
                    <span class="stat-value">${formatPct(d.perasn)} / ${formatPct(d.perwht)}</span>
                </div>

                <div class="stat-row">
                    <span class="stat-label">% Bachelor's Degree or Higher</span>
                    <span class="stat-value">${formatPct(d.baplusavgall)}</span>
                </div>

                <div class="stat-row">
                    <span class="stat-label">Democratic Vote Share (2020)</span>
                    <span class="stat-value">${formatPct(d.Dem_Vote_Share_2020)}</span>
                </div>

                <div class="stat-row">
                    <span class="stat-label">Drive to Manhattan</span>
                    <span class="stat-value">${d.Drive_Mins_To_Manhattan === 999 || d.Drive_Mins_To_Manhattan == null ? 'N/A' : d.Drive_Mins_To_Manhattan + ' mins'}</span>
                </div>
            </div>
        `;

        const cardsHtml = selected.map(id => {
            const d = districtsData.find(district => district.sedaadmin === id);
            return buildCard(d);
        }).join('');

        compareGrid.innerHTML = cardsHtml;
        modal.classList.remove('hidden');
    }

    init();

} catch (err) {
    document.body.innerHTML = `<h1 style="color:red; padding:2rem;">FATAL ERROR: ${err.message}</h1><pre style="padding:2rem;">${err.stack}</pre>`;
}
