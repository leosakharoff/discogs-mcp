# Discogs MCP

MCP server for Discogs music database research. Search releases, artists, labels, and access your collection/wantlist.

## Features

- Search the Discogs database (releases, artists, labels, masters)
- Get detailed release info with tracklist, credits, and market data
- Browse artist discographies and label catalogs
- Access user collections and wantlists
- Get marketplace statistics and collection value

## Tools

| Tool | Description |
|------|-------------|
| `discogs_search` | Search for releases, artists, labels, or masters |
| `discogs_get_release` | Get detailed release info (tracklist, credits, notes) |
| `discogs_get_master` | Get master release (canonical version grouping all pressings) |
| `discogs_get_master_versions` | List all versions/pressings of a master |
| `discogs_get_artist` | Get artist bio, aliases, members, groups |
| `discogs_get_artist_releases` | Get artist's discography |
| `discogs_get_label` | Get label info, sublabels |
| `discogs_get_label_releases` | Get label's catalog |
| `discogs_get_user_collection` | Get user's record collection |
| `discogs_get_user_wantlist` | Get user's wantlist |
| `discogs_get_release_stats` | Get marketplace stats (haves, wants, prices) |
| `discogs_get_collection_value` | Get estimated collection value |

## Deploy to Render

1. Fork this repo
2. Get a Discogs token from [Discogs Settings](https://www.discogs.com/settings/developers)
3. Go to [Render Dashboard](https://dashboard.render.com/select-repo?type=blueprint)
4. Select your forked repo
5. Set environment variables:
   - `DISCOGS_TOKEN`: Your Discogs personal access token
   - `DISCOGS_USERNAME`: Your Discogs username (optional, for collection access)
6. Click **Apply**

## Configure Claude

Add to `~/.mcp.json`:

```json
{
  "mcpServers": {
    "discogs": {
      "url": "https://your-app.onrender.com/sse"
    }
  }
}
```

Restart Claude Code to activate.

## Example Usage

```
"Search Discogs for Kraftwerk Autobahn"
"Get info about release 123456"
"Show me all versions of this master release"
"What's in my Discogs collection?"
"How much is my collection worth?"
```

## Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export DISCOGS_TOKEN=your_token
export DISCOGS_USERNAME=your_username

python -m src.server_remote
```

Server runs on `http://localhost:8000`

## Getting a Discogs Token

1. Go to [Discogs Developer Settings](https://www.discogs.com/settings/developers)
2. Click **Generate new token**
3. Copy the token

## License

MIT
