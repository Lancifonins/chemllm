This is a LLM agent based on Gemini, with access to functions allowing it to draw, read, search chemicals and structures. It could serve as a local deployed assistant for organic lab day to day operations.

Please dowload prompt-toolkit and rdkit before using:
#pip install prompt-toolkit

#uv add rdkit

Update 2026/04/02:
Now agent could help get neweest papers from a researcher. The agent is also managing an author watchlist for user, researchers could be added, modified, removed from the list and the user could get new publication updates from the watchlist. For now, ORCID is required for logging and tracking researcher, due to the name duplication issue in publications.

Update 2026/03/26:
Now agent could get the commercial avalibility data for compounds, which could be integerated to structure-based searching or name/CAS number based searching.