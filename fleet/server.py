#!/usr/bin/python3
"""Read-only local fleet console. No enrollment, credentials or remote commands."""
import argparse, collections, http.server, json, multiprocessing, pathlib, ssl, subprocess, threading, time, urllib.error, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
MAX_BODY = 65536

def run_json(argv):
    r = subprocess.run(argv, capture_output=True, text=True, timeout=6, check=True)
    return json.loads(r.stdout)

CONNECTION_MESSAGES = {
    'not-installed': ('Install Tailscale on this computer to see your workers.', 'Ask the owner to install Tailscale from its official website, then connect this computer and refresh.'),
    'not-running': ('Start Tailscale on this computer to see your workers.', 'Open Tailscale and start its connection. On Code Swarm OS, ask the owner to start the Tailscale service, then refresh.'),
    'not-logged-in': ('Connect this computer to Tailscale to see your workers.', 'Open Tailscale and sign in to the account or tailnet that contains your workers, then refresh.'),
    'permission-denied': ('This account cannot read Tailscale status.', 'Ask this computer’s administrator to review Tailscale access for your account, then refresh. No permissions have been changed.'),
    'needs-approval': ('This computer is waiting for Tailscale approval.', 'Ask your tailnet administrator to approve this computer, then refresh.'),
    'unavailable': ('Tailscale status is unavailable right now.', 'Open Tailscale to check its connection, then refresh. Troubleshooting details are available below.')
}

def connection_issue(state, detail=''):
    message, instructions = CONNECTION_MESSAGES[state]
    return dict(error=message, connection_state=state, setup_instructions=instructions, technical_detail=detail[:600])

def tailscale_status():
    try:
        status = run_json(['tailscale', 'status', '--json'])
    except FileNotFoundError as e:
        return None, connection_issue('not-installed', str(e))
    except PermissionError as e:
        return None, connection_issue('permission-denied', str(e))
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or '') + '\n' + str(e)
        if any(x in detail.lower() for x in ('permission denied', 'access denied', 'operation not permitted')):
            return None, connection_issue('permission-denied', detail)
        # A failed status command alone does not prove the daemon is stopped.
        try:
            service = subprocess.run(['systemctl','show','tailscaled.service','--property=LoadState,ActiveState'], capture_output=True, text=True, timeout=1)
            fields = dict(line.split('=',1) for line in service.stdout.splitlines() if '=' in line)
            if service.returncode == 0 and fields.get('LoadState') == 'loaded' and fields.get('ActiveState') in ('inactive','failed'):
                return None, connection_issue('not-running', detail + '\n' + service.stdout)
        except (OSError, subprocess.SubprocessError):
            pass
        return None, connection_issue('unavailable', detail)
    except Exception as e:
        return None, connection_issue('unavailable', str(e))
    state = status.get('BackendState','unknown')
    if state != 'Running':
        kind = {'NeedsLogin':'not-logged-in','NeedsMachineAuth':'needs-approval','Stopped':'not-running'}.get(state,'unavailable')
        return None, connection_issue(kind, 'Tailscale BackendState: ' + str(state))
    return status, None

def validate_url(value, host, path):
    u = urllib.parse.urlsplit(value)
    if (u.scheme != 'https' or u.hostname != host or not host.endswith('.ts.net')
        or u.username or u.password or u.port or u.query or u.fragment or u.path != path):
        raise ValueError('Use the exact peer HTTPS hostname and documented path')
    return value

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None

def fetch(url, method='GET'):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect(),
                                        urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(urllib.request.Request(url, method=method), timeout=3) as r:
            body = r.read(MAX_BODY + 1)
            if len(body) > MAX_BODY:
                raise ValueError('Response too large')
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, b''

def peer_row(peer, config, probe=fetch, now=None):
    now = time.time() if now is None else now
    host = str(peer.get('DNSName', '')).rstrip('.').lower()
    row = dict(id=peer.get('ID', host), name=peer.get('HostName') or host or 'Unnamed peer',
               hostname=host, os=peer.get('OS', 'unknown'), transport='online' if peer.get('Online') is True else 'offline' if peer.get('Online') is False else 'unknown',
               last_seen=peer.get('LastSeen'), desktop='unknown', app='unknown', worker='unknown',
               telemetry='not configured', desktop_url=None, detail='No worker telemetry configured.')
    item = config.get(host)
    if not item:
        return row
    try:
        status_url = validate_url(item['status_url'], host, '/code-swarm-status')
        desktop_url = validate_url(item['desktop_url'], host, '/vnc.html')
        if row['transport'] != 'online':
            row['telemetry'] = 'unavailable'
            row['detail'] = 'Tailscale peer is not online; desktop and app are unknown.'
            return row
        code, body = probe(status_url)
        if code != 200:
            raise ValueError('Worker telemetry HTTP ' + str(code))
        data = json.loads(body)
        age = now - float(data['observed_at'])
        if data.get('schema') != 1 or age < -30 or age > 90:
            row.update(telemetry='stale', detail='Worker timestamp is stale or clock differs; states are unknown.')
            return row
        row['telemetry'] = 'fresh'
        row['expires_at'] = min(float(data['observed_at']) + 90, now + 90)
        row['desktop'] = data.get('desktop') if data.get('desktop') in ('active', 'inactive', 'needs-login', 'display-unavailable') else 'unknown'
        row['app'] = data.get('app') if data.get('app') in ('running', 'starting', 'stopped', 'failed') else 'unknown'
        row['worker'] = 'unknown' # Process presence cannot establish authentication or active Codex work.
        row['resources'] = {k: data.get('resources', {}).get(k) for k in ('memory_available_mib', 'memory_total_mib', 'disk_free_gib', 'disk_total_gib', 'uptime_seconds')}
        row['updates'] = data.get('updates', 'unknown')
        row['detail'] = 'Fresh worker report. ChatGPT authentication and active jobs are not observable.'
        if row['desktop'] == 'needs-login':
            row['detail'] = 'Computer is at its login screen. OS login and encrypted-keyring unlock are still required.'
        elif row['desktop'] == 'display-unavailable':
            row['detail'] = 'No active graphical seat was found. Check the physical display, EDID and display manager.'
        if row['desktop'] in ('active', 'needs-login') and data.get('same_session_vnc') is True:
            code, _ = probe(desktop_url, 'HEAD')
            if code in (200, 401):
                row['desktop_url'] = desktop_url + '?autoconnect=1&resize=scale'
                row['detail'] += ' Desktop HTTPS route verified' + ('; sign in is required.' if code == 401 else '.')
            else:
                row['detail'] += ' Desktop route unavailable (HTTP ' + str(code) + ').'
    except Exception as e:
        row.update(telemetry='error', desktop='unknown', app='unknown', desktop_url=None,
                   detail=str(e)[:180])
    return row

def probe_child(connection, peer, config):
    try: connection.send(peer_row(peer, config))
    except Exception: pass
    finally: connection.close()

def bounded_probes(peers, config, budget=10, per_peer=6, target=probe_child):
    """OS processes make the deadline cover DNS, TLS and trickling bodies too."""
    rows = [peer_row(peer, {}) for peer in peers]
    queue = collections.deque(i for i,p in enumerate(peers) if str(p.get('DNSName','')).rstrip('.').lower() in config)
    for i in queue:
        rows[i].update(telemetry='unavailable', detail='Refresh deadline reached; worker readiness is unknown.')
    active = []
    deadline = time.monotonic() + budget
    context = multiprocessing.get_context('spawn')
    try:
        while (queue or active) and time.monotonic() < deadline:
            while queue and len(active) < 2 and time.monotonic() < deadline:
                i=queue.popleft(); parent, child=context.Pipe(duplex=False)
                process=context.Process(target=target,args=(child,peers[i],config),daemon=True)
                process.start();child.close();active.append((i,process,parent,time.monotonic()+per_peer))
            for job in list(active):
                i,process,connection,expires=job
                if connection.poll():
                    try: rows[i]=connection.recv()
                    except EOFError: pass
                    process.join(timeout=.05)
                    if process.is_alive(): process.terminate();process.join(timeout=.1)
                    connection.close();active.remove(job)
                elif time.monotonic()>=expires or not process.is_alive():
                    if process.is_alive():process.terminate()
                    process.join(timeout=.1);connection.close();active.remove(job)
            if active: time.sleep(.02)
    finally:
        for _,process,connection,_ in active:
            if process.is_alive():process.terminate()
            process.join(timeout=.1)
            if process.is_alive():process.kill();process.join(timeout=.1)
            connection.close()
    return rows

class Fleet:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.cached = None
        self.checked = 0

    def snapshot(self):
        if not self.lock.acquire(blocking=False):
            return dict(observed_at=time.time(),source='Local Tailscale',devices=[],error='A refresh is already in progress; readiness is unknown.')
        try:
            deadline=time.monotonic()+12
            if self.cached is not None and time.monotonic() - self.checked < 15:
                return self.cached
            result = dict(observed_at=time.time(), source='Local tailscale status --json', devices=[], error=None)
            try:
                config = json.loads(self.config.read_text()) if self.config.exists() else {}
                if not isinstance(config, dict) or len(config) > 100:
                    raise ValueError('Configuration must map at most 100 peer hostnames')
                ts, issue = tailscale_status()
                if issue:
                    result.update(issue)
                    self.cached, self.checked = result, time.monotonic()
                    return result
                result['backend_state'] = 'Running'
                peers = list(ts.get('Peer', {}).values())
                if ts.get('Self'):
                    peers.append(ts['Self'])
                peers = sorted(peers, key=lambda p: str(p.get('HostName', '')))[:100]
                result['devices'] = bounded_probes(peers,config,budget=max(0,deadline-time.monotonic()))
            except Exception as e:
                result.update(error='Worker status could not be refreshed.', setup_instructions='Check the troubleshooting details, then refresh.', technical_detail=str(e)[:600])
            self.cached, self.checked = result, time.monotonic()
            return result
        finally: self.lock.release()

def handler(fleet, port):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            # Reject DNS rebinding; this console intentionally has no remote bind option.
            if self.headers.get('Host') not in ('127.0.0.1:' + str(port), 'localhost:' + str(port)):
                self.send_error(403); return
            if self.path == '/api/workers':
                body = json.dumps(fleet.snapshot()).encode(); content_type = 'application/json'
            elif self.path in ('/', '/app.js', '/state.js', '/style.css', '/brand.svg'):
                name = {'/': 'index.html', '/app.js': 'app.js', '/state.js':'state.js', '/style.css': 'style.css', '/brand.svg': 'brand.svg'}[self.path]
                body = (ROOT / 'static' / name).read_bytes()
                content_type = {'index.html': 'text/html', 'app.js': 'text/javascript', 'state.js':'text/javascript', 'style.css': 'text/css', 'brand.svg': 'image/svg+xml'}[name]
            else:
                self.send_error(404); return
            self.send_response(200)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers(); self.wfile.write(body)
    return Handler

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=pathlib.Path, default=pathlib.Path.home()/'.config/code-swarm/workers.json')
    p.add_argument('--port', type=int, default=8765)
    args = p.parse_args()
    server = http.server.ThreadingHTTPServer(('127.0.0.1', args.port), handler(Fleet(args.config), args.port))
    print('Code Swarm OS Workers: http://127.0.0.1:' + str(args.port), flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
