/* Peptide calculators — plain JS, no dependencies.
   Results for the default inputs are already in the served HTML; this script only
   recalculates when the visitor changes something. */
(function () {
  "use strict";

  var U100 = 100; // units per mL on a U-100 insulin syringe

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function num(el) { var v = parseFloat(el && el.value); return isFinite(v) ? v : 0; }
  function fmt(v, d) {
    if (!isFinite(v)) return "–";
    var s = v.toFixed(d === undefined ? 2 : d);
    return s.indexOf(".") >= 0 ? s.replace(/\.?0+$/, "") : s;
  }
  function toMg(value, unit) { return unit === "mcg" ? value / 1000 : value; }
  function set(root, key, text) { $$('[data-out="' + key + '"]', root).forEach(function (el) { el.textContent = text; }); }

  /* Syringe drawing: fill the barrel to the drawn units. */
  function drawSyringe(root, units, capacity) {
    var svg = $(".syringe svg", root);
    if (!svg) return;
    var x0 = 30, w = 300;
    var pct = capacity > 0 ? Math.max(0, Math.min(units / capacity, 1)) : 0;
    var fill = $(".fill", svg), plunger = $(".plunger", svg);
    fill.setAttribute("width", (w * pct).toFixed(1));
    plunger.setAttribute("x", (x0 + w * pct).toFixed(1));
    var ticks = $(".ticks", svg);
    if (ticks && ticks.getAttribute("data-cap") !== String(capacity)) {
      var step = capacity === 100 ? 10 : 5, html = "";
      for (var u = 0; u <= capacity; u += step) {
        var x = x0 + w * (u / capacity);
        html += '<line class="tick" x1="' + x + '" y1="14" x2="' + x + '" y2="' + (u % (step * 2) === 0 ? 26 : 22) + '"/>';
        if (u % (step * 2) === 0) html += '<text class="tick-label" x="' + x + '" y="62" text-anchor="middle">' + u + "</text>";
      }
      ticks.innerHTML = html;
      ticks.setAttribute("data-cap", String(capacity));
    }
  }

  function pressChips(root) {
    $$(".chip", root).forEach(function (chip) {
      var target = $("#" + chip.getAttribute("data-target"), root);
      chip.setAttribute("aria-pressed", target && String(num(target)) === chip.getAttribute("data-value") ? "true" : "false");
    });
  }

  function wire(root, compute) {
    $$("input, select", root).forEach(function (el) {
      el.addEventListener("input", function () { pressChips(root); compute(root); });
      el.addEventListener("change", function () { pressChips(root); compute(root); });
    });
    $$(".chip", root).forEach(function (chip) {
      chip.addEventListener("click", function () {
        var target = $("#" + chip.getAttribute("data-target"), root);
        if (!target) return;
        target.value = chip.getAttribute("data-value");
        pressChips(root);
        compute(root);
      });
    });
    pressChips(root);
    compute(root);
  }

  function syringeWarning(root, units, capacity) {
    var alert = $('[data-out="alert"]', root);
    if (!alert) return;
    var msg = "";
    if (units > capacity) msg = "This draw (" + fmt(units, 1) + " units) is larger than the selected syringe. Use a larger syringe or add less water.";
    else if (units > 0 && units < 2) msg = "Under 2 units is hard to measure accurately. Adding more bacteriostatic water makes small doses easier to draw.";
    alert.textContent = msg;
    alert.hidden = !msg;
  }

  /* Home: all-in-one peptide calculator */
  function computeMain(root) {
    var vialMg = toMg(num($("#vial", root)), $("#vial-unit", root).value);
    var water = num($("#water", root));
    var doseMg = toMg(num($("#dose", root)), $("#dose-unit", root).value);
    var cap = parseInt($("#syringe", root).value, 10);
    var conc = water > 0 ? vialMg / water : 0;          // mg per mL
    var ml = conc > 0 ? doseMg / conc : 0;              // mL per dose
    var units = ml * U100;
    set(root, "units", fmt(units, 1));
    set(root, "ml", fmt(ml, 3) + " mL");
    set(root, "conc", fmt(conc, 3) + " mg/mL");
    set(root, "per-unit", fmt(conc * 1000 / U100, 2) + " mcg");
    set(root, "doses", doseMg > 0 ? fmt(Math.floor(vialMg / doseMg + 1e-9), 0) : "–");
    set(root, "dose-mcg", fmt(doseMg * 1000, 1) + " mcg");
    drawSyringe(root, units, cap);
    syringeWarning(root, units, cap);
  }

  /* Reconstitution: how much bacteriostatic water to add */
  function computeRecon(root) {
    var vialMg = toMg(num($("#r-vial", root)), $("#r-vial-unit", root).value);
    var doseMg = toMg(num($("#r-dose", root)), $("#r-dose-unit", root).value);
    var targetUnits = num($("#r-units", root));
    var cap = parseInt($("#r-syringe", root).value, 10);
    var water = doseMg > 0 ? (vialMg * targetUnits) / (U100 * doseMg) : 0;
    var conc = water > 0 ? vialMg / water : 0;
    set(root, "water", fmt(water, 2));
    set(root, "conc", fmt(conc, 3) + " mg/mL");
    set(root, "per-unit", fmt(conc * 1000 / U100, 2) + " mcg");
    set(root, "doses", doseMg > 0 ? fmt(Math.floor(vialMg / doseMg + 1e-9), 0) : "–");
    set(root, "units", fmt(targetUnits, 1) + " units");
    drawSyringe(root, targetUnits, cap);
    var alert = $('[data-out="alert"]', root), msg = "";
    if (water > 0 && water < 0.5) msg = "Less than 0.5 mL of water is hard to add precisely and makes a very strong solution. Consider a higher units-per-dose target.";
    else if (water > 10) msg = "More than 10 mL may not fit in a standard vial. Lower the units-per-dose target.";
    else if (targetUnits > cap) msg = "The units per dose exceed the selected syringe capacity.";
    alert.textContent = msg; alert.hidden = !msg;

    var body = $("#r-table", root);
    if (body) {
      var rows = "";
      [1, 1.5, 2, 2.5, 3, 5].forEach(function (w) {
        var c = vialMg / w, u = doseMg > 0 ? (doseMg / c) * U100 : 0;
        rows += "<tr><td>" + fmt(w, 1) + " mL</td><td>" + fmt(c, 3) + " mg/mL</td><td>" + fmt(c * 10, 2) + " mcg</td><td>" + fmt(u, 1) + " units</td></tr>";
      });
      body.innerHTML = rows;
    }
  }

  /* Dosage: dose to units, plus vial supply */
  function computeDose(root) {
    var vialMg = toMg(num($("#d-vial", root)), $("#d-vial-unit", root).value);
    var water = num($("#d-water", root));
    var doseMg = toMg(num($("#d-dose", root)), $("#d-dose-unit", root).value);
    var perWeek = num($("#d-freq", root));
    var cap = parseInt($("#d-syringe", root).value, 10);
    var conc = water > 0 ? vialMg / water : 0;
    var ml = conc > 0 ? doseMg / conc : 0;
    var units = ml * U100;
    var doses = doseMg > 0 ? Math.floor(vialMg / doseMg + 1e-9) : 0;
    var days = perWeek > 0 ? doses / perWeek * 7 : 0;
    var monthMg = doseMg * perWeek * 30 / 7;
    set(root, "units", fmt(units, 1));
    set(root, "ml", fmt(ml, 3) + " mL");
    set(root, "conc", fmt(conc, 3) + " mg/mL");
    set(root, "doses", doseMg > 0 ? fmt(doses, 0) : "–");
    set(root, "days", perWeek > 0 && doseMg > 0 ? fmt(Math.floor(days), 0) + " days" : "–");
    set(root, "month", fmt(monthMg, 2) + " mg");
    drawSyringe(root, units, cap);
    syringeWarning(root, units, cap);

    var body = $("#d-table", root);
    if (body) {
      var rows = "";
      [0.5, 0.75, 1, 1.25, 1.5, 2].forEach(function (k) {
        var d = doseMg * k, m = conc > 0 ? d / conc : 0;
        rows += "<tr><td>" + fmt(d * 1000, 1) + " mcg (" + fmt(d, 3) + " mg)</td><td>" + fmt(m, 3) + " mL</td><td>" + fmt(m * U100, 1) + " units</td></tr>";
      });
      body.innerHTML = rows;
    }
  }

  var map = { main: computeMain, recon: computeRecon, dose: computeDose };
  $$("[data-calc]").forEach(function (root) {
    var fn = map[root.getAttribute("data-calc")];
    if (fn) wire(root, fn);
  });
})();
