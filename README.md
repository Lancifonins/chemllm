This is a LLM agent based on Gemini, with access to functions allowing it to draw, read, search chemicals and structures. It could serve as a local deployed assistant for organic lab day to day operations.

Please dowload prompt-toolkit and rdkit before using:
#pip install prompt-toolkit

#uv add rdkit

Update 2026/03/26:
Now agent could get the commercial avalibility data for compounds, which could be integerated to structure-based searching or name/CAS number based searching.