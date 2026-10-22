"""Independent local video MVP. Python 3.10+, FFmpeg required for MP4 exports."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json, os, shutil, subprocess, tempfile, uuid

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'frontend'
DATA = Path(os.environ.get('CLONE_APP_DATA', str(ROOT / 'data')))
PROJECTS, MEDIA, EXPORTS = (DATA / name for name in ('projects', 'media', 'exports'))
for folder in (PROJECTS, MEDIA, EXPORTS): folder.mkdir(parents=True, exist_ok=True)
MIMES = {'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp', '.mp4':'video/mp4','.mov':'video/quicktime','.webm':'video/webm'}
MAX_FILE = 100 * 1024 * 1024

def parse_json(raw):
    obj=json.loads(raw)
    if not isinstance(obj,dict): raise ValueError('JSON must be an object')
    return obj

def project_payload(obj, old=None):
    name=str(obj.get('name','')).strip()[:100]
    if not name: raise ValueError('Tên dự án không được trống')
    media=obj.get('media',[])
    if not isinstance(media,list) or len(media)>100: raise ValueError('Danh sách media không hợp lệ')
    clean=[]
    for mid in media:
        if not isinstance(mid,str) or not any((MEDIA/(mid+ext)).is_file() for ext in MIMES):
            raise ValueError('Media không tồn tại: '+str(mid)[:60])
        clean.append(mid)
    return {'id': old or uuid.uuid4().hex, 'name':name,'notes':str(obj.get('notes',''))[:5000], 'media':clean}

def media_path(mid):
    if not isinstance(mid,str) or len(mid)!=32 or any(ch not in '0123456789abcdef' for ch in mid): return None
    return next((MEDIA/(mid+ext) for ext in MIMES if (MEDIA/(mid+ext)).is_file()), None)

def build_video(project, seconds=3):
    ffmpeg=shutil.which('ffmpeg')
    if not ffmpeg: raise RuntimeError('Chưa cài FFmpeg hoặc ffmpeg chưa có trong PATH')
    ids=project.get('media',[])
    if not ids: raise ValueError('Dự án chưa có ảnh/video')
    if not 1<=seconds<=10: raise ValueError('Thời lượng ảnh phải từ 1 đến 10 giây')
    paths=[media_path(mid) for mid in ids]
    if any(p is None for p in paths): raise ValueError('Dự án có file media bị thiếu')
    output=EXPORTS/(uuid.uuid4().hex+'.mp4')
    with tempfile.TemporaryDirectory(prefix='clone-render-') as tmp:
        segments=[]
        for idx,p in enumerate(paths):
            seg=Path(tmp)/f'{idx:04}.mp4'
            vf='scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p'
            if p.suffix.lower() in ('.jpg','.jpeg','.png','.webp'):
                args=[ffmpeg,'-hide_banner','-loglevel','error','-y','-loop','1','-framerate','25','-i',str(p),'-t',str(seconds)]
            else:
                args=[ffmpeg,'-hide_banner','-loglevel','error','-y','-i',str(p)]
            args+=['-an','-vf',vf,'-r','25','-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p',str(seg)]
            subprocess.run(args,check=True,capture_output=True,timeout=180)
            segments.append(seg)
        playlist=Path(tmp)/'concat.txt'
        playlist.write_text(''.join("file '"+p.name+"'\n" for p in segments),encoding='utf-8')
        subprocess.run([ffmpeg,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(playlist),'-c','copy','-movflags','+faststart',str(output)],check=True,capture_output=True,timeout=180)
    return output

class Handler(BaseHTTPRequestHandler):
    def _json(self,obj,code=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def _file(self,path,ctype):
        data=path.read_bytes(); self.send_response(200); self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(data))); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/api/health': return self._json({'ok':True,'app':'Clone App MVP','ffmpeg':bool(shutil.which('ffmpeg'))})
        if path=='/api/projects':
            items=[]
            for p in PROJECTS.glob('*.json'):
                try: items.append(parse_json(p.read_text(encoding='utf-8')))
                except (OSError,ValueError): pass
            return self._json({'ok':True,'projects':items})
        if path.startswith('/media/'):
            p=media_path(path.split('/')[-1]); return self._file(p,MIMES[p.suffix]) if p else self.send_error(404)
        if path.startswith('/exports/'):
            eid=path.split('/')[-1]
            if len(eid)==36 and eid.endswith('.mp4') and all(x in '0123456789abcdef' for x in eid[:-4]):
                p=EXPORTS/eid
                if p.is_file(): return self._file(p,'video/mp4')
            return self.send_error(404)
        f=(WEB/('index.html' if path=='/' else path.lstrip('/'))).resolve()
        if not f.is_relative_to(WEB.resolve()) or not f.is_file(): return self.send_error(404)
        return self._file(f,{'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8'}.get(f.suffix,'application/octet-stream'))
    def do_POST(self):
        path=urlparse(self.path).path
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<=0 or n>MAX_FILE: return self._json({'ok':False,'error':'File quá lớn hoặc trống (tối đa 100MB)'},413)
            raw=self.rfile.read(n)
            if path=='/api/media':
                filename=parse_qs(urlparse(self.path).query).get('name',[''])[0]
                ext=Path(filename).suffix.lower()
                if ext not in MIMES: raise ValueError('Chỉ hỗ trợ JPG, PNG, WebP, MP4, MOV, WebM')
                mid=uuid.uuid4().hex; (MEDIA/(mid+ext)).write_bytes(raw)
                return self._json({'ok':True,'media':{'id':mid,'name':Path(filename).name,'type':'image' if ext in ('.jpg','.jpeg','.png','.webp') else 'video','url':'/media/'+mid}},201)
            if n>1_000_000: return self._json({'ok':False,'error':'JSON quá lớn'},413)
            obj=parse_json(raw)
            if path=='/api/projects':
                item=project_payload(obj)
                (PROJECTS/(item['id']+'.json')).write_text(json.dumps(item,ensure_ascii=False),encoding='utf-8')
                return self._json({'ok':True,'project':item},201)
            if path=='/api/projects/update':
                pid=obj.get('id','')
                if not isinstance(pid,str) or len(pid)!=32 or any(x not in '0123456789abcdef' for x in pid): raise ValueError('ID dự án không hợp lệ')
                f=PROJECTS/(pid+'.json')
                if not f.is_file(): return self._json({'ok':False,'error':'Không tìm thấy dự án'},404)
                item=project_payload(obj,pid); f.write_text(json.dumps(item,ensure_ascii=False),encoding='utf-8')
                return self._json({'ok':True,'project':item})
            if path=='/api/export':
                pid=obj.get('id','')
                if not isinstance(pid,str) or len(pid)!=32 or any(x not in '0123456789abcdef' for x in pid): raise ValueError('ID dự án không hợp lệ')
                f=PROJECTS/(pid+'.json')
                if not f.is_file(): return self._json({'ok':False,'error':'Không tìm thấy dự án'},404)
                out=build_video(parse_json(f.read_text(encoding='utf-8')),int(obj.get('seconds',3)))
                return self._json({'ok':True,'url':'/exports/'+out.name})
            return self._json({'ok':False,'error':'Endpoint không tồn tại'},404)
        except (ValueError,TypeError,OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
            return self._json({'ok':False,'error':str(e)[:500]},400)

if __name__=='__main__':
    host,port='127.0.0.1',int(os.environ.get('PORT','8790'))
    print(f'Open http://{host}:{port}',flush=True)
    ThreadingHTTPServer((host,port),Handler).serve_forever()
