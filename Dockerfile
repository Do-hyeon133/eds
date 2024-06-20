# Python 3.9 이미지를 베이스로 사용
FROM python:3.9

# 작업 디렉토리를 /app으로 설정
WORKDIR /app

# 애플리케이션 종속성 설치
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY . .

# Flask 서버가 사용할 포트 번호
EXPOSE 5000

# Flask 서버 실행 명령어
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
