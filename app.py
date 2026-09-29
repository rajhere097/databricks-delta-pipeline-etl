from fastapi import FastAPI, UploadFile, File
import pandas as pd
from io import StringIO

# Create the FastAPI application
app = FastAPI(title='Agent Support API')


# Create the file-upload endpoint
@app.post('/upload')
async def upload_file(file: UploadFile = File(...)):

    # Read the uploaded file
    contents = await file.read()

    # Convert CSV bytes to text
    csv_data = StringIO(contents.decode('utf-8'))

    # Convert CSV into a Pandas DataFrame
    df = pd.read_csv(csv_data)

    # Convert DataFrame into JSON records
    records = df.to_dict(orient='records')

    return {'filename': file.filename,
        'records_received': len(records),
        'data': records}