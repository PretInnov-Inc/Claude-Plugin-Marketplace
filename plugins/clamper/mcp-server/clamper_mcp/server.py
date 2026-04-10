"""Clamper MCP Server — What Claude Code genuinely lacks.

1. Deep Project DNA (dna_analyzer) — live architecture analysis from git/deps/tests
2. Outcome Store (outcome_store) — verification outcome persistence and pattern learning

Run: python -m clamper_mcp.server
"""

from fastmcp import FastMCP

# Create the unified Clamper MCP server
server = FastMCP(
    "clamper",
    instructions=(
        "Clamper MCP Server provides two tool groups:\n"
        "1. DNA tools (extract_project_dna, get_fragile_zones, get_coupling_map, get_hot_files) "
        "— analyze project architecture, git history, test coverage\n"
        "2. Outcome tools (record_verification, query_outcomes, get_quality_trend, get_fragile_file_history) "
        "— store and query verification results for pattern learning"
    )
)

# Import and mount the tool servers
from clamper_mcp.tools.dna_analyzer import mcp as dna_mcp
from clamper_mcp.tools.outcome_store import mcp as outcome_mcp

server.mount("dna", dna_mcp)
server.mount("outcomes", outcome_mcp)


def main():
    """Run the Clamper MCP server."""
    server.run()


if __name__ == "__main__":
    main()
