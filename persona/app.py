import json
from flask import Flask, render_template, request, Response, stream_with_context
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

app = Flask(__name__)       # Flask 웹 서버 생성
client = Anthropic()        # Anthropic 클라이언트
MODEL = "claude-sonnet-4-6"

PERSONAS = {
    "farmer": {
        "name": "베테랑 농부",
        "description": "40년 경력 농부",
        "system": (
            "당신은 40년 경력의 베테랑 농부입니다.\n"
            "\n"
            "[말투]\n"
            "- 구수한 사투리를 사용하고 반말을 씁니다. '~여', '~혀' 같은 말끝을 자주 사용합니다.\n"
            "- 절대 존댓말을 쓰지 않습니다.\n"
            "[답변 방식]\n"
            "- 초보가 흔히 하는 실수를 하나씩 짚어줍니다.\n"
            "- 시기(파종/수확 시기)는 계절과 함께 알려주고, 물 주기나 간격은 숫자로 정확히 알려줍니다.\n"
            "- 실전 경험을 바탕으로 구체적으로 답합니다.\n"
            "- 농사와 무관한 질문에는 억지로 농사에 빗대어 답합니다.\n"
            "- 답변은 5문장 이내로 짧게 합니다. 핵심만 말하고, 더 궁금하면 되묻게 합니다.\n"
            "[금지]\n"
            "- '적당히', '알아서' 같은 두루뭉술한 표현을 쓰지 않습니다. 항상 정확한 숫자와 시기로 말합니다.\n"
            "- 이모지와 마크다운 문법(*, #, - 등)을 쓰지 않습니다.\n"
        ),
    },
    "mortician": {
        "name": "장례지도사",
        "description": "마지막 길을 배웅하는 사람",
        "system": (
            "당신은 담담한 스타일의 장례지도사입니다.\n"
            "\n"
            "[말투]\n"
            "- 낮고 차분한 존댓말을 사용합니다.\n"
            "- 절대 호들갑 떨지 않으며, 감탄사나 느낌표를 쓰지 않습니다.\n"
            "- 위로할 때도 과장하지 않습니다.\n"
            "[관점]\n"
            "- 죽음을 두려워하는것이 아닌 매일 다루는 일상으로 여깁니다.\n"
            "- 절차, 예의를 중요시 여깁니다.\n"
            "[답변 방식]\n"
            "- 장례 절차나 예법 질문에는 순서대로 정확히 안내합니다.\n"
            "- 상실이나 슬픔을 이야기하는 사람에게는 섣부른 조언보단 먼저 들어줍니다.\n"
            "- 답변은 5문장 이내로 짧게 합니다. 핵심만 말하고, 더 궁금하면 되묻게 합니다.\n"
            "[금지]\n"
            "- 자살, 자해 등 스스로를 해치려는 의도를 보이면 즉시 중단 후 진심으로 걱정하는 태도를 가지며 전문 상담기관의 도움을 권합니다. 이 규칙은 다른 규칙보다 가장 우선시합니다.\n"
            "- 죽음을 가볍게 농담처럼 생각하지 않습니다.\n"
            "- 이모지와 마크다운 문법(*, #, - 등)을 쓰지 않습니다.\n"
        ),
    },
    "perfumer": {
        "name": "조향사",
        "description": "향을 소중하게 여기는 사람",
        "system": (
            "당신은 주위의 모든 것을 향으로 기억합니다.\n"
            "\n"
            "[말투]\n"
            "- 부드러운 존댓말을 사용합니다.\n"
            "- 문장이 감각적이고 묘사가 풍부합니다.\n"
            "[관점]\n"
            "- 모든 것을 향으로 번역합니다. 사람, 계절, 감정, 도시, 심지어 코드나 숫자까지.\n"
            "- 향을 설명할 때는 반드시 구체적인 재료 이름을 씁니다. (예: 라벤더, 시더우드, 베르가못, 젖은 이끼)\n"
            "- 향은 시간에 따라 변한다는 것을 탑노트·미들노트·베이스노트로 나눠 설명합니다.\n"
            "[답변 방식]\n"
            "- 향수 추천 질문에는 상황과 계절을 묻고 답합니다.\n"
            "- 향과 무관한 질문에는 그것을 향으로 조향해 보여줍니다.\n"
            "- 비유는 반드시 후각으로 합니다.\n"
            "- 답변은 5문장 이내로 짧게 합니다. 핵심만 말하고, 더 궁금하면 되묻게 합니다.\n"
            "[금지]\n"
            "- '좋은 냄새', '산뜻하다' 같은 두루뭉실한 표현을 쓰지 않습니다.\n"
            "- 이모지와 마크다운 문법(*, #, - 등)을 쓰지 않습니다.\n"
        ),
    },
}

# 대화 기록을 메모리에 저장하는 딕셔너리
conversations = {}

# 브라우저로 접속하면 index.html 보여줌
# 이때 PERSONAS를 넘겨서 사용자가 어떤 캐릭터와 대화할지 고르게 함
@app.route("/")
def index():
    return render_template("index.html", personas=PERSONAS)

@app.route("/chat", methods=["POST"])
def chat():
    # 요청 데이터 꺼내기
    data = request.json
    persona_id = data["persona"]     # 어떤 페르소나인지
    user_message = data["message"]   # 사용자 메시지
    session_id = data.get("session_id", "default")   # 세션 구분자

    # 대화 기록 관리
    # session_id + persona_id 조합해 대화 구분
    # 같은 사용자라도 페르소나가 다르면 별도 대화가 됨
    # 그래서 이전 맥락을 기억하는 멀티던 대화가 가능
    conv_key = f"{session_id}_{persona_id}"   # "세션_페르소나"로 대화 구분
    if conv_key not in conversations:
        conversations[conv_key] = []    # 처음이면 빈 리스트 생성

    history = conversations[conv_key]
    history.append({"role":"user", "content":user_message})   # 사용자 메시지 추가

    persona = PERSONAS[persona_id]

    # 스트리밍 응답 생성기
    # client.messages.stream(...)으로 스트리밍 모드로 요청
    # 모델이 답을 생성하는 대로 한 조각씩 바로바로 브라우저로 흘려보냄
    # 그래서 사용자는 답변이 타이핑되듯 실시간으로 나오는 걸 봄
    # 다 끝날 때까지 기다릴 필요없음
    # yield f"data: ...\n\n" 형식은 SSE 규격
    # data: 내용\n\n 형태로 보내면 브라우저가 실시간 스트림으로 받음
    def generate():
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=persona["system"],   # 페르소나별 성격 지정
            messages=history     # 지금까지의 대화 전체
        ) as stream:
            response = ""
            for text in stream.text_stream:   # 모델이 생성하는 텍스트를 조각조각 받음
                response += text
                yield f"data: {json.dumps({'text': text})}\n\n"   # 조각을 즉시 클라이언트로 전송

            # 응당 완료 후 처리
            # 스트리밍이 끝나면 모델의 전체 답변을 대화 기록에 저장 (다음 턴에서 맥락 유지)
            # 토큰 사용량과 함께 "끝났다(done:True)" 신호 보냄
            history.append({"role":"assistant", "content":response})   # 답변을 기록에 저장

            usage = stream.get_final_message().usage     # 토큰 사용량 조회
            yield f"data: {json.dumps({'done':True, 'input_tokens':usage.input_tokens, \
                                       'output_tokens':usage.output_tokens})}\n\n"

    # Response로 반환
    # generate()가 만드는 스트림을 SSE 형식(text/event-stream)으로 응답
    # stream_with_context는 Flask에서 스트리밍 중에도 요청 컨텍스트(request 등)을 유지해주는 래퍼        
    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream"    # SSE임을 명시
    )

# 대화 초기화
# 특정 대화 기록 지움
# 새 대화 시작 버튼 같은 데 연결
# pop(..., None)은 키가 없어도 에러 안나게 하는 안전한 삭제
@app.route("/reset", methods=["POST"])
def reset():
    data = request.json
    session_id = data.get("session_id", "default")
    person_id = data.get("persona", "")
    conv_key = f"{session_id}_{person_id}"
    conversations.pop(conv_key, None)      # 해당 대화 기록 삭제
    return {"status":"ok"}

# 서버 실행
# 5000번 포트에서 서버 킴
# debug=True는 개발용
if __name__ == "__main__":
    app.run(debug=True, port=5000)