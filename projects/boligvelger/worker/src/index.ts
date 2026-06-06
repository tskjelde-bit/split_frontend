import { ADMIN_HTML } from './admin';

export interface Env {
  ASSETS: Fetcher;
  STATUS: KVNamespace;
  ADMIN_PASSWORD: string;
}

const VALID_STATUS = new Set(['ledig', 'reservert', 'solgt']);
// The exact 16 units: floors 1 and 2 have 05 units each (H0x01–H0x05),
// floor 3 has 06 (H0301–H0306). H0106/H0206 are ghosts and must be rejected.
const UNIT_RE = /^(H0[12]0[1-5]|H030[1-6])$/;

async function getAll(env: Env): Promise<Record<string, string>> {
  return (await env.STATUS.get('units', 'json')) ?? {};
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);

    if (url.pathname === '/api/status') {
      if (req.method === 'GET') {
        return Response.json(await getAll(env), {
          headers: { 'cache-control': 'no-store' },
        });
      }
      if (req.method === 'POST') {
        // Non-constant-time comparison is acceptable here: this is a single low-value
        // status flag behind a shared secret, not user auth. Timing-attack surface is
        // negligible against a high-entropy password over the network.
        if (req.headers.get('x-admin-password') !== env.ADMIN_PASSWORD) {
          return new Response('unauthorized', { status: 401 });
        }
        let body: { unit?: string; status?: string };
        try { body = await req.json(); } catch { return new Response('bad json', { status: 400 }); }
        if (!body.unit || !UNIT_RE.test(body.unit) || !body.status || !VALID_STATUS.has(body.status)) {
          return new Response('bad request', { status: 400 });
        }
        const all = await getAll(env);
        all[body.unit] = body.status;
        await env.STATUS.put('units', JSON.stringify(all));
        return Response.json(all);
      }
      return new Response('method not allowed', { status: 405 });
    }

    if (url.pathname === '/admin') {
      return new Response(ADMIN_HTML, { headers: { 'content-type': 'text/html;charset=utf-8' } });
    }

    return env.ASSETS.fetch(req);
  },
};
