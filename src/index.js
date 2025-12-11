const { MCPServer } = require('@modelcontextprotocol/sdk/server/mcp');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio');
require('dotenv').config();

/**
 * Main MCP Server entry point
 * Initializes and starts both GovInfo and Congress.gov MCP servers
 */
async function main() {
  console.error('Starting OpenDiscourse MCP Servers...');
  
  // Check for required environment variables
  if (!process.env.GOVINFO_API_KEY) {
    console.error('Error: GOVINFO_API_KEY environment variable is required');
    process.exit(1);
  }
  
  if (!process.env.CONGRESS_API_KEY) {
    console.error('Error: CONGRESS_API_KEY environment variable is required');
    process.exit(1);
  }

  // Create MCP server
  const server = new MCPServer({
    name: 'opendiscourse-mcp',
    version: '1.0.0',
  }, {
    capabilities: {
      tools: {},
    },
  });

  // Load and register GovInfo server tools
  try {
    const govinfoServer = require('./mcp-servers/govinfo');
    govinfoServer.registerTools(server);
    console.error('GovInfo MCP server tools registered');
  } catch (error) {
    console.error('Failed to load GovInfo server:', error);
  }

  // Load and register Congress.gov server tools
  try {
    const congressServer = require('./mcp-servers/congress');
    congressServer.registerTools(server);
    console.error('Congress.gov MCP server tools registered');
  } catch (error) {
    console.error('Failed to load Congress.gov server:', error);
  }

  // Start the server
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('OpenDiscourse MCP Servers started successfully');
}

if (require.main === module) {
  main().catch((error) => {
    console.error('Server startup failed:', error);
    process.exit(1);
  });
}

module.exports = { main };