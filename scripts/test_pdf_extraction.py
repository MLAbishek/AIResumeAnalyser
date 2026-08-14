from app.ingestion.pdf_loader import PDFLoader


loader = PDFLoader()

document = loader.load(
    "data/raw/jd/jd001.pdf",
    document_id="JD_001"
)

print("=" * 80)
print("DOCUMENT ID:", document.document_id)
print("DOCUMENT TYPE:", document.document_type)
print("PAGES:", len(document.pages))
print("=" * 80)

for page in document.pages:

    print(f"\n--- PAGE {page.page_number} ---\n")

    print(page.text)

print("\n" + "=" * 80)
print("FULL TEXT")
print("=" * 80)

print(document.text)