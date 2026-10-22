let projects=[],active=null;
const $=id=>document.getElementById(id);
function status(msg){$('status').textContent=msg}
async function api(path,options){const r=await fetch(path,options);const d=await r.json();if(!d.ok)throw new Error(d.error||'Không thể xử lý yêu cầu');return d}
function opt(p){const o=document.createElement('option');o.value=p.id;o.textContent=p.name;return o}
function mediaUI(){const list=$('mediaList');list.replaceChildren();if(!active)return;for(const id of active.media||[]){const li=document.createElement('li');const a=document.createElement('a');a.href='/media/'+id;a.textContent=id;a.target='_blank';li.append(a);list.append(li)}}
async function refresh(prefer){const d=await api('/api/projects');projects=d.projects;$('project').replaceChildren(...projects.map(opt));active=projects.find(x=>x.id===prefer)||projects[0]||null;if(active)$('project').value=active.id;mediaUI()}
$('project').addEventListener('change',()=>{active=projects.find(x=>x.id===$('project').value);mediaUI()});
$('form').addEventListener('submit',async e=>{e.preventDefault();try{const d=await api('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:$('name').value,notes:$('notes').value,media:[]})});await refresh(d.project.id);status('Đã tạo dự án')}catch(err){status(err.message)}});
$('media').addEventListener('change',async e=>{if(!active)return status('Hãy tạo dự án trước');try{for(const file of e.target.files){status('Đang nhập '+file.name);const d=await api('/api/media?name='+encodeURIComponent(file.name),{method:'POST',body:file});active.media.push(d.media.id)}await save();status('Nhập media thành công')}catch(err){status(err.message)}finally{e.target.value=''}});
async function save(){if(!active)throw new Error('Hãy chọn dự án');const d=await api('/api/projects/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(active)});await refresh(d.project.id);return d}
$('save').addEventListener('click',async()=>{try{await save();status('Đã lưu dự án')}catch(e){status(e.message)}});
$('export').addEventListener('click',async()=>{if(!active)return status('Hãy tạo dự án trước');$('export').disabled=true;status('Đang xuất MP4 (có thể mất một lúc)...');try{await save();const d=await api('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:active.id,seconds:Number($('seconds').value)})});const a=document.createElement('a');a.href=d.url;a.textContent='Mở / tải video MP4';a.target='_blank';$('result').replaceChildren(a);status('Xuất MP4 thành công')}catch(e){status('Lỗi xuất video: '+e.message)}finally{$('export').disabled=false}});
api('/api/health').then(d=>{$('health').textContent=d.ffmpeg?'FFmpeg: đã nhận diện':'FFmpeg: chưa có trong PATH — không thể xuất MP4'}).catch(()=>{});
refresh().catch(e=>status(e.message));
