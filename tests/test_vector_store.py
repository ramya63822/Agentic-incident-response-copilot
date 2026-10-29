
from incident_copilot.vector_store import search_knowledge

queries = [
    "The database is running out of available connections",
    "Payment requests are returning HTTP 500 errors",
    "What should an engineer check before restarting a service?",
    "The application becomes slow before requests fail",
]

for query in queries:
    print("\n" + "=" * 65)
    print("QUERY:", query)

    results = search_knowledge(query, top_k=2)

    for result in results:
        print("\nSource:", result["source"])
        print("Type:", result["type"])
        print("Distance:", round(result["distance"], 4))
        print("Content:", result["content"][:250])
