const GovInfoAPIClient = require('../src/mcp-servers/govinfo/client');
const CongressAPIClient = require('../src/mcp-servers/congress/client');

describe('GovInfo API Client', () => {
  let client;

  beforeEach(() => {
    client = new GovInfoAPIClient('test-key');
  });

  test('should initialize with correct configuration', () => {
    expect(client.apiKey).toBe('test-key');
    expect(client.baseUrl).toBe('https://api.govinfo.gov');
    expect(client.rateLimitDelay).toBe(100);
  });

  test('should construct correct request URL', () => {
    const url = client.constructUrl('/collections/BILLS', {
      pageSize: 10,
      offsetMark: '*'
    });
    
    expect(url).toContain('api_key=test-key');
    expect(url).toContain('pageSize=10');
    expect(url).toContain('offsetMark=*');
  });
});

describe('Congress API Client', () => {
  let client;

  beforeEach(() => {
    client = new CongressAPIClient('test-key');
  });

  test('should initialize with correct configuration', () => {
    expect(client.apiKey).toBe('test-key');
    expect(client.baseUrl).toBe('https://api.congress.gov/v3');
    expect(client.rateLimitDelay).toBe(90);
  });

  test('should construct correct bill URL', () => {
    const url = client.constructUrl('/bill/118/house/hr1');
    
    expect(url).toContain('api_key=test-key');
    expect(url).toContain('/bill/118/house/hr1');
  });
});