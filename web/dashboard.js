const cards=document.getElementById("cards"),alerts=document.getElementById("alerts"),documents=document.getElementById("documents"),reviews=document.getElementById("reviews"),adminKey=document.getElementById("adminKey");
adminKey.value=localStorage.getItem("coachai.adminKey")||"";
document.getElementById("saveKey").onclick=()=>{localStorage.setItem("coachai.adminKey",adminKey.value);load()};

function headers(){return {"X-Admin-Key":adminKey.value}}
function pct(x){return (x*100).toFixed(1)+"%"}
function fmt(x){return new Intl.NumberFormat().format(x||0)}

async function load(){
  if(!adminKey.value){alerts.innerHTML="<p>Enter the admin key to view operations data.</p>";return}
  try{
    const kpiRes=await fetch("/kpis",{headers:headers()});
    if(!kpiRes.ok)throw new Error("Admin access denied");
    const d=await kpiRes.json(),k=d.kpis;
    cards.innerHTML="";
    [
      ["Requests",fmt(k.requests)],["Grounded rate",pct(k.grounded_answer_rate)],
      ["Fast-path rate",pct(k.fast_path_rate)],["Cloud LLM rate",pct(k.llm_call_rate)],
      ["Cache hit rate",pct(k.cache_hit_rate)],["Avg latency",(k.average_latency_ms||0)+" ms"],
      ["Input tokens",fmt(k.estimated_input_tokens)],["Output tokens",fmt(k.estimated_output_tokens)],
      ["TTS characters",fmt(k.tts_characters)],["Human handoffs",fmt(k.human_escalations)],
      ["Verification failures",fmt(k.verification_failures)],["Security blocks",fmt(k.injection_blocks)]
    ].forEach(([l,v])=>{cards.innerHTML+=`<div class="card"><div class="label">${l}</div><div class="value">${v}</div></div>`});

    alerts.innerHTML=d.alerts.length?d.alerts.map(a=>`<div class="alert"><b>${a.severity}: ${a.code}</b><div>${a.message}</div><small>Action: ${a.action}</small></div>`).join(""):"<p>No active alerts.</p>";

    const docs=await (await fetch("/documents",{headers:headers()})).json();
    documents.innerHTML=docs.length?docs.map(x=>{
      const action=x.status==="PENDING_REVIEW"?`<button onclick="approve('${x.document_id}')">Approve</button><button onclick="rejectDoc('${x.document_id}')">Reject</button>`:"";
      return `<div class="row"><div><b>${x.name}</b><small>${x.version} • ${x.status}</small></div><div>${action}</div></div>`
    }).join(""):"<p>No documents yet.</p>";

    const rv=await (await fetch("/reviews?status=OPEN",{headers:headers()})).json();
    reviews.innerHTML=rv.length?rv.map(x=>`<div class="row"><div><b>${x.reason}</b><small>${x.message}</small></div><button onclick="resolveReview('${x.review_id}')">Resolve</button></div>`).join(""):"<p>No open reviews.</p>";
  }catch(e){alerts.innerHTML="<p>Admin access denied or API unavailable.</p>"}
}

async function approve(id){await fetch("/admin/documents/"+id+"/approve?reviewer=admin",{method:"POST",headers:headers()});load()}
async function rejectDoc(id){await fetch("/admin/documents/"+id+"/reject?reviewer=admin",{method:"POST",headers:headers()});load()}
async function resolveReview(id){
  const resolution=prompt("Resolution");
  if(!resolution)return;
  await fetch("/reviews/"+id+"/resolve",{method:"POST",headers:{...headers(),"Content-Type":"application/json"},body:JSON.stringify({reviewer:"admin",resolution})});
  load()
}
load();setInterval(load,5000);