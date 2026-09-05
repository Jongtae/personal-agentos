FROM python:3.12-slim
WORKDIR /app
COPY personal_agent /app/personal_agent
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8080
CMD ["python", "-m", "personal_agent.runtime"]
