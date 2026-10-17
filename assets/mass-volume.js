export function convertMassVolume(direction, value, unit, basis, rate) {
  if (![value, rate].every(n => Number.isFinite(n) && n > 0)) throw new RangeError('Enter positive, finite numbers greater than zero.');
  if (!['concentration', 'density'].includes(basis)) throw new RangeError('Choose a valid relationship.');
  if (!['mass-to-volume', 'volume-to-mass'].includes(direction)) throw new RangeError('Choose a valid calculation.');
  if (!['mg', 'g'].includes(unit)) throw new RangeError('Choose mg or g.');
  const massRate = basis === 'concentration' ? rate : rate * 1000;
  const result = direction === 'mass-to-volume' ? (unit === 'g' ? value * 1000 : value) / massRate : value * massRate / (unit === 'g' ? 1000 : 1);
  if (!Number.isFinite(result) || result <= 0) throw new RangeError('The result is outside the supported numeric range.');
  return result;
}

const root = document.querySelector('[data-mass-volume]');
if (root) {
  const direction = root.querySelector('#mv-direction');
  const value = root.querySelector('#mv-value');
  const unit = root.querySelector('#mv-unit');
  const basis = root.querySelector('#mv-basis');
  const rate = root.querySelector('#mv-rate');
  const rateLabel = root.querySelector('#mv-rate-label');
  const rateHint = root.querySelector('#mv-rate-hint');
  const result = root.querySelector('#mv-result');
  const formula = root.querySelector('#mv-formula');
  const error = root.querySelector('#mv-error');
  const fmt = n => new Intl.NumberFormat('en-US', { maximumSignificantDigits: 10 }).format(n);
  function update() {
    const reverse = direction.value === 'volume-to-mass';
    const density = basis.value === 'density';
    unit.disabled = reverse;
    unit.hidden = reverse;
    rateLabel.textContent = density ? 'Density (g/mL)' : 'Concentration (mg/mL)';
    rateHint.textContent = density ? 'Use the density for the exact pure liquid and conditions.' : 'For example, 5 mg/mL means each 1 mL contains 5 mg of the substance.';
    error.hidden = true;
    value.removeAttribute('aria-invalid');
    rate.removeAttribute('aria-invalid');
    if (!value.value || !rate.value) { result.textContent = '—'; formula.textContent = 'Enter an amount and a known concentration or density.'; return; }
    try {
      const amount = Number(value.value), known = Number(rate.value);
      const output = convertMassVolume(direction.value, amount, unit.value, basis.value, known);
      const rateUnit = density ? 'g/mL' : 'mg/mL';
      result.textContent = `${fmt(output)} ${reverse ? 'mg' : 'mL'}`;
      const amountText = reverse ? `${fmt(amount)} mL` : `${fmt(amount)} ${unit.value}`;
      const massText = !reverse && unit.value === 'g' ? `${fmt(amount * 1000)} mg` : amountText;
      const rateText = density ? `${fmt(known * 1000)} mg/mL` : `${fmt(known)} mg/mL`;
      formula.textContent = reverse
        ? `${amountText} × ${rateText} = ${fmt(output)} mg${density ? ` (${fmt(known)} ${rateUnit})` : ''}`
        : `${massText} ÷ ${rateText} = ${fmt(output)} mL${density ? ` (${fmt(known)} ${rateUnit})` : ''}`;
    } catch (cause) {
      result.textContent = '—'; formula.textContent = 'Check the entered values.';
      error.textContent = cause.message; error.hidden = false;
      if (!Number.isFinite(Number(value.value)) || Number(value.value) <= 0) value.setAttribute('aria-invalid', 'true');
      if (!Number.isFinite(Number(rate.value)) || Number(rate.value) <= 0) rate.setAttribute('aria-invalid', 'true');
    }
  }
  direction.addEventListener('change', () => { value.value = direction.value === 'volume-to-mass' ? '2' : '10'; update(); });
  for (const control of [value, unit, basis, rate]) control.addEventListener(control.tagName === 'SELECT' ? 'change' : 'input', update);
  update();
}
