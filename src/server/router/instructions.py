from starlette.responses import JSONResponse
from langchain_openai_voice.prompt import INSTRUCTIONS


async def get_instructions(request):
    return JSONResponse({"instructions": INSTRUCTIONS})


async def update_instructions(request):
    try:
        data = await request.json()
        new_instructions = data.get("instructions")
        if new_instructions:
            global INSTRUCTIONS
            INSTRUCTIONS = new_instructions
            print(f"Instructions updated: {INSTRUCTIONS}")  # 로그 추가
            return JSONResponse(
                {"status": "success", "message": "Instructions updated"}
            )
        else:
            return JSONResponse(
                {"status": "error", "message": "Invalid or missing instructions"},
                status_code=400,
            )
    except Exception as e:
        print(f"Error updating instructions: {str(e)}")  # 오류 로그 추가
        return JSONResponse(
            {"status": "error", "message": f"Server error: {str(e)}"}, status_code=500
        )
