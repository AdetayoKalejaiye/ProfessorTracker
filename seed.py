import os

from app import app, live_professors_for_search


DEFAULT_LIVE_QUERIES = [
    "MIT",
    "Stanford",
    "Harvard",
    "Carnegie Mellon",
    "UC Berkeley",
    "Caltech",
    "Princeton",
    "Yale",
    "Columbia",
    "University of Michigan",
    "Georgia Tech",
    "UT Austin",
    "UCLA",
    "NYU",
    "Northwestern",
]


def seed():
    queries = [
        query.strip()
        for query in os.environ.get("OPENALEX_SEED_QUERIES", ",".join(DEFAULT_LIVE_QUERIES)).split(",")
        if query.strip()
    ]

    with app.app_context():
        total = 0
        for query in queries:
            professors = live_professors_for_search(query, "", 50)
            total += len(professors)
            print(f"Synced {len(professors)} live faculty profiles for {query}")
        print(f"Finished warming live cache with {total} profiles")


if __name__ == "__main__":
    seed()
