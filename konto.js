/* AI Auditor – frivilligt konto. Sparar bara sammanfattningen av en granskning, aldrig filen. */
(function(){
  var API = window.AIA_KONTO_API || "https://konto.aiauditor.se";
  var NYCKEL = "aia-token", VANTANDE = "aia-vantande";
  function hamta(k){ try { return localStorage.getItem(k); } catch(e){ return null; } }
  function satt(k, v){ try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch(e){} }
  function e(s){ return String(s == null ? "" : s).replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]; }); }
  function tal(v, dec){ return v == null ? "–" : Number(v).toLocaleString("sv-SE", {maximumFractionDigits: dec == null ? 0 : dec}); }

  async function api(metod, vag, data){
    var t = hamta(NYCKEL), h = {"Content-Type": "application/json"};
    if (t) h.Authorization = "Bearer " + t;
    var r = await fetch(API + vag, {method: metod, headers: h, body: data ? JSON.stringify(data) : undefined});
    var j = {}; try { j = await r.json(); } catch(_){}
    if (r.status === 401) satt(NYCKEL, null);
    if (!r.ok) throw new Error(j.fel || "Kontot svarar inte just nu.");
    return j;
  }

  function sammaBolag(a, b){ return (a.orgnr && a.orgnr === b.orgnr) || (!a.orgnr && a.bolag === b.bolag); }
  function rakna(s){ var r = {rod: 0, gul: 0, gron: 0}; (s.fynd || []).forEach(function(f){ r[f.allvar == 1 ? "rod" : f.allvar == 2 ? "gul" : "gron"] += f.antal || 1; }); return r; }

  /* Jämför två sammanfattningar för samma bolag. */
  function jamfor(forra, nu){
    var fm = {}, nm = {}; (forra.fynd || []).forEach(function(f){ fm[f.regel] = f; }); (nu.fynd || []).forEach(function(f){ nm[f.regel] = f; });
    var rattade = Object.keys(fm).filter(function(k){ return !nm[k]; }), nya = Object.keys(nm).filter(function(k){ return !fm[k]; }),
        kvar = Object.keys(nm).filter(function(k){ return fm[k]; });
    var rad = function(k, m){ return "<li>" + e(m[k].rubrik || k) + " <span class=\"kod\">" + e(k) + "</span></li>"; };
    var nt = [["soliditet", "Soliditet", " %", 1], ["kassalikv", "Kassalikviditet", " %", 0], ["rorelsemarg", "Rörelsemarginal", " %", 1]]
      .filter(function(x){ return forra.nyckeltal && nu.nyckeltal && forra.nyckeltal[x[0]] != null && nu.nyckeltal[x[0]] != null; })
      .map(function(x){ var a = forra.nyckeltal[x[0]], b = nu.nyckeltal[x[0]]; return "<li>" + x[1] + ": " + tal(a, x[3]) + x[2] + " → <strong>" + tal(b, x[3]) + x[2] + "</strong></li>"; });
    return "<p class=\"jmf-rubrik\">Jämfört med granskningen " + e(forra.granskad || (forra.sparad || "").slice(0, 10)) + (forra.till ? " (period till " + e(forra.till) + ")" : "") + ":</p>" +
      "<div class=\"jmf\">" +
      "<div><p class=\"jmf-tal gron\">" + rattade.length + "</p><p>rättade</p>" + (rattade.length ? "<ul>" + rattade.map(function(k){ return rad(k, fm); }).join("") + "</ul>" : "") + "</div>" +
      "<div><p class=\"jmf-tal rod\">" + nya.length + "</p><p>nya</p>" + (nya.length ? "<ul>" + nya.map(function(k){ return rad(k, nm); }).join("") + "</ul>" : "") + "</div>" +
      "<div><p class=\"jmf-tal\">" + kvar.length + "</p><p>kvar</p>" + (kvar.length ? "<ul>" + kvar.map(function(k){ return rad(k, nm); }).join("") + "</ul>" : "") + "</div>" +
      "</div>" + (nt.length ? "<ul class=\"jmf-nt\">" + nt.join("") + "</ul>" : "");
  }

  async function skickaLank(epost, sammanfattning){
    if (sammanfattning) satt(VANTANDE, JSON.stringify(sammanfattning));
    await api("POST", "/api/lank", {epost: epost});
  }

  /* Rutan under rapporten på startsidan. */
  async function visaSparaRuta(ruta, s){
    ruta.hidden = false;
    var info = "<p class=\"liten\">Vi sparar bara sammanfattningen: bolagets namn, perioden, några nyckeltal och vilka kontroller som gav anmärkning. Aldrig filen eller verifikationerna. <a href=\"/integritet/\">Mer om det</a>.</p>";
    if (!hamta(NYCKEL)){
      ruta.innerHTML = "<p class=\"hand\">Spara och jämför</p><h3>Se vad som har rättats nästa gång</h3>" +
        "<p>Spara resultatet i ett gratis konto. När du granskar nästa fil ser du direkt vad som har rättats, vad som är nytt och hur nyckeltalen har ändrats.</p>" +
        "<form class=\"spara-form\"><label>Din e-post<input type=\"email\" required autocomplete=\"email\" placeholder=\"namn@foretag.se\"></label>" +
        "<button class=\"knapp prim\" type=\"submit\">Skicka inloggningslänk</button></form>" + info + "<p class=\"spara-status\" role=\"status\"></p>";
      ruta.querySelector("form").addEventListener("submit", async function(ev){
        ev.preventDefault(); var st = ruta.querySelector(".spara-status"), knapp = ruta.querySelector("button");
        knapp.disabled = true; st.textContent = "Skickar…";
        try { await skickaLank(ruta.querySelector("input").value.trim(), s); st.textContent = "Klart. Öppna länken i mejlet så sparas granskningen i ditt konto. Titta i skräpposten om den inte kommer inom ett par minuter.";
              if (window.aiaHand) window.aiaHand("konto-lank"); }
        catch(err){ st.textContent = err.message; knapp.disabled = false; }
      });
      return;
    }
    ruta.innerHTML = "<p class=\"spara-status\">Hämtar dina tidigare granskningar…</p>";
    try {
      var lista = (await api("GET", "/api/resultat")).resultat || [];
      var forra = lista.filter(function(x){ return sammaBolag(x, s); })[0];
      ruta.innerHTML = "<p class=\"hand\">Ditt konto</p><h3>" + (forra ? "Jämförelse med förra gången" : "Första granskningen av " + e(s.bolag || "bolaget")) + "</h3>" +
        (forra ? jamfor(forra, s) : "<p>Spara den, så kan du jämföra nästa gång.</p>") +
        "<button class=\"knapp prim\" type=\"button\">Spara i mitt konto</button> <a href=\"/konto/\">Mitt konto</a>" + info + "<p class=\"spara-status\" role=\"status\"></p>";
      ruta.querySelector("button").addEventListener("click", async function(){
        var st = ruta.querySelector(".spara-status"); this.disabled = true;
        try { await api("POST", "/api/resultat", s); st.textContent = "Sparat."; if (window.aiaHand) window.aiaHand("konto-sparat"); }
        catch(err){ st.textContent = err.message; this.disabled = false; }
      });
    } catch(err){ ruta.innerHTML = "<p class=\"spara-status\">" + e(err.message) + "</p>"; }
  }

  /* Sidan /konto/. */
  async function kontosida(rot){
    var p = new URLSearchParams(location.search), kod = p.get("kod");
    if (kod){
      history.replaceState(null, "", "/konto/");
      try { var j = await api("POST", "/api/logga-in", {kod: kod}); satt(NYCKEL, j.token);
            var v = hamta(VANTANDE); if (v){ await api("POST", "/api/resultat", JSON.parse(v)); satt(VANTANDE, null); } }
      catch(err){ rot.innerHTML = "<p class=\"fel\">" + e(err.message) + "</p>"; }
    }
    if (!hamta(NYCKEL)){
      rot.innerHTML += "<h2>Logga in</h2><p>Du får en länk med e-post. Inget lösenord behövs.</p>" +
        "<form class=\"spara-form\"><label>Din e-post<input type=\"email\" required autocomplete=\"email\"></label><button class=\"knapp prim\">Skicka inloggningslänk</button></form><p class=\"spara-status\" role=\"status\"></p>";
      rot.querySelector("form").addEventListener("submit", async function(ev){
        ev.preventDefault(); var st = rot.querySelector(".spara-status");
        try { await skickaLank(rot.querySelector("input").value.trim(), null); st.textContent = "Klart. Öppna länken i mejlet."; } catch(err){ st.textContent = err.message; }
      });
      return;
    }
    try {
      var jag = await api("GET", "/api/jag"), lista = (await api("GET", "/api/resultat")).resultat || [];
      var grupper = {}; lista.forEach(function(x){ var k = x.orgnr || x.bolag || "–"; (grupper[k] = grupper[k] || []).push(x); });
      var html = "<p>Inloggad som <strong>" + e(jag.epost) + "</strong>.</p>" +
        "<label class=\"kryss\"><input type=\"checkbox\" id=\"paminn\"" + (jag.paminnelse ? " checked" : "") + "> Påminn mig med e-post varje kvartal</label>";
      if (!lista.length) html += "<h2>Inga sparade granskningar än</h2><p><a href=\"/#granska\">Granska en SIE-fil</a> och spara resultatet.</p>";
      Object.keys(grupper).forEach(function(k){
        var g = grupper[k];
        html += "<section class=\"bolag\"><h2>" + e(g[0].bolag || "Okänt bolag") + " <span class=\"kod\">" + e(g[0].orgnr || "") + "</span></h2>";
        g.forEach(function(x, i){
          var r = rakna(x);
          html += "<div class=\"post\"><p><strong>Granskad " + e(x.granskad || x.sparad.slice(0, 10)) + "</strong>, period " + e(x.fran || "?") + " – " + e(x.till || "?") +
            ": <span class=\"rod\">" + r.rod + (r.rod == 1 ? " röd" : " röda") + "</span>, <span class=\"gul\">" + r.gul + (r.gul == 1 ? " gul" : " gula") + "</span>. " +
            "<button class=\"lank-knapp\" data-tabort=\"" + x.id + "\">Ta bort</button></p>" + (g[i + 1] ? jamfor(g[i + 1], x) : "") + "</div>";
        });
        html += "</section>";
      });
      html += "<h2>Ditt konto</h2><p><button class=\"knapp\" id=\"ut\">Logga ut</button> <button class=\"knapp\" id=\"radera\">Radera kontot</button></p><p class=\"spara-status\" role=\"status\"></p>";
      rot.innerHTML = html;
      var st = rot.querySelector(".spara-status");
      rot.querySelector("#paminn").addEventListener("change", async function(){ try { await api("POST", "/api/paminnelse", {pa: this.checked}); st.textContent = this.checked ? "Du får en påminnelse när ett nytt kvartal börjar." : "Påminnelserna är avstängda."; } catch(err){ st.textContent = err.message; } });
      rot.querySelectorAll("[data-tabort]").forEach(function(b){ b.addEventListener("click", async function(){ await api("DELETE", "/api/resultat/" + b.dataset.tabort); kontosida(rot); }); });
      rot.querySelector("#ut").addEventListener("click", async function(){ try { await api("POST", "/api/logga-ut"); } catch(_){} satt(NYCKEL, null); location.href = "/"; });
      var rb = rot.querySelector("#radera");
      rb.addEventListener("click", async function(){
        if (!rb.dataset.saker){ rb.dataset.saker = "1"; rb.textContent = "Klicka igen för att radera allt"; return; }
        try { await api("DELETE", "/api/konto"); } catch(_){}
        satt(NYCKEL, null); satt(VANTANDE, null); rot.innerHTML = "<h2>Kontot är raderat</h2><p>E-postadressen och alla sparade granskningar är borttagna.</p>";
      });
    } catch(err){ rot.innerHTML = "<p class=\"fel\">" + e(err.message) + "</p>"; }
  }

  window.aiaKonto = {visaSparaRuta: visaSparaRuta, kontosida: kontosida, jamfor: jamfor};
})();
