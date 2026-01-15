FROM python:3.11-slim

# نصب ffmpeg و پیش‌نیازها
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# تعیین پوشه کاری
WORKDIR /workspace

# کپی فایل‌ها
COPY . .

# نصب کتابخانه‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# دستور اجرا
CMD ["python", "main.py"]
