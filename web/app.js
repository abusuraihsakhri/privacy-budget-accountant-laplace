/* Browser-only Laplace demonstration. No network requests or persistent storage. */
(function (scope) {
  "use strict";

  function finite(value, label, positive) {
    const n = Number(value);
    if (value === "" || value === null || !Number.isFinite(n) || (positive && n <= 0)) {
      throw new Error(label + " must be a finite" + (positive ? ", positive" : "") + " number.");
    }
    return n;
  }

  function secureUnit() {
    if (!scope.crypto || typeof scope.crypto.getRandomValues !== "function") {
      throw new Error("Secure browser randomness is unavailable. No release was made.");
    }
    const bits = new Uint32Array(2);
    scope.crypto.getRandomValues(bits);
    // Keep both endpoints strictly inside (0, 1) after IEEE-754 rounding.
    return ((bits[0] >>> 5) * 67108864 + (bits[1] >>> 6) + 1) / 9007199254740994;
  }

  function laplace(scale, unit) {
    finite(scale, "Scale", true);
    const u = unit === undefined ? secureUnit() : finite(unit, "Uniform draw");
    if (!(u > 0 && u < 1)) throw new Error("Uniform draw must lie in (0, 1).");
    return u < 0.5 ? scale * Math.log(2 * u) : -scale * Math.log(2 * (1 - u));
  }

  function sensitivityFor(type, options) {
    if (type === "count") return 1;
    if (type !== "mean") throw new Error("Choose a supported query type.");
    const lower = finite(options.lower, "Lower bound");
    const upper = finite(options.upper, "Upper bound");
    const n = finite(options.n, "Dataset size", true);
    if (!Number.isSafeInteger(n) || upper <= lower) {
      throw new Error("Mean queries need a positive integer sample size and upper > lower.");
    }
    const sensitivity = (upper - lower) / n;
    if (!Number.isFinite(sensitivity) || sensitivity <= 0) throw new Error("Invalid sensitivity.");
    return sensitivity;
  }

  function createLedger(totalEpsilon) {
    const total = finite(totalEpsilon, "Total epsilon", true);
    let spent = 0;
    return {
      get total() { return total; },
      get spent() { return spent; },
      get remaining() { return Math.max(0, total - spent); },
      release(value, epsilon, sensitivity) {
        const v = finite(value, "Query result");
        const eps = finite(epsilon, "Query epsilon", true);
        const sens = finite(sensitivity, "Sensitivity", true);
        const scale = sens / eps;
        if (!Number.isFinite(scale) || scale <= 0) throw new Error("Invalid noise scale.");
        const next = spent + eps;
        // Comparison tolerance is ONLY for floating-point representation at the boundary.
        const tolerance = 4 * Number.EPSILON * Math.max(Math.abs(total), Math.abs(next));
        if (next > total + tolerance || eps > total) {
          throw new Error("Insufficient remaining privacy budget. No release was made.");
        }
        const noise = laplace(scale);
        const noisy = v + noise;
        if (!Number.isFinite(noisy)) throw new Error("Noisy result would be non-finite.");
        spent = Math.min(total, next);
        return { noisy, noise, epsilon: eps, sensitivity: sens, scale, spent, remaining: this.remaining };
      }
    };
  }

  const api = { finite, laplace, sensitivityFor, createLedger };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document === "undefined") return;

  const byId = (id) => document.getElementById(id);
  let ledger = null;
  let releases = [];
  const number = (n) => Number(n).toLocaleString("en-US", { maximumFractionDigits: 6 });
  const notice = (message, error) => {
    const el = byId("notice");
    el.textContent = message;
    el.className = error ? "notice error" : "notice";
    el.setAttribute("role", error ? "alert" : "status");
  };

  function render() {
    byId("total").textContent = ledger ? number(ledger.total) : "—";
    byId("spent").textContent = ledger ? number(ledger.spent) : "—";
    byId("remaining").textContent = ledger ? number(ledger.remaining) : "—";
    byId("releases").textContent = String(releases.length);
    byId("history").replaceChildren();
    for (const [index, r] of releases.entries()) {
      const tr = document.createElement("tr");
      for (const value of [index + 1, r.type, number(r.epsilon), number(r.scale), number(r.noisy)]) {
        const td = document.createElement("td");
        td.textContent = String(value);
        tr.appendChild(td);
      }
      byId("history").appendChild(tr);
    }
    byId("download").disabled = releases.length === 0;
  }

  function newSession() {
    ledger = createLedger(byId("epsilon-total").value);
    releases = [];
    byId("last-result").textContent = "No disclosures in this session.";
    render();
    notice("New in-memory demonstration ledger. This does not reset a real dataset's previously spent privacy budget.", false);
  }

  byId("budget-form").addEventListener("submit", (event) => {
    event.preventDefault();
    try { newSession(); } catch (err) { notice(err.message, true); }
  });

  byId("query-type").addEventListener("change", () => {
    byId("mean-options").hidden = byId("query-type").value !== "mean";
    byId("query-help").textContent = byId("query-type").value === "mean"
      ? "Fixed-size replace-one adjacency; all individual values must be bounded."
      : "Unweighted event count, add/remove-one adjacency; global sensitivity = 1.";
  });

  byId("release-form").addEventListener("submit", (event) => {
    event.preventDefault();
    try {
      if (!ledger) throw new Error("Initialize an epsilon budget first.");
      const type = byId("query-type").value;
      const value = finite(byId("query-value").value, "Query result");
      const sensitivity = sensitivityFor(type, {
        lower: byId("lower").value, upper: byId("upper").value, n: byId("n").value
      });
      if (type === "count" && (!Number.isSafeInteger(value) || value < 0)) {
        throw new Error("Counts must be nonnegative whole numbers.");
      }
      if (type === "mean" && (value < Number(byId("lower").value) || value > Number(byId("upper").value))) {
        throw new Error("Mean must lie within the provided bounds.");
      }
      const outcome = ledger.release(value, byId("epsilon-query").value, sensitivity);
      releases.push({ type, ...outcome });
      byId("last-result").textContent = "Noisy " + type + " = " + number(outcome.noisy) +
        "   |   Laplace scale = " + number(outcome.scale);
      render();
      notice("Query release generated locally. Epsilon charged to this tab's demonstration ledger.", false);
    } catch (err) { notice(err.message, true); }
  });

  byId("download").addEventListener("click", () => {
    const lines = ["release,query_type,epsilon,sensitivity,scale,noisy_result"];
    for (const [index, r] of releases.entries()) {
      lines.push([index + 1, r.type, r.epsilon, r.sensitivity, r.scale, r.noisy].join(","));
    }
    const url = URL.createObjectURL(new Blob([lines.join("\n") + "\n"], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "laplace-releases.csv";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  });

  try { newSession(); } catch (err) { notice(err.message, true); }
})(globalThis);
