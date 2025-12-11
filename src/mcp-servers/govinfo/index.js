const GovInfoAPIClient = require('./client');

/**
 * GovInfo MCP Server Tools
 * Provides MCP tools for accessing GovInfo API data
 */
class GovInfoMCPServer {
  constructor(apiKey) {
    this.client = new GovInfoAPIClient(apiKey);
  }

  /**
   * Register all GovInfo tools with the MCP server
   */
  registerTools(server) {
    // List collections
    server.setRequestHandler('tools/list', async () => ({
      tools: [
        {
          name: 'govinfo_list_collections',
          description: 'List collections updated since a specific date',
          inputSchema: {
            type: 'object',
            properties: {
              collectionCode: {
                type: 'string',
                description: 'Collection code (e.g., BILLS, CREC, FR, CFR)',
                enum: ['BILLS', 'CREC', 'FR', 'CFR', 'USCOURTS', 'CHRG']
              },
              fromDate: {
                type: 'string',
                description: 'ISO date string (e.g., 2023-01-01T00:00:00Z)'
              },
              pageSize: {
                type: 'number',
                description: 'Number of results to return (max 100)',
                default: 20,
                minimum: 1,
                maximum: 100
              }
            },
            required: ['collectionCode', 'fromDate']
          }
        },
        {
          name: 'govinfo_get_package',
          description: 'Get detailed information about a specific package',
          inputSchema: {
            type: 'object',
            properties: {
              packageId: {
                type: 'string',
                description: 'Package ID (e.g., CREC-2023-01-01, BILLS-118hr1enr)'
              }
            },
            required: ['packageId']
          }
        },
        {
          name: 'govinfo_list_granules',
          description: 'List granules within a package',
          inputSchema: {
            type: 'object',
            properties: {
              packageId: {
                type: 'string',
                description: 'Package ID'
              },
              offset: {
                type: 'number',
                description: 'Starting offset',
                default: 0,
                minimum: 0
              },
              pageSize: {
                type: 'number',
                description: 'Number of granules to return',
                default: 50,
                minimum: 1,
                maximum: 250
              }
            },
            required: ['packageId']
          }
        },
        {
          name: 'govinfo_get_granule',
          description: 'Get detailed information about a specific granule',
          inputSchema: {
            type: 'object',
            properties: {
              packageId: {
                type: 'string',
                description: 'Package ID'
              },
              granuleId: {
                type: 'string',
                description: 'Granule ID'
              }
            },
            required: ['packageId', 'granuleId']
          }
        },
        {
          name: 'govinfo_download_content',
          description: 'Download content from GovInfo (PDF, XML, HTML)',
          inputSchema: {
            type: 'object',
            properties: {
              downloadUrl: {
                type: 'string',
                description: 'Download URL from GovInfo API response'
              },
              format: {
                type: 'string',
                description: 'Content format',
                enum: ['pdf', 'xml', 'htm', 'zip'],
                default: 'pdf'
              }
            },
            required: ['downloadUrl']
          }
        },
        {
          name: 'govinfo_list_118th_bills',
          description: 'List processed 118th Congress bills from local database',
          inputSchema: {
            type: 'object',
            properties: {
              billType: {
                type: 'string',
                description: 'Filter by bill type (hr, s, hconres, etc.)',
                enum: ['hr', 's', 'hconres', 'sconres', 'hjres', 'sjres']
              },
              session: {
                type: 'number',
                description: 'Filter by session (1 or 2)',
                minimum: 1,
                maximum: 2
              },
              limit: {
                type: 'number',
                description: 'Maximum number of results to return',
                default: 20,
                minimum: 1,
                maximum: 100
              },
              offset: {
                type: 'number',
                description: 'Number of results to skip (for pagination)',
                default: 0,
                minimum: 0
              }
            }
          }
        },
        {
          name: 'govinfo_get_118th_bill',
          description: 'Get detailed information about a specific 118th Congress bill',
          inputSchema: {
            type: 'object',
            properties: {
              billId: {
                type: 'string',
                description: 'Bill ID (e.g., hr366, s2403)',
                pattern: '^[a-z]+\\d+$'
              }
            },
            required: ['billId']
          }
        },
        {
          name: 'govinfo_search_118th_bills',
          description: 'Search 118th Congress bills by text content',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query for bill titles and content',
                minLength: 2
              },
              billType: {
                type: 'string',
                description: 'Filter by bill type (hr, s, hconres, etc.)',
                enum: ['hr', 's', 'hconres', 'sconres', 'hjres', 'sjres']
              },
              session: {
                type: 'number',
                description: 'Filter by session (1 or 2)',
                minimum: 1,
                maximum: 2
              },
              limit: {
                type: 'number',
                description: 'Maximum number of results to return',
                default: 10,
                minimum: 1,
                maximum: 50
              }
            },
            required: ['query']
          }
        }
      ]
    }));

    // Handle tool calls
    server.setRequestHandler('tools/call', async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        switch (name) {
          case 'govinfo_list_collections':
            return await this.listCollections(args);
          case 'govinfo_get_package':
            return await this.getPackage(args);
          case 'govinfo_list_granules':
            return await this.listGranules(args);
          case 'govinfo_get_granule':
            return await this.getGranule(args);
           case 'govinfo_download_content':
             return await this.downloadContent(args);
           case 'govinfo_list_118th_bills':
             return await this.list118thBills(args);
           case 'govinfo_get_118th_bill':
             return await this.get118thBill(args);
           case 'govinfo_search_118th_bills':
             return await this.search118thBills(args);
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

  async listCollections(args) {
    const { collectionCode, fromDate, pageSize = 20 } = args;
    
    const data = await this.client.getCollections(collectionCode, fromDate, pageSize);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async getPackage(args) {
    const { packageId } = args;
    
    const data = await this.client.getPackageSummary(packageId);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async listGranules(args) {
    const { packageId, offset = 0, pageSize = 50 } = args;
    
    const data = await this.client.getPackageGranules(packageId, offset, pageSize);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async getGranule(args) {
    const { packageId, granuleId } = args;
    
    const data = await this.client.getGranuleSummary(packageId, granuleId);
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(data, null, 2)
      }]
    };
  }

  async downloadContent(args) {
    const { downloadUrl, format = 'pdf' } = args;
    
    // Ensure URL has API key
    const url = new URL(downloadUrl);
    if (!url.searchParams.has('api_key')) {
      url.searchParams.set('api_key', this.client.apiKey);
    }
    
    const data = await this.client.downloadContent(url.toString());
    
    // For binary content, we'll return metadata
    const contentInfo = {
      downloadUrl,
      format,
      size: data.length,
      timestamp: new Date().toISOString()
    };
    
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(contentInfo, null, 2)
      }]
      };
    }
  }

  async list118thBills(args) {
    const { billType, session, limit = 20, offset = 0 } = args;
    
    try {
      const sqlite3 = require('sqlite3').verbose();
      const db = new sqlite3.Database('data/govinfo_downloads.db');
      
      let query = `
        SELECT bill_id, bill_type, bill_number, title, official_title, 
               sponsor_name, sponsor_party, sponsor_state, introduced_date,
               current_chamber, bill_stage, congress, session
        FROM bills 
        WHERE congress = 118
      `;
      const params = [];
      
      if (billType) {
        query += ' AND bill_type = ?';
        params.push(billType);
      }
      
      if (session) {
        query += ' AND session = ?';
        params.push(session);
      }
      
      query += ' ORDER BY bill_number LIMIT ? OFFSET ?';
      params.push(limit, offset);
      
      return new Promise((resolve, reject) => {
        db.all(query, params, (err, rows) => {
          if (err) {
            reject(err);
          } else {
            resolve({
              content: [{
                type: 'text',
                text: JSON.stringify(rows, null, 2)
              }],
              results: rows.length
            });
          }
        });
      });
      
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error listing 118th Congress bills: ${error.message}`
        }],
        isError: true
      };
    }
  }

  async get118thBill(args) {
    const { billId } = args;
    
    try {
      const sqlite3 = require('sqlite3').verbose();
      const db = new sqlite3.Database('data/govinfo_downloads.db');
      
      // Get bill details
      const billQuery = `
        SELECT * FROM bills WHERE bill_id = ? AND congress = 118
      `;
      
      // Get bill sections
      const sectionsQuery = `
        SELECT section_id, section_type, section_number, header, content, level, order_index
        FROM bill_sections 
        WHERE bill_id = ? 
        ORDER BY order_index
      `;
      
      return new Promise((resolve, reject) => {
        db.get(billQuery, [billId], (err, bill) => {
          if (err) {
            reject(err);
            return;
          }
          
          if (!bill) {
            resolve({
              content: [{
                type: 'text',
                text: `Bill ${billId} not found in 118th Congress database`
              }],
              isError: true
            });
            return;
          }
          
          db.all(sectionsQuery, [billId], (err, sections) => {
            if (err) {
              reject(err);
            } else {
              resolve({
                content: [{
                  type: 'text',
                  text: JSON.stringify({
                    bill: bill,
                    sections: sections
                  }, null, 2)
                }],
                bill: bill,
                sections: sections
              });
            }
          });
        });
      });
      
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error getting 118th Congress bill: ${error.message}`
        }],
        isError: true
      };
    }
  }

  async search118thBills(args) {
    const { query: searchQuery, billType, session, limit = 10 } = args;
    
    try {
      const sqlite3 = require('sqlite3').verbose();
      const db = new sqlite3.Database('data/govinfo_downloads.db');
      
      let sql = `
        SELECT bill_id, bill_type, bill_number, title, official_title,
               sponsor_name, sponsor_party, sponsor_state, introduced_date,
               current_chamber, bill_stage, congress, session
        FROM bills 
        WHERE congress = 118 AND (
          title LIKE ? OR official_title LIKE ?
        )
      `;
      const params = [`%${searchQuery}%`, `%${searchQuery}%`];
      
      if (billType) {
        sql += ' AND bill_type = ?';
        params.push(billType);
      }
      
      if (session) {
        sql += ' AND session = ?';
        params.push(session);
      }
      
      sql += ' ORDER BY bill_number LIMIT ?';
      params.push(limit);
      
      return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
          if (err) {
            reject(err);
          } else {
            resolve({
              content: [{
                type: 'text',
                text: JSON.stringify(rows, null, 2)
              }],
              results: rows.length,
              query: searchQuery
            });
          }
        });
      });
      
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error searching 118th Congress bills: ${error.message}`
        }],
        isError: true
      };
    }
  }
}

module.exports = GovInfoMCPServer;