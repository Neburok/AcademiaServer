from academiaserver.search.base import SearchEngine


class KeywordSearchEngine(SearchEngine):
    def search(self, notes: list[dict], query: str) -> list[dict]:
        normalized_query = query.lower().strip()
        if not normalized_query:
            return []

        results = []
        for note in notes:
            haystack = " ".join(
                [
                    str(note.get("title", "")),
                    str(note.get("content", "")),
                    " ".join(note.get("tags", [])),
                    " ".join(
                        note.get("metadata", {})
                        .get("enrichment", {})
                        .get("topics", [])
                    ),
                ]
            ).lower()
            if normalized_query in haystack:
                results.append(note)

        return results
