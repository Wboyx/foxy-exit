import shutil,subprocess,re,time
F="/root/foxteam-bot/bot.js"
shutil.copy(F,F+".bak-grammy-1022")
s=open(F).read()
def rep(old,new,name):
    global s
    n=s.count(old)
    if n!=1:
        print("ABORT",name,"count=",n); raise SystemExit(1)
    s=s.replace(old,new); print("ok:",name)
OLD_TG='''async function tg(config, method, body) {
  const res = await fetch(`${config.tgApiBase}/bot${config.botToken}/${method}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
  });
  return res.json();
}'''
NEW_TG='''async function tg(config, method, body) {
  const url = `${config.tgApiBase}/bot${config.botToken}/${method}`;
  const payload = JSON.stringify(body);
  let lastErr = null;
  for (let i = 0; i < 2; i++) {
    const t0 = Date.now();
    try {
      const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: payload });
      const j = await res.json();
      const ms = Date.now() - t0;
      if (ms > 1500) console.log(`\U0001F401 SLOW-TG ${method} ${ms}ms`);
      return j;
    } catch (e) {
      lastErr = e;
      console.log(`\U0001F501 TG-RETRY ${method} ${Date.now() - t0}ms ${(e && e.message || "").slice(0, 60)}`);
      await new Promise((r) => setTimeout(r, 400));
    }
  }
  throw lastErr;
}'''
rep(OLD_TG,NEW_TG,"tg-retry")
OLD_ED='  const result = await tg(config, "editMessageText", body);'
NEW_ED='''  let result;
  try { result = await tg(config, "editMessageText", body); }
  catch (e) { console.log("\u21a9\ufe0f edit-fail \u2192 fallback-send:", (e && e.message || "").slice(0, 60)); return sendTelegram(config, chatId, text, replyMarkup); }'''
rep(OLD_ED,NEW_ED,"edit-fallback")
OLD_PU='''async function processUpdate(update, config) {
  try {
    if (update.message) await handleMessage(update.message, env, config);
    else if (update.callback_query) await handleCallback(update.callback_query, env, config);
  } catch (e) {'''
NEW_PU='''async function processUpdate(update, config) {
  const _t0 = Date.now();
  try {
    if (update.message) await handleMessage(update.message, env, config);
    else if (update.callback_query) await handleCallback(update.callback_query, env, config);
    const _ms = Date.now() - _t0;
    if (_ms > 1500) console.log(`\U0001F401 SLOW-UPD ${_ms}ms`);
  } catch (e) {'''
rep(OLD_PU,NEW_PU,"slowupd")
open(F,"w").write(s)
r=subprocess.run(["node","--check",F],capture_output=True,text=True)
print("syntax:","OK" if r.returncode==0 else "BAD "+r.stderr[:150])
if r.returncode!=0:
    shutil.copy(F+".bak-grammy-1022",F); print("restored"); raise SystemExit(1)
env=open("/root/foxteam-bot/.env").read()
def setenv(k,v):
    global env
    if re.search("^"+k+"=",env,re.M): env=re.sub("^"+k+"=.*",k+"="+v,env,flags=re.M)
    else: env=env.rstrip()+"\n"+k+"="+v+"\n"
setenv("FETCH_TIMEOUT_SHORT_MS","25000")
setenv("POLL_TIMEOUT_SECONDS","25")
open("/root/foxteam-bot/.env","w").write(env)
print("envs-ok")
subprocess.run(["systemctl","restart","foxteam-bot"])
time.sleep(7)
print("bot:",subprocess.run(["systemctl","is-active","foxteam-bot"],capture_output=True,text=True).stdout.strip())
print("PATCH-DONE")
