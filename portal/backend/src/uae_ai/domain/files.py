from pathlib import Path
from fastapi import HTTPException


async def read_document(file):
    name=Path(file.filename or 'document').name[:240]
    suffix=Path(name).suffix.lower()
    try:
        if suffix not in {'.pdf','.txt'}:
            raise HTTPException(415,'Upload a PDF or UTF-8 text file.')
        content=await file.read(10*1024*1024+1)
        if not content or len(content)>10*1024*1024:
            raise HTTPException(413,'Choose a nonempty file smaller than 10 MB.')
        if suffix=='.pdf' and not content.startswith(b'%PDF-'):
            raise HTTPException(422,'This file is not a valid PDF.')
        if suffix=='.txt':
            try: content.decode('utf-8')
            except UnicodeDecodeError: raise HTTPException(422,'Text files must be UTF-8 encoded.') from None
        return name,suffix,content
    finally:
        await file.close()
