const axios = require('axios');
const xml2js = require('xml2js');

/**
 * GovInfo API Client
 * Handles communication with the GovInfo API
 */
class GovInfoAPIClient {
  constructor(apiKey, baseUrl = 'https://api.govinfo.gov') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.rateLimitDelay = 100; // 100ms between requests to respect rate limits
  }

  /**
   * Make a request to the GovInfo API
   */
  async request(endpoint, params = {}) {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    
    // Add API key
    url.searchParams.set('api_key', this.apiKey);
    
    // Add other parameters
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, value);
      }
    });

    try {
      console.error(`GovInfo API Request: ${url.toString()}`);
      
      const response = await axios.get(url.toString(), {
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'OpenDiscourse-MCP/1.0.0'
        },
        timeout: 30000
      });

      // Rate limiting
      await new Promise(resolve => setTimeout(resolve, this.rateLimitDelay));
      
      return response.data;
    } catch (error) {
      console.error(`GovInfo API Error: ${error.message}`);
      if (error.response) {
        console.error(`Response status: ${error.response.status}`);
        console.error(`Response data:`, error.response.data);
      }
      throw error;
    }
  }

  /**
   * Get collections updated since a specific date
   */
  async getCollections(collectionCode, fromDate, pageSize = 20, offsetMark = '*') {
    return this.request(`/collections/${collectionCode}/${fromDate}`, {
      pageSize,
      offsetMark
    });
  }

  /**
   * Get package summary
   */
  async getPackageSummary(packageId) {
    return this.request(`/packages/${packageId}/summary`);
  }

  /**
   * Get package granules
   */
  async getPackageGranules(packageId, offset = 0, pageSize = 100) {
    return this.request(`/packages/${packageId}/granules`, {
      offset,
      pageSize
    });
  }

  /**
   * Get granule summary
   */
  async getGranuleSummary(packageId, granuleId) {
    return this.request(`/packages/${packageId}/granules/${granuleId}/summary`);
  }

  /**
   * Download content file
   */
  async downloadContent(downloadUrl) {
    try {
      const response = await axios.get(downloadUrl, {
        responseType: 'arraybuffer',
        timeout: 60000 // 60 seconds for downloads
      });
      return response.data;
    } catch (error) {
      console.error(`Download error: ${error.message}`);
      throw error;
    }
  }

  /**
   * Parse XML content
   */
  async parseXML(xmlContent) {
    const parser = new xml2js.Parser();
    return parser.parseStringPromise(xmlContent);
  }
}

module.exports = GovInfoAPIClient;