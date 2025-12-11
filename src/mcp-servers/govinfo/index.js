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

module.exports = GovInfoMCPServer;