# Fixtures

Real `searchAuctions` responses from fragment.com (captured 2026-09-28, unauthenticated), cut down to a few
representative rows. Only the listing rows were removed; the surrounding markup is untouched.

- `usernames_statuses.html`, `numbers_statuses.html`, `gifts_statuses.html`: one item per distinct status
- `usernames_search_durov.html`, `numbers_search.html`: whole search results, including the "Show more" footer
- `gifts_page2.json`: a paginated (`offset_id`) response, `{"part": true, "body": ..., "foot": ...}`
