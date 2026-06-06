import { describe, it, expect } from 'vitest';
import worker from '../src/index';

function mockEnv(initial: Record<string, string> = {}) {
  const store = new Map<string, string>([['units', JSON.stringify(initial)]]);
  return {
    ADMIN_PASSWORD: 'hemmelig',
    STATUS: {
      get: async (k: string, _t?: string) => {
        const v = store.get(k);
        return v ? JSON.parse(v) : null;
      },
      put: async (k: string, v: string) => { store.set(k, v); },
    },
    ASSETS: { fetch: async () => new Response('asset') },
  } as never;
}

describe('/api/status', () => {
  it('GET returns stored status', async () => {
    const env = mockEnv({ H0101: 'solgt' });
    const res = await worker.fetch(new Request('https://x/api/status'), env);
    expect(await res.json()).toEqual({ H0101: 'solgt' });
  });
  it('POST without password is 401', async () => {
    const res = await worker.fetch(new Request('https://x/api/status', {
      method: 'POST', body: JSON.stringify({ unit: 'H0101', status: 'solgt' }),
    }), mockEnv());
    expect(res.status).toBe(401);
  });
  it('POST with password updates status', async () => {
    const env = mockEnv();
    const res = await worker.fetch(new Request('https://x/api/status', {
      method: 'POST',
      headers: { 'x-admin-password': 'hemmelig' },
      body: JSON.stringify({ unit: 'H0204', status: 'reservert' }),
    }), env);
    expect(res.status).toBe(200);
    expect(await res.json()).toMatchObject({ H0204: 'reservert' });
  });
  it('POST rejects invalid unit or status', async () => {
    const env = mockEnv();
    const res = await worker.fetch(new Request('https://x/api/status', {
      method: 'POST',
      headers: { 'x-admin-password': 'hemmelig' },
      body: JSON.stringify({ unit: 'DROP TABLE', status: 'solgt' }),
    }), env);
    expect(res.status).toBe(400);
  });
  it('/admin serves html', async () => {
    const res = await worker.fetch(new Request('https://x/admin'), mockEnv());
    expect(res.headers.get('content-type')).toContain('text/html');
  });
  it('other paths go to assets', async () => {
    const res = await worker.fetch(new Request('https://x/'), mockEnv());
    expect(await res.text()).toBe('asset');
  });
});
