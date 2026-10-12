// If you open this file directly from disk, talk to the local server.
const API = location.protocol === "file:" ? "http://localhost:8000" : "";
 
const MODELS = ["Punch","Punch EV","Nexon","Nexon EV","Curvv","Curvv EV","Harrier","Harrier EV","Safari","Sierra"];
const STARTERS = [
  "Which Nexon variants have a sunroof?",
  "Compare the Harrier and the Safari",
  "What colours does the Curvv come in?"
];
 
const thread  = document.getElementById("thread");
const scroller= document.getElementById("scroller");
const form    = document.getElementById("form");
const input   = document.getElementById("input");
const sendBtn = document.getElementById("send");
const signal  = document.getElementById("signal");
let busy = false;
 
/* ---------- tiny, safe markdown renderer ---------- */
const esc = s => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
function inline(s){
  s = esc(s);
  s = s.replace(/`([^`]+)`/g,"<code>$1</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");
  s = s.replace(/(^|[^*])\*([^*\s][^*]*)\*/g,"$1<em>$2</em>");
  return s;
}
function md(text){
  const lines = text.replace(/\r/g,"").split("\n");
  const out = [];
  const isTableRow = l => /^\s*\|.*\|\s*$/.test(l);
  const isBullet = l => /^\s*[-*•]\s+/.test(l);
  const isNumber = l => /^\s*\d+[.)]\s+/.test(l);
  let i = 0;
  while(i < lines.length){
    const l = lines[i];
    if(/^\s*$/.test(l)){ i++; continue; }
 
    let m = l.match(/^#{1,4}\s+(.*)/);
    if(m){ out.push("<h4>"+inline(m[1])+"</h4>"); i++; continue; }
 
    if(isTableRow(l) && i+1 < lines.length && /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i+1]) && lines[i+1].includes("-")){
      const cells = r => r.trim().replace(/^\||\|$/g,"").split("|").map(c => c.trim());
      const head = cells(l); i += 2;
      const rows = [];
      while(i < lines.length && isTableRow(lines[i])){ rows.push(cells(lines[i])); i++; }
      out.push('<div class="tbl"><table><thead><tr>' + head.map(h => "<th>"+inline(h)+"</th>").join("") +
        "</tr></thead><tbody>" + rows.map(r => "<tr>"+r.map(c => "<td>"+inline(c)+"</td>").join("")+"</tr>").join("") +
        "</tbody></table></div>");
      continue;
    }
 
    if(isBullet(l)){
      const items = [];
      while(i < lines.length && isBullet(lines[i])){ items.push(lines[i].replace(/^\s*[-*•]\s+/,"")); i++; }
      out.push("<ul>"+items.map(x => "<li>"+inline(x)+"</li>").join("")+"</ul>");
      continue;
    }
    if(isNumber(l)){
      const items = [];
      while(i < lines.length && isNumber(lines[i])){ items.push(lines[i].replace(/^\s*\d+[.)]\s+/,"")); i++; }
      out.push("<ol>"+items.map(x => "<li>"+inline(x)+"</li>").join("")+"</ol>");
      continue;
    }
 
    const p = [];
    while(i < lines.length && !/^\s*$/.test(lines[i]) && !/^#{1,4}\s/.test(lines[i]) &&
          !isBullet(lines[i]) && !isNumber(lines[i]) && !isTableRow(lines[i])){
      p.push(lines[i]); i++;
    }
    if(!p.length){ p.push(lines[i]); i++; }   // safety: always advance
    out.push("<p>"+p.map(inline).join("<br>")+"</p>");
  }
  return out.join("");
}
 
/* ---------- UI helpers ---------- */
function scrollDown(){ scroller.scrollTop = scroller.scrollHeight; }
 
function showEmpty(){
  thread.innerHTML = "";
  const box = document.createElement("div");
  box.className = "empty";
  box.innerHTML = "<h2>Which Tata are you looking at?</h2>" +
    "<p>Ask about variants, features, engines or colours. Pick a model above or start with one of these.</p>";
  const list = document.createElement("div");
  list.className = "starters";
  STARTERS.forEach(q => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = q;
    b.onclick = () => send(q);
    list.appendChild(b);
  });
  box.appendChild(list);
  thread.appendChild(box);
}
 
function addUser(text){
  const w = document.createElement("div");
  w.className = "msg user";
  const b = document.createElement("div");
  b.className = "bubble"; b.textContent = text;
  w.appendChild(b); thread.appendChild(w); scrollDown();
}
 
function addBot(html, sources, isError){
  const w = document.createElement("div");
  w.className = "msg bot";
  const b = document.createElement("div");
  b.className = "bubble" + (isError ? " error" : "");
  b.innerHTML = html;
  w.appendChild(b);
  if(sources && sources.length){
    const s = document.createElement("div");
    s.className = "sources";
    sources.forEach(x => { const t = document.createElement("span"); t.textContent = x; s.appendChild(t); });
    w.appendChild(s);
  }
  thread.appendChild(w); scrollDown();
}
 
function addTyping(){
  const w = document.createElement("div");
  w.className = "msg bot"; w.id = "typing";
  w.innerHTML = '<div class="bubble"><span class="typing" aria-label="Searching the documents"><i></i><i></i><i></i></span></div>';
  thread.appendChild(w); scrollDown();
}
function removeTyping(){ const t = document.getElementById("typing"); if(t) t.remove(); }
 
function setBusy(v){
  busy = v;
  sendBtn.disabled = v;
  signal.classList.toggle("busy", v);
}
 
/* ---------- sending ---------- */
async function send(text){
  text = (text || "").trim();
  if(!text || busy) return;
 
  const empty = thread.querySelector(".empty");
  if(empty) empty.remove();
 
  addUser(text);
  input.value = ""; autosize();
  setBusy(true); addTyping();
 
  try{
    const res = await fetch(API + "/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: text})
    });
    const data = await res.json().catch(() => ({}));
    removeTyping();
    if(!res.ok){
      addBot("<p><strong>The chatbot hit an error.</strong></p><p>" + esc(data.detail || ("Server returned " + res.status)) +
             "</p><p>Check the terminal running <code>uvicorn</code> for the full message.</p>", null, true);
    }else{
      addBot(md(data.answer || "I couldn't find that in the documents."), data.sources, false);
    }
  }catch(e){
    removeTyping();
    addBot("<p><strong>Can't reach the chatbot server.</strong></p><p>Start it in your project folder with " +
           "<code>uvicorn api:app --reload</code>, then try again.</p>", null, true);
  }finally{
    setBusy(false); input.focus();
  }
}
 
function autosize(){
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 150) + "px";
}
 
/* ---------- wiring ---------- */
MODELS.forEach(name => {
  const b = document.createElement("button");
  b.type = "button"; b.textContent = name;
  if(/EV$/.test(name)) b.classList.add("ev");
  b.onclick = () => send("Give me an overview of the Tata " + name + ": price range, variants, colours, engine or battery and range, safety rating and key features.");
  document.getElementById("lineup").appendChild(b);
});
 
form.addEventListener("submit", e => { e.preventDefault(); send(input.value); });
input.addEventListener("input", autosize);
input.addEventListener("keydown", e => {
  if(e.key === "Enter" && !e.shiftKey){ e.preventDefault(); send(input.value); }
});
document.getElementById("clear").onclick = () => { if(!busy){ showEmpty(); input.focus(); } };
 
showEmpty();
input.focus();


async function sendQuestion(question) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ question })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }

  return data.answer;
}
