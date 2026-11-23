# SeeSound: one image, run twice (learner app on 8502, Dev/rating app on 8501). The 1.2 GB phone-recogniser model is NOT inside the image: mount it at /model.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 git && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
 && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir "transformers>=4.40"
COPY app /srv/app
ENV FRICATIVE_LOGS=/data/logs FRICATIVE_PROFILES=/data/profiles W2V_DIR=/model SEESOUND_CAMLOG=off PYTHONUNBUFFERED=1
WORKDIR /srv/app
CMD ["streamlit", "run", "learner_app.py", "--server.port=8502", "--server.address=0.0.0.0", "--server.headless=true"]
