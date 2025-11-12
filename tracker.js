(function(){
  const WINDOW_MS = 2000;
  let keyDownTimes = {}, keyHolds = [], keyIntervals = [], lastKeyTime = null;
  let mouseMoves = [], lastMouse = null, clicks = 0;
  function now(){ return Date.now(); }
  document.addEventListener('keydown', (e)=>{
    const t = now();
    if (!keyDownTimes[e.code]) keyDownTimes[e.code] = t;
    if (lastKeyTime) keyIntervals.push((t - lastKeyTime)/1000.0);
    lastKeyTime = t;
  });
  document.addEventListener('keyup', (e)=>{
    const t = now();
    if (keyDownTimes[e.code]){
      keyHolds.push((t - keyDownTimes[e.code])/1000.0);
      delete keyDownTimes[e.code];
    }
  });
  document.addEventListener('mousemove', (e)=>{
    const t = now();
    if (lastMouse){
      const dt = (t - lastMouse.t)/1000.0;
      if (dt>0){
        const dx = e.clientX - lastMouse.x, dy = e.clientY - lastMouse.y;
        const speed = Math.sqrt(dx*dx + dy*dy)/dt;
        mouseMoves.push(speed);
      }
    }
    lastMouse = {x:e.clientX,y:e.clientY,t:t};
  });
  document.addEventListener('click', ()=>{ clicks += 1; });
  function stats(arr){ if (!arr || arr.length===0) return {mean:0,std:0,count:0}; const mean = arr.reduce((a,b)=>a+b,0)/arr.length; const variance = arr.reduce((a,b)=>a+(b-mean)*(b-mean),0)/arr.length; return {mean:mean, std: Math.sqrt(variance), count: arr.length}; }
  async function sendWindow(){
    const kh = stats(keyHolds), ki = stats(keyIntervals), mm = stats(mouseMoves);
    const click_rate = clicks / (WINDOW_MS/1000.0);
    const payload = { features: { avg_key_hold: +(kh.mean||0).toFixed(4), std_key_hold: +(kh.std||0).toFixed(4), avg_latency: +(ki.mean||0).toFixed(4), std_latency: +(ki.std||0).toFixed(4), avg_mouse_speed: +(mm.mean||0).toFixed(2), std_mouse_speed: +(mm.std||0).toFixed(2), click_rate: +click_rate.toFixed(3) } };
    try{
      const res = await fetch('/track',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      const j = await res.json();
      let box = document.getElementById('status-box');
      if (!box){ box = document.createElement('div'); box.id='status-box'; box.className='status-box'; document.body.appendChild(box); }
      box.innerText = 'prob: ' + (j.prob !== undefined ? j.prob : '-') + '\ncount: ' + (j.count!==undefined?j.count:'-');
      if (j.action === 'logout'){ alert('Anomaly detected — returning to login'); window.location='/login'; }
    }catch(e){ console.warn('tracking error', e); }
    keyHolds = []; keyIntervals = []; mouseMoves = []; clicks = 0;
  }
  setInterval(sendWindow, WINDOW_MS);
})();