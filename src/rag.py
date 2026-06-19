def ensure_index():
    return None


def search_guides(query, n_results=2):
    return [
        f"Guide result for: {query}"
    ]


def rag_ask(question):
    results = search_guides(question)

    if not results:
        return "I could not find anything relevant in your guides."

    return "Based on your guides:\n\n" + "\n\n".join(results)