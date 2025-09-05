from app.rag_runtime import _DOCS_DIR, build_rag_context
print("DOCS_DIR =", _DOCS_DIR)                 # should print an absolute .../project/docs
print(build_rag_context("what is in the guide?", k=3)[:300])