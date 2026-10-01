const chat=document.getElementById("chat"),form=document.getElementById("composer"),input=document.getElementById("message"),mic=document.getElementById("mic"),status=document.getElementById("status"),voice=document.getElementById("voice"),style=document.getElementById("style"),language=document.getElementById("language"),autoSpeak=document.getElementById("autoSpeak");

const PREF_KEY="coachai.preferences.v2";
const prefs=JSON.parse(localStorage.getItem(PREF_KEY)||"{}");
async function loadLanguages(){
  const list=await (await fetch("/languages")).json();
  language.innerHTML="";
  list.forEach(x=>{
    const o=document.createElement("option");o.value=x.code;o.textContent=x.code==="auto"?x.name:(x.name+" • "+x.native_name);language.appendChild(o)
  });
  language.value=prefs.language||"auto";
  window.__coachaiLanguages=list;
  const selected=list.find(x=>x.code===language.value)||list[0];
  add(selected.greeting,"assistant");
}
loadLanguages().catch(()=>{language.innerHTML="<option value='auto'>Auto-detect</option>"});
if(prefs.voice)voice.value=prefs.voice;
if(prefs.style)style.value=prefs.style;
if(typeof prefs.autoSpeak==="boolean")autoSpeak.checked=prefs.autoSpeak;

function savePrefs(){localStorage.setItem(PREF_KEY,JSON.stringify({language:language.value,voice:voice.value,style:style.value,autoSpeak:autoSpeak.checked}))}
voice.onchange=savePrefs;style.onchange=savePrefs;language.onchange=()=>{savePrefs();const selected=(window.__coachaiLanguages||[]).find(x=>x.code===language.value);if(selected)add(selected.greeting,"assistant")};autoSpeak.onchange=savePrefs;

function browserSpeak(text){
  if(!("speechSynthesis" in window))return false;
  speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);
  const selected=language.value==="auto"?(lastLanguage||"en-GB"):language.value;
  u.lang=selected;
  const voices=window.speechSynthesis.getVoices();
  const female=["female","samantha","karen","moira","victoria","zoe","hazel","zira"];
  const male=["male","daniel","george","ryan","alex","fred","david"];
  const hints=voice.value.includes("Amy")||voice.value.includes("Joanna")||voice.value==="Aditi"?female:male;
  const candidate=voices.find(v=>v.lang.toLowerCase().startsWith(selected.toLowerCase())&&hints.some(h=>v.name.toLowerCase().includes(h)));
  if(candidate)u.voice=candidate;
  u.rate=style.value==="concise"?1.08:1.02;
  speechSynthesis.speak(u);status.textContent="● Speaking…";u.onend=()=>status.textContent="● Ready";return true
}

async function speak(text){
  if((window.__coachaiConfig?.tts_mode||"browser")==="browser"&&browserSpeak(text))return;
  status.textContent="● Speaking…";
  try{
    const res=await fetch("/tts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text,voice_id:voice.value,language:lastLanguage||language.value||"en-GB"})});
    if(!res.ok)throw new Error();
    const audio=new Audio(URL.createObjectURL(await res.blob()));audio.onended=()=>status.textContent="● Ready";await audio.play()
  }catch(e){status.textContent="● Voice unavailable"}
}

function add(text,kind,citations=[]){
  const box=document.createElement("div");box.className="msg "+kind;box.textContent=text;
  if(citations.length){const c=document.createElement("div");c.className="citations";citations.slice(0,3).forEach(x=>{const s=document.createElement("span");s.className="citation";s.textContent=(x.document_name||"Source")+" • "+(x.page!=null?"page "+x.page:"section");c.appendChild(s)});box.appendChild(c)}
  if(kind==="assistant"){const b=document.createElement("button");b.className="play";b.textContent="🔊 Listen";b.onclick=()=>speak(text);box.appendChild(b)}
  chat.appendChild(box);chat.scrollTop=chat.scrollHeight
}

let lastLanguage="en-GB";

form.addEventListener("submit",async e=>{
  e.preventDefault();const message=input.value.trim();if(!message)return;
  add(message,"user");input.value="";status.textContent="● Checking…";
  try{
    const res=await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message,voice_id:voice.value,conversation_style:style.value,language:language.value})});
    if(!res.ok)throw new Error();
    const data=await res.json();lastLanguage=data.language||"en-GB";
    add(data.answer||"I couldn't verify that information.","assistant",data.citations||[]);
    const p=data.performance||{};status.textContent=data.abstained?"● Needs human review":p.cache_hit?"● Instant answer":p.llm_called?"● Verified answer":"● Verified fast answer";
    if(autoSpeak.checked&&!data.abstained)await speak(data.answer)
  }catch(err){add("I’m having trouble reaching the assistant right now. Please try again in a moment.","assistant");status.textContent="● Error"}
});

const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(Recognition){
  const recognition=new Recognition();
  mic.onclick=()=>{recognition.lang=language.value==="auto"?"en-GB":language.value;status.textContent="● Listening…";recognition.start()};
  recognition.interimResults=false;
  recognition.onresult=e=>{input.value=e.results[0][0].transcript;status.textContent="● Ready"};
  recognition.onerror=()=>status.textContent="● Voice input unavailable"
}else{mic.disabled=true;mic.title="Browser speech recognition is not available"}

fetch("/config").then(r=>r.json()).then(c=>window.__coachaiConfig=c).catch(()=>window.__coachaiConfig={tts_mode:"browser"});
