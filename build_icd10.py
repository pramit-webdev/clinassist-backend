from icd_rag import ICD10RAG

rag = ICD10RAG()
rag.build_from_csv("data/ICD10codes.csv")
print("ICD-10 index created")
