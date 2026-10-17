export function positive(raw) {
    if (raw.trim() === '')
        return null;
    const value = Number(raw);
    return Number.isFinite(value) && value > 0 ? value : null;
}
function checked(value) {
    if (!Number.isFinite(value) || value <= 0)
        throw new RangeError('The result is outside the supported numeric range.');
    return value;
}
export function concentration(amount, volume) {
    if (!Number.isFinite(amount) || amount <= 0 || !Number.isFinite(volume) || volume <= 0)
        throw new RangeError('Enter positive, finite values.');
    const value = checked(amount / volume);
    const mcg = checked(value * 1000);
    return { value, unit: 'mg/mL', secondary: `${format(mcg)} mcg/mL`, formula: `${format(amount)} mg ÷ ${format(volume)} mL = ${format(value)} mg/mL; ${format(value)} mg/mL × 1,000 = ${format(mcg)} mcg/mL` };
}
export function volume(amount, target) {
    if (!Number.isFinite(amount) || amount <= 0 || !Number.isFinite(target) || target <= 0)
        throw new RangeError('Enter positive, finite values.');
    const value = checked(amount / target);
    return { value, unit: 'mL', formula: `${format(amount)} mg ÷ ${format(target)} mg/mL = ${format(value)} mL (theoretical mathematical volume)` };
}
export function convert(value, from) {
    if (!Number.isFinite(value) || value <= 0)
        throw new RangeError('Enter a positive, finite value.');
    const factors = {
        mg: { factor: 1000, to: 'mcg', label: '× 1,000' },
        mcg: { factor: 0.001, to: 'mg', label: '÷ 1,000' },
        mL: { factor: 1000, to: 'µL', label: '× 1,000' },
        uL: { factor: 0.001, to: 'mL', label: '÷ 1,000' },
    };
    const rule = factors[from];
    if (!rule)
        throw new RangeError('Unsupported unit.');
    const output = checked(value * rule.factor);
    const source = from === 'uL' ? 'µL' : from;
    return { value: output, unit: rule.to, formula: `${format(value)} ${source} ${rule.label} = ${format(output)} ${rule.to}` };
}
export function format(value) {
    return new Intl.NumberFormat('en-US', { maximumSignificantDigits: 10 }).format(value);
}
function init() {
    document.querySelectorAll('[data-bac]').forEach((root) => {
        const kind = root.dataset.bac;
        const inputs = Array.from(root.querySelectorAll('input'));
        const select = root.querySelector('select');
        const result = root.querySelector('[data-result]');
        const formula = root.querySelector('[data-formula]');
        const secondary = root.querySelector('[data-secondary]');
        const error = root.querySelector('.bac-error');
        const copy = root.querySelector('[data-copy]');
        const status = root.querySelector('[data-copy-status]');
        const initialFormula = formula.textContent || '';
        let copyText = '';
        function update() {
            status.textContent = '';
            error.textContent = '';
            inputs.forEach((input) => input.removeAttribute('aria-invalid'));
            copy.disabled = true;
            copyText = '';
            result.textContent = '—';
            formula.textContent = initialFormula;
            if (secondary)
                secondary.textContent = '— mcg/mL';
            const invalid = inputs.filter((input) => input.value.trim() !== '' && positive(input.value) === null);
            if (invalid.length) {
                invalid.forEach((input) => input.setAttribute('aria-invalid', 'true'));
                error.textContent = 'Enter positive, finite numbers greater than zero.';
                return;
            }
            if (inputs.some((input) => input.value.trim() === ''))
                return;
            const values = inputs.map((input) => positive(input.value));
            try {
                const a = values[0];
                const b = values[1];
                const calculated = kind === 'concentration' ? concentration(a, b) : kind === 'volume' ? volume(a, b) : convert(a, select.value);
                result.textContent = `${format(calculated.value)} ${calculated.unit}`;
                formula.textContent = calculated.formula;
                if (secondary)
                    secondary.textContent = calculated.secondary || '';
                copyText = `${kind === 'volume' ? 'Theoretical volume' : kind === 'concentration' ? 'Concentration' : 'Conversion'}: ${result.textContent}${calculated.secondary ? `; ${calculated.secondary}` : ''}. ${calculated.formula}`;
                copy.disabled = false;
            }
            catch (cause) {
                inputs.forEach((input) => input.setAttribute('aria-invalid', 'true'));
                error.textContent = cause instanceof Error ? cause.message : 'Invalid calculation.';
            }
        }
        inputs.forEach((input) => input.addEventListener('input', update));
        select?.addEventListener('change', update);
        root.querySelector('[data-reset]').addEventListener('click', () => {
            inputs.forEach((input) => { input.value = ''; });
            if (select)
                select.selectedIndex = 0;
            update();
            inputs[0]?.focus();
        });
        copy.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(copyText);
                status.textContent = 'Result copied.';
            }
            catch {
                status.textContent = 'Copy failed. Select the displayed result to copy it.';
            }
        });
        update();
    });
}
if (typeof document !== 'undefined')
    init();
