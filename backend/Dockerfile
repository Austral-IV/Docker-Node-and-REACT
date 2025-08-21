

FROM python:3.11

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir setuptools requests redis fastapi uvicorn kombu httpx python-multipart

COPY . .
EXPOSE 8000
# CMD ["uvicorn", "main:app", "--reload"]
CMD ["uvicorn", "main:app", "--reload", "--cors"]

