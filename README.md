# 실시간 음성 ReAct 에이전트

- [소개](#소개)
- [설치](#설치)
- [프로젝트 실행하기](#프로젝트-실행하기)
- [브라우저 열기](#브라우저-열기)
- [Custom Tool 추가하기](#custom-tool-추가하기)
- [Custom System Prompt 작성하기](#custom-system-prompt-작성하기)
- [오류](#오류)

이 프로젝트는 Langchain의 [React-Voice-Agent](https://github.com/langchain-ai/react-voice-agent)을 기반으로 하여 OpenAI API를 통해 Realtime 대화를 구현한 프로젝트입니다.

[LangChain 도구](https://python.langchain.com/docs/how_to/custom_tools/#creating-tools-from-functions)를 활용하여 모델이 도구를 확장하여 호출할 수 있게 작성되었습니다.

## 설치

Python 3.10 이상을 실행 중인지 확인한 다음, 프로젝트를 실행할 수 있도록 `uv`를 설치하세요.

```bash
pip install uv
```

그리고 `OPENAI_API_KEY`와 `TAVILY_API_KEY` 환경 변수가 설정되어 있는지 확인해주세요.

```bash
export OPENAI_API_KEY=your_openai_api_key
export TAVILY_API_KEY=your_tavily_api_key
```

> **_Note_**
Tavily API 키는 Tavily 검색 엔진을 위한 것이며, [여기](https://app.tavily.com/)에서 API 키를 받을 수 있습니다. 이 도구는 예시일 뿐이므로, 사용하지 않아도 됩니다 ([자신만의 도구 추가하기](#자신만의-도구-추가하기) 참조).

## 프로젝트 실행하기

다음 명령어를 실행하세요:

```bash
uv run src/server/app.py
```

## 브라우저 열기

이제 브라우저를 열고 `http://localhost:3000`으로 이동하여 실행 중인 프로젝트를 볼 수 있습니다.

### 마이크 활성화

브라우저가 마이크에 접근할 수 있도록 해야 할 수 있습니다.

- [Chrome](http://localhost:3000/)

## Custom Tool 추가하기

`src/langchain_openai_voice/tools.py` 파일에 Tool의 코드를 작성해서 추가해주세요.

## Custom System Prompt 작성하기

`src/langchain_openai_voice/prompt.py` 파일에 Instruction을 수정해주세요.

## 오류

- `WebSocket connection: HTTP 403`
  - 이 오류는 OpenAI 측의 계정 권한 때문입니다. 계정에 실시간 API에 대한 접근 권한이 없거나 충전금이 부족합니다.
  - 우선, [여기](https://platform.openai.com/playground/realtime)에서 실시간 API 접근 권한이 있는지 확인하세요.
