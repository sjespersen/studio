# Only the standard library: the app and its pages on a slim Python. No GPU of its own: the
# renders run in ComfyUI, the shot list on a chat model's API.
FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f
COPY *.py page.html login.html comfy-nodes.txt /app/
USER 1000:1000
EXPOSE 8078
CMD ["python", "/app/app.py"]
