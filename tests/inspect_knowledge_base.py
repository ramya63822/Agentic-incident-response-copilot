
from incident_copilot.vector_store import collection

results = collection.get(
    include=["documents", "metadatas"]
)

print("Total indexed chunks:", len(results["ids"]))

for index, chunk_id in enumerate(results["ids"]):
    print("\n" + "=" * 60)
    print("ID:", chunk_id)
    print("SOURCE:", results["metadatas"][index]["source"])
    print("TYPE:", results["metadatas"][index]["type"])
    print("CHUNK INDEX:", results["metadatas"][index]["chunk_index"])
    print("CONTENT:")
    print(results["documents"][index])
