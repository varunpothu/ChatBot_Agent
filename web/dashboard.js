const cards=document.getElementById("cards"),alerts=document.getElementById("alerts");
function pct(x){return (x*100).toFixed(1)+"%"}
function fmt(x){return new Intl.NumberFormat().format(x||0)}
async function load(){
  const d=await (await fetch("/kpis")).json(),k=d.kpis;
  cards.innerHTML="";
  [
    ["Requests",fmt(k.requests)],
    ["Grounded rate",pct(k.grounded_answer_rate)],
    ["Fast-path rate",pct(k.fast_path_rate)],
    ["Cloud LLM rate",pct(k.llm_call_rate)],
    ["Cache hit rate",pct(k.cache_hit_rate)],
    ["Avg latency",(k.average_latency_ms||0)+" ms"],
    ["Input tokens",fmt(k.estimated_input_tokens)],
    ["Output tokens",fmt(k.estimated_output_tokens)],
    ["TTS characters",fmt(k.tts_characters)],
    ["Human handoffs",fmt(k.human_escalations)],
    ["Verification failures",fmt(k.verification_failures)],
    ["Security blocks",fmt(k.injection_blocks)]
  ].forEach(([l,v])=>{cards.innerHTML+=`<div class="card"><div class="label">${l}</div><div class="value">${v}</div></div>`});
  alerts.innerHTML=d.alerts.length?d.alerts.map(a=>`<div class="alert"><b>${a.severity}: ${a.code}</b><div>${a.message}</div><small>Action: ${a.action}</small></div>`).join(""):"<p>No active alerts.</p>"
}
load();setInterval(load,5000);
