import asyncio

async def f():
    print("INSIDE ASYNC F")

if __name__ == "__main__":
    print("BEFORE RUN")
    asyncio.run(f())
    print("AFTER RUN")
