"""
Remote MCP Server for Discogs (HTTP/SSE transport)
For deployment to Render, Railway, Fly.io, etc.
"""
import os
import json
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

from .discogs_client import DiscogsClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("discogs-mcp")

# Global client instance
discogs_client: DiscogsClient = None
discogs_username: str = None


def init_discogs_client():
    """Initialize Discogs client from environment variables."""
    global discogs_client, discogs_username

    token = os.environ.get("DISCOGS_TOKEN")
    if not token:
        raise RuntimeError("DISCOGS_TOKEN environment variable not set")

    discogs_username = os.environ.get("DISCOGS_USERNAME", "")
    discogs_client = DiscogsClient(token=token)
    logger.info("Discogs client initialized successfully")


def format_release(release: dict, verbose: bool = False) -> str:
    """Format a release for display."""
    lines = []
    artists = ", ".join([a.get("name", "") for a in release.get("artists", [])])
    title = release.get("title", "Unknown")
    year = release.get("year", "Unknown")
    labels = ", ".join([l.get("name", "") for l in release.get("labels", [])])
    formats = ", ".join([f.get("name", "") for f in release.get("formats", [])])

    lines.append(f"{artists} - {title} ({year})")
    lines.append(f"  Label: {labels}")
    lines.append(f"  Format: {formats}")

    if release.get("id"):
        lines.append(f"  Release ID: {release['id']}")
    if release.get("master_id"):
        lines.append(f"  Master ID: {release['master_id']}")

    if verbose:
        if release.get("genres"):
            lines.append(f"  Genres: {', '.join(release['genres'])}")
        if release.get("styles"):
            lines.append(f"  Styles: {', '.join(release['styles'])}")
        if release.get("country"):
            lines.append(f"  Country: {release['country']}")

        # Tracklist
        if release.get("tracklist"):
            lines.append("  Tracklist:")
            for track in release["tracklist"]:
                pos = track.get("position", "")
                ttitle = track.get("title", "")
                dur = track.get("duration", "")
                lines.append(f"    {pos}. {ttitle} ({dur})" if dur else f"    {pos}. {ttitle}")

        # Notes
        if release.get("notes"):
            lines.append(f"  Notes: {release['notes'][:500]}...")

    return "\n".join(lines)


def format_artist(artist: dict, verbose: bool = False) -> str:
    """Format an artist for display."""
    lines = []
    lines.append(f"Artist: {artist.get('name', 'Unknown')}")

    if artist.get("id"):
        lines.append(f"  ID: {artist['id']}")
    if artist.get("realname"):
        lines.append(f"  Real Name: {artist['realname']}")

    if verbose:
        if artist.get("profile"):
            profile = artist["profile"][:1000]
            lines.append(f"  Profile: {profile}...")
        if artist.get("namevariations"):
            lines.append(f"  Name Variations: {', '.join(artist['namevariations'][:5])}")
        if artist.get("aliases"):
            aliases = [a.get("name", "") for a in artist["aliases"][:5]]
            lines.append(f"  Aliases: {', '.join(aliases)}")
        if artist.get("members"):
            members = [m.get("name", "") for m in artist["members"][:10]]
            lines.append(f"  Members: {', '.join(members)}")
        if artist.get("groups"):
            groups = [g.get("name", "") for g in artist["groups"][:5]]
            lines.append(f"  Groups: {', '.join(groups)}")

    return "\n".join(lines)


def format_label(label: dict, verbose: bool = False) -> str:
    """Format a label for display."""
    lines = []
    lines.append(f"Label: {label.get('name', 'Unknown')}")

    if label.get("id"):
        lines.append(f"  ID: {label['id']}")

    if verbose:
        if label.get("profile"):
            profile = label["profile"][:1000]
            lines.append(f"  Profile: {profile}...")
        if label.get("contact_info"):
            lines.append(f"  Contact: {label['contact_info']}")
        if label.get("parent_label"):
            lines.append(f"  Parent Label: {label['parent_label'].get('name', '')}")
        if label.get("sublabels"):
            sublabels = [s.get("name", "") for s in label["sublabels"][:10]]
            lines.append(f"  Sublabels: {', '.join(sublabels)}")

    return "\n".join(lines)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools for Discogs research."""
    return [
        Tool(
            name="discogs_search",
            description="Search the Discogs database for releases, artists, labels, or masters. Returns key info and IDs for further lookup.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "General search query",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["release", "master", "artist", "label"],
                        "description": "Type of result to return",
                    },
                    "artist": {
                        "type": "string",
                        "description": "Filter by artist name",
                    },
                    "title": {
                        "type": "string",
                        "description": "Filter by release title",
                    },
                    "label": {
                        "type": "string",
                        "description": "Filter by label name",
                    },
                    "genre": {
                        "type": "string",
                        "description": "Filter by genre (e.g., 'Electronic', 'Rock')",
                    },
                    "style": {
                        "type": "string",
                        "description": "Filter by style (e.g., 'Ambient', 'Krautrock')",
                    },
                    "country": {
                        "type": "string",
                        "description": "Filter by country (e.g., 'Germany', 'UK')",
                    },
                    "year": {
                        "type": "string",
                        "description": "Filter by year (e.g., '1975' or '1970-1980')",
                    },
                    "format": {
                        "type": "string",
                        "description": "Filter by format (e.g., 'Vinyl', 'CD', 'Cassette')",
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page (1-100)",
                        "default": 10,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1,
                    },
                },
            },
        ),
        Tool(
            name="discogs_get_release",
            description="Get detailed information about a specific release including tracklist, credits, notes, and market data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "release_id": {
                        "type": "integer",
                        "description": "Discogs release ID",
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency for price data (USD, EUR, GBP, etc.)",
                    },
                },
                "required": ["release_id"],
            },
        ),
        Tool(
            name="discogs_get_master",
            description="Get master release info - the canonical version that groups all pressings/versions together.",
            inputSchema={
                "type": "object",
                "properties": {
                    "master_id": {
                        "type": "integer",
                        "description": "Discogs master release ID",
                    },
                },
                "required": ["master_id"],
            },
        ),
        Tool(
            name="discogs_get_master_versions",
            description="Get all versions/pressings of a master release. Useful for finding specific pressings, countries, or formats.",
            inputSchema={
                "type": "object",
                "properties": {
                    "master_id": {
                        "type": "integer",
                        "description": "Discogs master release ID",
                    },
                    "format": {
                        "type": "string",
                        "description": "Filter by format (Vinyl, CD, etc.)",
                    },
                    "country": {
                        "type": "string",
                        "description": "Filter by country",
                    },
                    "label": {
                        "type": "string",
                        "description": "Filter by label",
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page",
                        "default": 25,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1,
                    },
                },
                "required": ["master_id"],
            },
        ),
        Tool(
            name="discogs_get_artist",
            description="Get detailed artist information including bio/profile, aliases, members (for groups), and groups (for individuals).",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist_id": {
                        "type": "integer",
                        "description": "Discogs artist ID",
                    },
                },
                "required": ["artist_id"],
            },
        ),
        Tool(
            name="discogs_get_artist_releases",
            description="Get an artist's discography - all releases they appear on.",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist_id": {
                        "type": "integer",
                        "description": "Discogs artist ID",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["year", "title", "format"],
                        "description": "Sort field",
                        "default": "year",
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "default": "asc",
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page",
                        "default": 25,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1,
                    },
                },
                "required": ["artist_id"],
            },
        ),
        Tool(
            name="discogs_get_label",
            description="Get detailed label information including profile, parent label, and sublabels.",
            inputSchema={
                "type": "object",
                "properties": {
                    "label_id": {
                        "type": "integer",
                        "description": "Discogs label ID",
                    },
                },
                "required": ["label_id"],
            },
        ),
        Tool(
            name="discogs_get_label_releases",
            description="Get all releases from a label's catalog.",
            inputSchema={
                "type": "object",
                "properties": {
                    "label_id": {
                        "type": "integer",
                        "description": "Discogs label ID",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["year", "title", "format"],
                        "description": "Sort field",
                        "default": "year",
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "default": "asc",
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page",
                        "default": 25,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1,
                    },
                },
                "required": ["label_id"],
            },
        ),
        Tool(
            name="discogs_get_user_collection",
            description="Get items from a user's collection. Use folder_id=0 for all items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Discogs username (optional - uses authenticated user if not provided)",
                    },
                    "folder_id": {
                        "type": "integer",
                        "description": "Collection folder ID (0 = all)",
                        "default": 0,
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page",
                        "default": 25,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1,
                    },
                },
            },
        ),
        Tool(
            name="discogs_get_user_wantlist",
            description="Get a user's wantlist - releases they want to acquire.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Discogs username (optional - uses authenticated user if not provided)",
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "Results per page",
                        "default": 25,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number",
                        "default": 1,
                    },
                },
            },
        ),
        Tool(
            name="discogs_get_release_stats",
            description="Get marketplace statistics for a release - how many people have it (haves), want it (wants), and price data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "release_id": {
                        "type": "integer",
                        "description": "Discogs release ID",
                    },
                },
                "required": ["release_id"],
            },
        ),
        Tool(
            name="discogs_get_collection_value",
            description="Get the estimated minimum, median, and maximum value of a user's collection.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Discogs username (optional - uses authenticated user if not provided)",
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""
    try:
        if name == "discogs_search":
            results = await discogs_client.search(
                query=arguments.get("query"),
                type=arguments.get("type"),
                title=arguments.get("title"),
                artist=arguments.get("artist"),
                label=arguments.get("label"),
                genre=arguments.get("genre"),
                style=arguments.get("style"),
                country=arguments.get("country"),
                year=arguments.get("year"),
                format=arguments.get("format"),
                per_page=arguments.get("per_page", 10),
                page=arguments.get("page", 1),
            )

            pagination = results.get("pagination", {})
            items = results.get("results", [])

            if not items:
                return [TextContent(type="text", text="No results found.")]

            lines = [f"Found {pagination.get('items', len(items))} results (page {pagination.get('page', 1)} of {pagination.get('pages', 1)}):\n"]

            for item in items:
                item_type = item.get("type", "release")
                title = item.get("title", "Unknown")

                if item_type == "artist":
                    lines.append(f"[Artist] {title}")
                    lines.append(f"  ID: {item.get('id')}")
                elif item_type == "label":
                    lines.append(f"[Label] {title}")
                    lines.append(f"  ID: {item.get('id')}")
                else:  # release or master
                    year = item.get("year", "")
                    label_info = ", ".join(item.get("label", [])[:2])
                    format_info = ", ".join(item.get("format", [])[:2])
                    lines.append(f"[{item_type.title()}] {title}" + (f" ({year})" if year else ""))
                    lines.append(f"  Label: {label_info}")
                    lines.append(f"  Format: {format_info}")
                    if item_type == "master":
                        lines.append(f"  Master ID: {item.get('id')}")
                    else:
                        lines.append(f"  Release ID: {item.get('id')}")
                        if item.get("master_id"):
                            lines.append(f"  Master ID: {item.get('master_id')}")
                lines.append("")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "discogs_get_release":
            release = await discogs_client.get_release(
                release_id=arguments["release_id"],
                currency=arguments.get("currency"),
            )
            return [TextContent(type="text", text=format_release(release, verbose=True))]

        elif name == "discogs_get_master":
            master = await discogs_client.get_master_release(
                master_id=arguments["master_id"]
            )
            lines = []
            artists = ", ".join([a.get("name", "") for a in master.get("artists", [])])
            lines.append(f"Master: {artists} - {master.get('title', 'Unknown')}")
            lines.append(f"Master ID: {master.get('id')}")
            lines.append(f"Year: {master.get('year', 'Unknown')}")

            if master.get("genres"):
                lines.append(f"Genres: {', '.join(master['genres'])}")
            if master.get("styles"):
                lines.append(f"Styles: {', '.join(master['styles'])}")

            lines.append(f"Main Release ID: {master.get('main_release')}")
            lines.append(f"Versions Count: {master.get('versions_count', 0)}")

            if master.get("tracklist"):
                lines.append("\nTracklist:")
                for track in master["tracklist"]:
                    pos = track.get("position", "")
                    title = track.get("title", "")
                    dur = track.get("duration", "")
                    lines.append(f"  {pos}. {title}" + (f" ({dur})" if dur else ""))

            if master.get("notes"):
                lines.append(f"\nNotes: {master['notes'][:500]}...")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "discogs_get_master_versions":
            versions = await discogs_client.get_master_release_versions(
                master_id=arguments["master_id"],
                format=arguments.get("format"),
                country=arguments.get("country"),
                label=arguments.get("label"),
                per_page=arguments.get("per_page", 25),
                page=arguments.get("page", 1),
            )

            pagination = versions.get("pagination", {})
            items = versions.get("versions", [])

            if not items:
                return [TextContent(type="text", text="No versions found.")]

            lines = [f"Found {pagination.get('items', len(items))} versions (page {pagination.get('page', 1)} of {pagination.get('pages', 1)}):\n"]

            for v in items:
                title = v.get("title", "Unknown")
                year = v.get("released", "")
                country = v.get("country", "")
                label = v.get("label", "")
                format_str = v.get("format", "")

                lines.append(f"{title}" + (f" ({year})" if year else ""))
                lines.append(f"  Release ID: {v.get('id')}")
                lines.append(f"  Country: {country} | Label: {label}")
                lines.append(f"  Format: {format_str}")
                lines.append("")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "discogs_get_artist":
            artist = await discogs_client.get_artist(artist_id=arguments["artist_id"])
            return [TextContent(type="text", text=format_artist(artist, verbose=True))]

        elif name == "discogs_get_artist_releases":
            releases = await discogs_client.get_artist_releases(
                artist_id=arguments["artist_id"],
                sort=arguments.get("sort", "year"),
                sort_order=arguments.get("sort_order", "asc"),
                per_page=arguments.get("per_page", 25),
                page=arguments.get("page", 1),
            )

            pagination = releases.get("pagination", {})
            items = releases.get("releases", [])

            if not items:
                return [TextContent(type="text", text="No releases found.")]

            lines = [f"Found {pagination.get('items', len(items))} releases (page {pagination.get('page', 1)} of {pagination.get('pages', 1)}):\n"]

            for r in items:
                title = r.get("title", "Unknown")
                year = r.get("year", "")
                role = r.get("role", "")
                format_str = r.get("format", "")

                lines.append(f"{title}" + (f" ({year})" if year else ""))
                lines.append(f"  Role: {role}")
                lines.append(f"  Format: {format_str}")
                lines.append(f"  ID: {r.get('id')} (type: {r.get('type', 'release')})")
                lines.append("")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "discogs_get_label":
            label = await discogs_client.get_label(label_id=arguments["label_id"])
            return [TextContent(type="text", text=format_label(label, verbose=True))]

        elif name == "discogs_get_label_releases":
            releases = await discogs_client.get_label_releases(
                label_id=arguments["label_id"],
                sort=arguments.get("sort", "year"),
                sort_order=arguments.get("sort_order", "asc"),
                per_page=arguments.get("per_page", 25),
                page=arguments.get("page", 1),
            )

            pagination = releases.get("pagination", {})
            items = releases.get("releases", [])

            if not items:
                return [TextContent(type="text", text="No releases found.")]

            lines = [f"Found {pagination.get('items', len(items))} releases (page {pagination.get('page', 1)} of {pagination.get('pages', 1)}):\n"]

            for r in items:
                artist = r.get("artist", "Unknown")
                title = r.get("title", "Unknown")
                year = r.get("year", "")
                format_str = r.get("format", "")
                catno = r.get("catno", "")

                lines.append(f"{artist} - {title}" + (f" ({year})" if year else ""))
                lines.append(f"  Cat#: {catno}")
                lines.append(f"  Format: {format_str}")
                lines.append(f"  ID: {r.get('id')}")
                lines.append("")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "discogs_get_user_collection":
            username = arguments.get("username") or discogs_username
            if not username:
                # Try to get from identity
                identity = await discogs_client.get_user_identity()
                username = identity.get("username")

            if not username:
                return [TextContent(type="text", text="Error: Username required. Set DISCOGS_USERNAME or provide username parameter.")]

            collection = await discogs_client.get_user_collection_items(
                username=username,
                folder_id=arguments.get("folder_id", 0),
                per_page=arguments.get("per_page", 25),
                page=arguments.get("page", 1),
            )

            pagination = collection.get("pagination", {})
            items = collection.get("releases", [])

            if not items:
                return [TextContent(type="text", text="No items in collection.")]

            lines = [f"Collection ({pagination.get('items', len(items))} items, page {pagination.get('page', 1)} of {pagination.get('pages', 1)}):\n"]

            for item in items:
                info = item.get("basic_information", {})
                artists = ", ".join([a.get("name", "") for a in info.get("artists", [])])
                title = info.get("title", "Unknown")
                year = info.get("year", "")

                lines.append(f"{artists} - {title}" + (f" ({year})" if year else ""))
                lines.append(f"  Release ID: {info.get('id')}")
                lines.append(f"  Format: {', '.join([f.get('name', '') for f in info.get('formats', [])])}")
                lines.append("")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "discogs_get_user_wantlist":
            username = arguments.get("username") or discogs_username
            if not username:
                identity = await discogs_client.get_user_identity()
                username = identity.get("username")

            if not username:
                return [TextContent(type="text", text="Error: Username required. Set DISCOGS_USERNAME or provide username parameter.")]

            wantlist = await discogs_client.get_user_wantlist(
                username=username,
                per_page=arguments.get("per_page", 25),
                page=arguments.get("page", 1),
            )

            pagination = wantlist.get("pagination", {})
            items = wantlist.get("wants", [])

            if not items:
                return [TextContent(type="text", text="Wantlist is empty.")]

            lines = [f"Wantlist ({pagination.get('items', len(items))} items, page {pagination.get('page', 1)} of {pagination.get('pages', 1)}):\n"]

            for item in items:
                info = item.get("basic_information", {})
                artists = ", ".join([a.get("name", "") for a in info.get("artists", [])])
                title = info.get("title", "Unknown")
                year = info.get("year", "")

                lines.append(f"{artists} - {title}" + (f" ({year})" if year else ""))
                lines.append(f"  Release ID: {info.get('id')}")
                if item.get("notes"):
                    lines.append(f"  Notes: {item['notes']}")
                lines.append("")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "discogs_get_release_stats":
            stats = await discogs_client.get_release_stats(
                release_id=arguments["release_id"]
            )

            lines = [f"Marketplace Stats for Release {arguments['release_id']}:"]
            lines.append(f"  In Collections (Haves): {stats.get('num_have', 'N/A')}")
            lines.append(f"  In Wantlists (Wants): {stats.get('num_want', 'N/A')}")

            if stats.get("lowest_price"):
                lowest = stats["lowest_price"]
                lines.append(f"  Lowest Price: {lowest.get('currency', '')} {lowest.get('value', 'N/A')}")

            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "discogs_get_collection_value":
            username = arguments.get("username") or discogs_username
            if not username:
                identity = await discogs_client.get_user_identity()
                username = identity.get("username")

            if not username:
                return [TextContent(type="text", text="Error: Username required. Set DISCOGS_USERNAME or provide username parameter.")]

            value = await discogs_client.get_user_collection_value(username=username)

            lines = [f"Collection Value for {username}:"]
            lines.append(f"  Minimum: {value.get('minimum', 'N/A')}")
            lines.append(f"  Median: {value.get('median', 'N/A')}")
            lines.append(f"  Maximum: {value.get('maximum', 'N/A')}")

            return [TextContent(type="text", text="\n".join(lines))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# SSE transport for MCP
sse = SseServerTransport("/messages/")


async def handle_sse(request):
    """Handle SSE connection for MCP."""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(
            streams[0], streams[1], app.create_initialization_options()
        )


async def handle_messages(request):
    """Handle POST messages for MCP."""
    await sse.handle_post_message(request.scope, request.receive, request._send)


async def health(request):
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "service": "discogs-mcp"})


# Starlette app with routes
starlette_app = Starlette(
    debug=False,
    routes=[
        Route("/health", health),
        Route("/sse", handle_sse),
        Route("/messages/", handle_messages, methods=["POST"]),
    ],
)


def main():
    """Run the HTTP server."""
    init_discogs_client()

    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Discogs MCP server on port {port}")

    uvicorn.run(starlette_app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
