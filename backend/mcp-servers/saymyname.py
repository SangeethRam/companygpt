"""Sample test server will be removed in the future."""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("saymyname", port=8003)

@mcp.tool(
    name="saymyname",
    description="Say my name.",
)
def say_my_name() -> str:
    """
    Say my name.
    """
    return f"Hello, Heisenberg!"

if __name__ == "__main__":
    mcp.run(transport="sse")
    # Run the FastMCP server