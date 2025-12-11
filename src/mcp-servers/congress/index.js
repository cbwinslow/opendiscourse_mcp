const CongressAPIClient = require('./client');

/**
 * Congress.gov MCP Server Tools
 * Provides MCP tools for accessing Congress.gov API data
 */
class CongressMCPServer {
  constructor(apiKey) {
    this.client = new CongressAPIClient(apiKey);
  }

  /**
   * Register all Congress.gov tools with MCP server
   */
  registerTools(server) {
    // List tools
    server.setRequestHandler('tools/list', async () => ({
      tools: [
        {
          name: 'congress_get_bill',
          description: 'Get detailed information about a specific bill',
          inputSchema: {
            type: 'object',
            properties: {
              congress: {
                type: 'number',
                description: 'Congress number (e.g., 118 for 118th Congress)',
                minimum: 93,
                maximum: 150
              },
              chamber: {
                type: 'string',
                description: 'Chamber (house or senate)',
                enum: ['house', 'senate']
              },
              billNumber: {
                type: 'string',
                description: 'Bill number (e.g., hr1, s1)'
              }
            },
            required: ['congress', 'chamber', 'billNumber']
          }
        },
        {
          name: 'congress_search_bills',
          description: 'Search for bills by text query',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query terms'
              },
              congress: {
                type: 'number',
                description: 'Filter by Congress number (optional)',
                minimum: 93,
                maximum: 150
              },
              limit: {
                type: 'number',
                description: 'Number of results to return',
                default: 20,
                minimum: 1,
                maximum: 250
              }
            },
            required: ['query']
          }
        },
        {
          name: 'congress_get_bill_actions',
          description: 'Get legislative actions for a bill',
          inputSchema: {
            type: 'object',
            properties: {
              congress: {
                type: 'number',
                description: 'Congress number'
              },
              chamber: {
                type: 'string',
                description: 'Chamber (house or senate)',
                enum: ['house', 'senate']
              },
              billNumber: {
                type: 'string',
                description: 'Bill number'
              },
              limit: {
                type: 'number',
                description: 'Number of actions to return',
                default: 20,
                minimum: 1,
                maximum: 250
              }
            },
            required: ['congress', 'chamber', 'billNumber']
          }
        },
        {
          name: 'congress_get_bill_text',
          description: 'Get full text of a bill',
          inputSchema: {
            type: 'object',
            properties: {
              congress: {
                type: 'number',
                description: 'Congress number'
              },
              chamber: {
                type: 'string',
                description: 'Chamber (house or senate)',
                enum: ['house', 'senate']
              },
              billNumber: {
                type: 'string',
                description: 'Bill number'
              }
            },
            required: ['congress', 'chamber', 'billNumber']
          }
        },
        {
          name: 'congress_search_members',
          description: 'Search for members of Congress',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query (name, state, etc.)'
              },
              limit: {
                type: 'number',
                description: 'Number of results to return',
                default: 20,
                minimum: 1,
                maximum: 250
              }
            },
            required: ['query']
          }
        },
        {
          name: 'congress_get_member',
          description: 'Get detailed information about a specific member',
          inputSchema: {
            type: 'object',
            properties: {
              memberId: {
                type: 'string',
                description: 'Member ID (e.g., S000148)'
              }
            },
            required: ['memberId']
          }
        },
        {
          name: 'congress_get_committee_meetings',
          description: 'Get committee meetings',
          inputSchema: {
            type: 'object',
            properties: {
              chamber: {
                type: 'string',
                description: 'Filter by chamber (house, senate, or null for both)',
                enum: ['house', 'senate']
              },
              congress: {
                type: 'number',
                description: 'Filter by Congress number (optional)',
                minimum: 93,
                maximum: 150
              },
              limit: {
                type: 'number',
                description: 'Number of meetings to return',
                default: 20,
                minimum: 1,
                maximum: 250
              }
            }
          }
        },
        {
          name: 'congress_get_nominations',
          description: 'Get presidential nominations',
          inputSchema: {
            type: 'object',
            properties: {
              congress: {
                type: 'number',
                description: 'Filter by Congress number (optional)',
                minimum: 93,
                maximum: 150
              },
              limit: {
                type: 'number',
                description: 'Number of nominations to return',
                default: 20,
                minimum: 1,
                maximum: 250
              }
            }
          }
        }
      ]
    }));

    // Handle tool calls
    server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        switch (name) {
          case 'congress_get_bill':
            return await this.getBill(args);
          case 'congress_search_bills':
            return await this.searchBills(args);
          case 'congress_get_bill_actions':
            return await this.getBillActions(args);
          case 'congress_get_bill_text':
            return await this.getBillText(args);
          case 'congress_search_members':
            return await this.searchMembers(args);
          case 'congress_get_member':
            return await this.getMember(args);
          case 'congress_get_committee_meetings':
            return await this.getCommitteeMeetings(args);
          case 'congress_get_nominations':
            return await this.getNominations(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [{
            type: 'text',
            text: `Error: ${error.message}`
          }],
          isError: true
        };
      }
    });
  }

  async getBill(args) {
    const { congress, chamber, billNumber } = args;
    
    const data = await this.client.getBill(congress, chamber, billNumber);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async searchBills(args) {
    const { query, congress, limit = 20 } = args;
    
    const data = await this.client.searchBills(query, congress, limit);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async getBillActions(args) {
    const { congress, chamber, billNumber, limit = 20 } = args;
    
    const data = await this.client.getBillActions(congress, chamber, billNumber, limit);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async getBillText(args) {
    const { congress, chamber, billNumber } = args;
    
    const data = await this.client.getBillText(congress, chamber, billNumber);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async searchMembers(args) {
    const { query, limit = 20 } = args;
    
    const data = await this.client.searchMembers(query, limit);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async getMember(args) {
    const { memberId } = args;
    
    const data = await this.client.getMember(memberId);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async getCommitteeMeetings(args) {
    const { chamber, congress, limit = 20 } = args;
    
    const data = await this.client.getCommitteeMeetings(chamber, congress, limit);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async getNominations(args) {
    const { congress, limit = 20 } = args;
    
    const data = await this.client.getNominations(congress, limit);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }
}

module.exports = CongressMCPServer;