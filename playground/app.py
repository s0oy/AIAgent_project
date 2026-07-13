import json, time
from flask import Flask, render_template, request, Response, stream_with_context
from dotenv import load_dotenv
from anthropic import Anthropic

# .env 파일에 있는 API 키를 읽어 환경변수로 등록
load_dotenv

app = Flask(__name__)    # Flask 웹 서버
client = Anthropic()     # Claude API 클라이언트

# 화면에서 선책할 수 있는 모델 목록
# id : 실제 API에 보낼 모델 이름
# name/description : 화면에 보여줄 용도
MODELS = {
    "haiku": {
        "id": "claude-haiku-4-5",
        "name": "Haiku 4.5",
        "description": "가장 빠른 답변",
    },
    "sonnet": {
        "id": "claude-sonnet-4-6",
        "name": "Sonnet 4.6",
        "description": "일상적인 작업에 가장 효율적",
    },
    "opus": {
        "id": "claude-opus-4-5",
        "name": "Opus 4.5",
        "description": "복잡한 작업용",
    },
}

# 대화 기록 저장소
# LLM은 이전 대화를 기억하지 못하므로 여기에 쌓아둔 대화를 
# 매 요청마다 통째로 다시 보내어 맥락이 이어짐 
# 구조: {"세션id_모델키": [{rold, content}, {role, content}, ...]}
conversations = {}

def send(data):
    # 딕셔너리를 SSE 형식 문자열로 만들어 줌
    # SSE(Server-Sent Events) 규격상 'data:내용 \\n\n' 형태여야 
    # 브라우저가 실시간 스트림으로 받아들임
    return f"data: {json.dumps(data)}\n\n"

@app.route("/")
def index():
    # 브라우저 접속 시 채팅 화면 보여줌
    # MODELS를 함께 넘겨서 HTML이 모델 선택 버튼을 그릴 수 있게 함
    return render_template("index.html", models=MODELS)

@app.route("/chat", methods=["POST"])
def chat():
    # 사용자 메시지를 받아 선택한 모델로 호출하고 응답 실시간 스트리밍
    # 1) 브라우저가 보낸 값 꺼내기
    data = request.json
    model_key = data["model"]
    user_message = data["message"]     # 사용자가 입력한 질문
    session_id = data.get("session_id", "default")    # 대화방 구분용

    # 브라우저에서 오는 값은 전부 문자열이라 숫자로 변환
    # temperature : 답변의 무작위성 (0에 가까울수록 일관되고 높을수록 창의적)
    # max_tokens : 답변 최대 길이 (길이 제한이자 비용 상한)
    temperature = float(data.get("temperature", 1.0))
    max_tokens = int(data.get("max_tokens", 1000))

    # 2) 모델과의 대화 기록 가져오기
    # 모델별로 히스토리를 나눠야 대화가 섞이지 않음
    conv_key = f"{session_id}_{model_key}"
    if conv_key not in conversations:
        conversations[conv_key] = []   # 첫 대화면 빈 리스트 생성

    history = conversations[conv_key]
    history.append({"role":"user", "content": user_message})   # 내 질문 추가

    # 3) 실제 API에 보낼 모델 이름
    model_id = MODELS[model_key]["id"]

    # 4) 답변을 조각조각 흘려보내기
    def generate():
        start_time = time.time()    # 응답 속도 측정 시작
        
        # stream()은 답변이 완성될 때까지 기다리지 않고 모델이 생성하는 즉시 조각 단위로 받아옴
        with client.messages.stream(
            model=model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=history,     # 누적된 전체 대화를 매번 다시 보냄
        ) as stream:
            response = ""    # 전체 답변을 모아둘 변수

            # 조각이 올 때마다 즉시 브라우저로 전송
            for text in stream.text_stream:
                response += text            # 나중에 저장하기 위해 모아둠
                yield send({"text":text})   # 바로 브라우저로 보냄

            # 다 끝나면 전체 답변 기록에 저장
            history.append({"role":"assistant", "content":response})

            # 마지막으로 통계 전송
            usage = stream.get_final_message().usage
            elapsed = round(time.time() - start_time, 2)

            yield send({
                "done": True,                          # 브라우저에 "끝났다" 신호
                "input_tokens": usage.input_tokens,    # 보낸 토큰 수 (대화가 길어질수록 증가 = 비용 증가)
                "output_tokens": usage.output_tokens,  # 받은 토큰 수
                "elapsed": elapsed,                    # 응답에 걸린 시간
            })
    
    # generate()가 만드는 스트림을 SSE 형식으로 응답
    # stream_with_context : 스트리밍 도중에도 request 등에 접근할 수 있게 유지해주는 래퍼
    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",   # '이건 SSE 스트림이다'라고 명시
    )

@app.route("/reset", methods=["POST"])
def reset():
    # 선택한 모델의 대화 기록 지움
    data = request.json
    session_id = data.get("session_id", "default")
    model_key = data.get("model", "")

    conv_key = f"{session_id}_{model_key}"
    conversations.pop(conv_key, None)

    return {'status':'ok'}

if __name__ == "__main__":
    app.run(debug=True, port=5001)