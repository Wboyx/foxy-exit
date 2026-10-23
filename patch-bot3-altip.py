import shutil,subprocess,time
F="/root/foxteam-bot/bot.js"
shutil.copy(F,F+".bak-altip-1023")
s=open(F).read()
HELPERS='''// === Fox Net v3: dual-IP failover (per-request auto-switch on edge freeze) ===
const FOX_ALT_IP = "172.66.47.10";
function altFetch(url, opts = {}) {
  return new Promise((resolve, reject) => {
    try {
      const u = new URL(url);
      const data = opts.body || null;
      const headers = Object.assign({}, opts.headers || {}, { host: u.hostname });
      if (data) headers["content-length"] = Buffer.byteLength(data);
      const req = require("https").request({
        host: FOX_ALT_IP, port: 443, path: u.pathname + u.search,
        method: opts.method || "GET", servername: u.hostname,
        headers, timeout: 9000
      }, (res) => {
        const chunks = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () => {
          const text = Buffer.concat(chunks).toString();
          resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, status: res.statusCode, json: async () => { try { return JSON.parse(text); } catch (e) { return { ok: false }; } } });
        });
      });
      req.on("timeout", () => req.destroy(new Error("alt-ip-timeout")));
      req.on("error", reject);
      if (data) req.write(data);
      req.end();
    } catch (e) { reject(e); }
  });
}
async function foxFetch(url, opts = {}) {
  try {
    return await fetch(url, opts);
  } catch (e) {
    console.log("\U0001F501 FOX-ALT-IP:", (e && e.message || "").slice(0, 50));
    return await altFetch(url, opts);
  }
}
// === end Fox Net v3 ===
async function tg(config, method, body) {'''
OLD_TG='async function tg(config, method, body) {'
assert s.count(OLD_TG)==1, "tg-head:"+str(s.count(OLD_TG))
s=s.replace(OLD_TG,HELPERS)
OLD_F='      const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "Connection": "close" }, body: payload });'
NEW_F='      const res = await foxFetch(url, { method: "POST", headers: { "Content-Type": "application/json", "Connection": "close" }, body: payload });'
assert s.count(OLD_F)==1, "tg-fetch:"+str(s.count(OLD_F))
s=s.replace(OLD_F,NEW_F)
OLD_GU='  const res = await fetch(url, { headers: { "Connection": "close" } });'
NEW_GU='  const res = await foxFetch(url, { headers: { "Connection": "close" } });'
assert s.count(OLD_GU)==1, "gu-fetch:"+str(s.count(OLD_GU))
s=s.replace(OLD_GU,NEW_GU)
open(F,"w").write(s)
r=subprocess.run(["node","--check",F],capture_output=True,text=True)
print("syntax:","OK" if r.returncode==0 else "BAD "+r.stderr[:150])
if r.returncode!=0:
    shutil.copy(F+".bak-altip-1023",F); raise SystemExit(1)
subprocess.run(["systemctl","restart","foxteam-bot"])
time.sleep(7)
print("bot:",subprocess.run(["systemctl","is-active","foxteam-bot"],capture_output=True,text=True).stdout.strip())
print("PATCH3-DONE")
