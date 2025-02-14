from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
import pytesseract
import io

# Initialize the FastAPI app
app = FastAPI()

# Endpoint to extract text from the uploaded image
@app.post("/extract_text/")
async def extract_text(file: UploadFile = File(...)):
    try:
        # Read image from uploaded file
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # Perform OCR to extract text from the image
        extracted_text = pytesseract.image_to_string(image)

        # Return the extracted text as JSON
        return JSONResponse(content={"extracted_text": extracted_text})

    except Exception as e:
        # If an error occurs, return the error message
        return JSONResponse(content={"error": str(e)}, status_code=500)

