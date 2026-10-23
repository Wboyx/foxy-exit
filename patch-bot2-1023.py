import shutil,subprocess,time,re
F="/root/foxteam-bot/bot.js"
shutil.copy(F,F+".bak-ka-1023")
s=open(F).read()
OLD='''async function tg(config, method, body) {
  const url = `${config.tgApiBase}/bot${config.botToken}/${method}`;
  const payload = JSON.stringify(body);
  let lastErr = null;
  for (let i = 0; i < 2; i++) {
    const t0 = Date.now();
    try {
      const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: payload });
      const j = await res.json();'''
NEW='''async function tg(config, method, body) {
  const url = `${config.tgApiBase}/bot${config.botToken}/${method}`;
  const payload = JSON.stringify(body);
  let lastErr = null;
  for (let i = 0; i < 2; i++) {
    const t0 = Date.now();
    try {
      const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "Connection": "close" }, body: payload });
      const j = await res.json();'''
assert s.count(OLD)==1, "tg-block not found"
s=s.replace(OLD,NEW)
open(F,"w").write(s)
r=subprocess.run(["node","--check",F],capture_output=True,text=True)
print("syntax:","OK" if r.returncode==0 else "BAD "+r.stderr[:120])
if r.returncode!=0:
    shutil.copy(F+".bak-ka-1023",F); raise SystemExit(1)
# envs در خودِ یونیت (قبل از استارتِ پروسه — wrapper خطِ اول می‌خواندش)
O="/etc/systemd/system/foxteam-bot.service.d/override.conf"
o=open(O).read()
if "FETCH_TIMEOUT_SHORT_MS" not in o:
    o=o.rstrip()+"\nEnvironment=FETCH_TIMEOUT_SHORT_MS=8000 FETCH_TIMEOUT_LONG_MS=60000\n"
    open(O,"w").write(o)
print("unit-env-ok")
subprocess.run(["systemctl","daemon-reload"])
subprocess.run(["systemctl","restart","foxteam-bot"])
time.sleep(7)
print("bot:",subprocess.run(["systemctl","is-active","foxteam-bot"],capture_output=True,text=True).stdout.strip())
# تستِ پیاپی: ۸ فچِ editMessageText شبیهِ منو (کانکشنِ نو هر بار)
tok=""
for ln in open("/root/foxteam-bot/.env"):
    if ln.startswith("BOT_TOKEN"): tok=ln.split("=",1)[1].strip()
js='''(async()=>{const t0=Date.now();for(let i=0;i<8;i++){const a=Date.now();try{const r=await fetch("https://tg.salamfox.ir/fxtgc1b9cc638dad/bot"+process.env.T+"/answerCallbackQuery",{method:"POST",headers:{"Content-Type":"application/json","Connection":"close"},body:JSON.stringify({callback_query_id:"x"+i})});await r.json();console.log(i,Date.now()-a+"ms")}catch(e){console.log(i,"ERR",Date.now()-a+"ms",(e.cause&&e.cause.code)||e.message)}}console.log("total",Date.now()-t0+"ms")})()'''
open("/tmp/rt.js","w").write("process.env.T="+json.dumps(tok)+";"+js)
r=subprocess.run(["node","/tmp/rt.js"],capture_output=True,text=True,timeout=50)
print("rapid8:",r.stdout[:300])
print("PATCH2-DONE")
