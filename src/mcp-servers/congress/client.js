const axios = require('axios');

/**
 * Congress.gov API Client
 * Handles communication with Congress.gov API
 */
class CongressAPIClient {
  constructor(apiKey, baseUrl = 'https://api.congress.gov/v3') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.rateLimitDelay = 90; // ~40 requests per second to stay under 5000/hour
  }

  /**
   * Make a request to Congress.gov API
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
      console.error(`Congress.gov API Request: ${url.toString()}`);
      
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
      console.error(`Congress.gov API Error: ${error.message}`);
      if (error.response) {
        console.error(`Response status: ${error.response.status}`);
        console.error(`Response data:`, error.response.data);
      }
      throw error;
    }
  }

  /**
   * Get bill information
   */
  async getBill(congress, chamber, billNumber, format = 'json') {
    return this.request(`/bill/${congress}/${chamber}/${billNumber}`, {
      format
    });
  }

  /**
   * Get bill actions
   */
  async getBillActions(congress, chamber, billNumber, limit = 20, offset = 0) {
    return this.request(`/bill/${congress}/${chamber}/${billNumber}/actions`, {
      limit,
      offset
    });
  }

  /**
   * Get bill amendments
   */
  async getBillAmendments(congress, chamber, billNumber, limit = 20, offset = 0) {
    return this.request(`/bill/${congress}/${chamber}/${billNumber}/amendments`, {
      limit,
      offset
    });
  }

  /**
   * Get bill cosponsors
   */
  async getBillCosponsors(congress, chamber, billNumber, limit = 20, offset = 0) {
    return this.request(`/bill/${congress}/${chamber}/${billNumber}/cosponsors`, {
      limit,
      offset
    });
  }

  /**
   * Get bill text
   */
  async getBillText(congress, chamber, billNumber, format = 'json') {
    return this.request(`/bill/${congress}/${chamber}/${billNumber}/text`, {
      format
    });
  }

  /**
   * Search bills
   */
  async searchBills(query, congress = null, limit = 20, offset = 0) {
    const params = {
      q: query,
      limit,
      offset
    };
    
    if (congress) {
      params.congress = congress;
    }
    
    return this.request('/bill', params);
  }

  /**
   * Get member information
   */
  async getMember(memberId, format = 'json') {
    return this.request(`/member/${memberId}`, {
      format
    });
  }

  /**
   * Search members
   */
  async searchMembers(query, limit = 20, offset = 0) {
    return this.request('/member', {
      q: query,
      limit,
      offset
    });
  }

  /**
   * Get committee information
   */
  async getCommittee(chamber, committeeCode, format = 'json') {
    return this.request(`/committee/${chamber}/${committeeCode}`, {
      format
    });
  }

  /**
   * Get committee meetings
   */
  async getCommitteeMeetings(chamber = null, congress = null, limit = 20, offset = 0) {
    const params = {
      limit,
      offset
    };
    
    if (chamber) params.chamber = chamber;
    if (congress) params.congress = congress;
    
    return this.request('/committee-meeting', params);
  }

  /**
   * Get nominations
   */
  async getNominations(congress = null, limit = 20, offset = 0) {
    const params = {
      limit,
      offset
    };
    
    if (congress) params.congress = congress;
    
    return this.request('/nomination', params);
  }

  /**
   * Get roll call votes
   */
  async getRollCallVotes(congress, chamber, sessionNumber, rollCallNumber, format = 'json') {
    return this.request(`/roll-call-vote/${congress}/${chamber}/${sessionNumber}/${rollCallNumber}`, {
      format
    });
  }
}

module.exports = CongressAPIClient;