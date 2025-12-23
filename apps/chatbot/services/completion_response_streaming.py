import asyncio

from django.http import StreamingHttpResponse

def _sse(data: str) -> bytes:
    return f"data: {data}\n\n".encode("utf-8")

async def sse_stream(request):
    async def event_stream():
        sentence1 = "Is it possible to learn the power?"
        i = 0
        while i != len(sentence1):
            try:
                chunk = sentence1[i]
                print(chunk)
                yield chunk
                i += 1
                await asyncio.sleep(0.2)
            except asyncio.CancelledError:
                print("Cancelled at event stream")
                break
            except Exception as e:
                # 다른 예외 처리
                print(f"An error occured: {e}")
                break

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    return response