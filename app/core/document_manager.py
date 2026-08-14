from pathlib import Path
from app.core.schemas import DocumentMetadata
import hashlib

class DocumentManager:
    """Generates stable document identity and metadata."""

    def calculate_checksum(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        sha256 = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(8192), b""):
                sha256.update(chunk)
                
        return sha256.hexdigest()

    def generate_document_id(self, file_path: str) -> str:
        return self.calculate_checksum(file_path)

    def build_metadata(self, file_path: str) -> DocumentMetadata:
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = path.stat()
        
        return DocumentMetadata(
            file_name=path.name,
            file_size=stat.st_size,
            content_type="application/pdf",
            checksum= self.calculate_checksum(file_path),
        )
    
    def create_document_metadata(
        self,
        file_path: str,
        ) -> tuple[str, DocumentMetadata]:
        document_id = self.generate_document_id(file_path)
        metadata = self.build_metadata(file_path)

        return document_id, metadata    