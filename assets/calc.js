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

  /* TDEE: Mifflin-St Jeor BMR x activity factor */
  function computeTdee(root) {
    var sex = $("#t-sex", root).value;
    var age = num($("#t-age", root));
    var height = num($("#t-height", root));
    var heightCm = $("#t-height-unit", root).value === "in" ? height * 2.54 : height;
    var weight = num($("#t-weight", root));
    var weightKg = $("#t-weight-unit", root).value === "lb" ? weight * 0.45359237 : weight;
    var factor = num($("#t-activity", root));
    var steps = num($("#t-steps", root));
    var stepLevel = "";
    if (steps > 0) {
      // Tudor-Locke & Bassett (2004) step bands mapped to the standard activity factors
      var bands = [[5000, 1.2, "sedentary"], [7500, 1.375, "low active"], [10000, 1.55, "somewhat active"],
                   [12500, 1.725, "active"], [Infinity, 1.9, "highly active"]];
      for (var i = 0; i < bands.length; i++) {
        if (steps < bands[i][0]) { factor = bands[i][1]; stepLevel = bands[i][2]; break; }
      }
    }
    set(root, "factor", "× " + factor + (stepLevel ? " (" + stepLevel + ", from steps)" : ""));
    var ok = age > 0 && heightCm > 0 && weightKg > 0 && factor > 0;
    var bmr = ok ? 10 * weightKg + 6.25 * heightCm - 5 * age + (sex === "male" ? 5 : -161) : 0;
    var tdee = bmr * factor;
    var floor = sex === "male" ? 1500 : 1200;
    var r = function (v) { return ok ? Math.round(v).toLocaleString("en-US") : "–"; };
    set(root, "tdee", r(tdee));
    set(root, "bmr", r(bmr) + " kcal");
    set(root, "mild", r(tdee - 250) + " kcal");
    set(root, "loss", r(tdee - 500) + " kcal");
    set(root, "gain", r(tdee + 250) + " kcal");
    set(root, "protein", ok ? Math.round(weightKg * 1.2) + "–" + Math.round(weightKg * 1.6) + " g" : "–");
    var alert = $('[data-out="alert"]', root), msg = "";
    if (ok && tdee - 500 < floor) msg = "A 500 kcal deficit would put you under " + floor.toLocaleString("en-US") + " kcal a day. Very low intakes should only be followed with medical supervision.";
    if (ok && age < 18) msg = "The Mifflin-St Jeor equation was developed for adults. Ask a pediatric professional about energy needs under 18.";
    alert.textContent = msg; alert.hidden = !msg;
  }

  /* Adaptive TDEE: back-calculated from real intake and weight change */
  function computeAdaptive(root) {
    var intake = num($("#a-intake", root));
    var toKg = $("#a-unit", root).value === "lb" ? 0.45359237 : 1;
    var start = num($("#a-start", root)) * toKg;
    var end = num($("#a-end", root)) * toKg;
    var days = num($("#a-days", root));
    var ok = intake > 0 && start > 0 && end > 0 && days > 0;
    var balance = ok ? (end - start) * 7700 / days : 0;   // kcal/day stored (+) or drawn from reserves (-)
    var tdee = intake - balance;
    var perWeek = ok ? (end - start) / days * 7 : 0;
    var unit = toKg === 1 ? "kg" : "lb";
    set(root, "a-tdee", ok ? Math.round(tdee).toLocaleString("en-US") : "–");
    set(root, "a-balance", ok ? (balance > 0 ? "+" : balance < 0 ? "−" : "") + Math.abs(Math.round(balance)).toLocaleString("en-US") + " kcal" : "–");
    set(root, "a-rate", ok ? (perWeek > 0 ? "+" : perWeek < 0 ? "−" : "") + fmt(Math.abs(perWeek / toKg), 2) + " " + unit : "–");
    set(root, "a-loss", ok ? Math.round(tdee - 500).toLocaleString("en-US") + " kcal" : "–");
    var alert = $('[data-out="alert"]', root), msg = "";
    if (ok && days < 14) msg = "Under two weeks of data is dominated by water-weight swings. Use at least 14 days, ideally 3–4 weeks.";
    alert.textContent = msg; alert.hidden = !msg;
  }

  var map = { main: computeMain, recon: computeRecon, dose: computeDose, tdee: computeTdee, adaptive: computeAdaptive };
  $$("[data-calc]").forEach(function (root) {
    var fn = map[root.getAttribute("data-calc")];
    if (fn) wire(root, fn);
  });
})();
