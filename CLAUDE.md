# Discogs MCP

MCP server til Discogs database research.

## Tools

### discogs_search
Søg i Discogs databasen.
- `query`: Søgeord
- `type`: "release", "master", "artist", "label"
- `artist`, `title`, `label`, `genre`, `style`, `country`, `year`, `format`: Filtre
- `per_page`, `page`: Pagination

### discogs_get_release
Hent release detaljer.
- `release_id` (required): Discogs release ID
- `currency`: Valuta for prisdata (USD, EUR, etc.)

### discogs_get_master
Hent master release (grupperer alle pressings).
- `master_id` (required): Discogs master ID

### discogs_get_master_versions
List alle versioner af en master.
- `master_id` (required)
- `format`, `country`, `label`: Filtre
- `per_page`, `page`: Pagination

### discogs_get_artist
Hent kunstner info.
- `artist_id` (required): Discogs artist ID

### discogs_get_artist_releases
Hent kunstners diskografi.
- `artist_id` (required)
- `sort`: "year", "title", "format"
- `sort_order`: "asc", "desc"

### discogs_get_label
Hent label info.
- `label_id` (required): Discogs label ID

### discogs_get_label_releases
Hent labels katalog.
- `label_id` (required)
- `sort`, `sort_order`, `per_page`, `page`

### discogs_get_user_collection
Hent brugers samling.
- `username`: Discogs brugernavn (bruger authenticated user hvis tom)
- `folder_id`: 0 = alle

### discogs_get_user_wantlist
Hent brugers ønskeliste.
- `username`

### discogs_get_release_stats
Hent marketplace statistik.
- `release_id` (required)

Returnerer: antal der har den, antal der vil have den, laveste pris.

### discogs_get_collection_value
Hent estimeret samlings-værdi.
- `username`

## Eksempler

```
# Søg efter album
discogs_search(query="Kraftwerk Autobahn", type="release")

# Hent release detaljer
discogs_get_release(release_id=123456)

# Find alle pressings
discogs_get_master_versions(master_id=1234, country="Germany", format="Vinyl")

# Se samling
discogs_get_user_collection(username="mitteBrugernavn")
```
