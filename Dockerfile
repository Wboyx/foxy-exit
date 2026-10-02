FROM python:3.12-alpine
WORKDIR /app
RUN pip install --no-cache-dir aiohttp
COPY app.py .
EXPOSE 3000
CMD ["python", "app.py"]
