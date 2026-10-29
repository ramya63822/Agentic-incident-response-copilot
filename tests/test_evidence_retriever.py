
from incident_copilot.evidence_retriever import retrieve_evidence

query = "Payment API database connection failures"

results = retrieve_evidence(query, top_k=3)

print("Query:", results["query"])

print("\nRUNBOOKS:")
for item in results["runbooks"]:
    print(item["source"], item["distance"])
    print(item["content"][:200])

print("\nHISTORICAL INCIDENTS:")
for item in results["historical_incidents"]:
    print(item["source"], item["distance"])
    print(item["content"][:200])
