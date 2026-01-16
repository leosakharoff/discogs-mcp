# Discogs MCP - Endpoints Reference

**Server URL:** `https://discogs-mcp.onrender.com/sse`

## Endpoints

### discogs_search
Søg i hele Discogs databasen.

```json
{
  "query": "Kraftwerk",
  "type": "release|master|artist|label",
  "artist": "filter by artist",
  "title": "filter by title",
  "label": "filter by label",
  "genre": "Electronic",
  "style": "Krautrock",
  "country": "Germany",
  "year": "1974",
  "format": "Vinyl",
  "per_page": 10,
  "page": 1
}
```

**Brug til:** Første søgning, find release/artist IDs.

---

### discogs_get_release
Hent fuld release info.

```json
{
  "release_id": 123456,
  "currency": "EUR"
}
```

**Returnerer:** Tracklist, credits, labels, styles, notes, images.

**Brug til:** Dyb research på specifik udgivelse. Find producer credits her!

---

### discogs_get_master
Hent master release (kanonisk version).

```json
{
  "master_id": 1234
}
```

**Returnerer:** Original tracklist, main release ID, versions count.

**Brug til:** Find den "rigtige" version af et album, se hvor mange pressings der findes.

---

### discogs_get_master_versions
Alle pressings/versioner af en master.

```json
{
  "master_id": 1234,
  "format": "Vinyl",
  "country": "Japan",
  "label": "Brain",
  "per_page": 25,
  "page": 1
}
```

**Brug til:** Find sjældne pressings, specifikke lande-udgaver.

---

### discogs_get_artist
Kunstner profil.

```json
{
  "artist_id": 5678
}
```

**Returnerer:** Bio, aliases, members (hvis gruppe), groups (hvis solo), name variations.

**Brug til:** VIGTIG! Find forbindelser til andre kunstnere/projekter.

---

### discogs_get_artist_releases
Kunstners diskografi.

```json
{
  "artist_id": 5678,
  "sort": "year|title|format",
  "sort_order": "asc|desc",
  "per_page": 25,
  "page": 1
}
```

**Brug til:** Oversigt over karriere, find tidlige/sene perioder.

---

### discogs_get_label
Label profil.

```json
{
  "label_id": 9012
}
```

**Returnerer:** Profile, parent label, sublabels, contact info.

**Brug til:** Forstå labelets æstetik og fokus.

---

### discogs_get_label_releases
Labels katalog.

```json
{
  "label_id": 9012,
  "sort": "year|title|format",
  "sort_order": "asc|desc",
  "per_page": 25,
  "page": 1
}
```

**Brug til:** GULD! Find andre kunstnere på samme label = kureret samling.

---

### discogs_get_release_stats
Marketplace statistik.

```json
{
  "release_id": 123456
}
```

**Returnerer:** num_have, num_want, lowest_price.

**Brug til:**
- Høj wants/lav haves = kultklassiker
- Pris indikerer sjældenhed

---

### discogs_get_user_collection
Brugers samling.

```json
{
  "username": "optional",
  "folder_id": 0,
  "per_page": 25,
  "page": 1
}
```

---

### discogs_get_user_wantlist
Brugers ønskeliste.

```json
{
  "username": "optional",
  "per_page": 25,
  "page": 1
}
```

---

### discogs_get_collection_value
Estimeret samlings-værdi.

```json
{
  "username": "optional"
}
```

**Returnerer:** minimum, median, maximum value.

---

## Prioriteret Workflow

1. `discogs_search` → Find release ID
2. `discogs_get_release` → Hent credits, styles, label
3. `discogs_get_artist` → Find aliases/members
4. `discogs_get_label_releases` → Find lignende kunstnere
5. `discogs_get_release_stats` → Tjek kultværdi
