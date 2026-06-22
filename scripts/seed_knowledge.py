"""Seed knowledge base with example learning materials."""

import asyncio

from app.db.vector.loader import load_text
from app.db.connection import get_pool, close_pool


SEED_DATA = [
    {
        "topic": "Python 异步编程",
        "content": """Python 异步编程使用 async/await 语法。
async def 用于定义协程函数，调用该函数会返回一个协程对象。
await 用于等待一个协程完成，它只能在 async 函数内部使用。
asyncio 是 Python 的标准异步 I/O 库，提供了事件循环（Event Loop）。
事件循环负责调度和执行协程，原理类似于 JavaScript 的事件循环。
asyncio.run() 是运行协程的入口函数。
asyncio.gather() 可以并发执行多个协程。
asyncio.create_task() 创建一个 Task 对象，将协程调度到事件循环中。
与多线程不同，协程是单线程的并发，通过协作式调度实现。
这意味着没有 GIL 竞争，但也不适合 CPU 密集型任务。
对于 I/O 密集型任务（网络请求、文件读写），异步编程能大幅提升性能。""",
    },
    {
        "topic": "Python 装饰器",
        "content": """Python 装饰器是一种设计模式，用于在不修改原函数代码的情况下增加额外功能。
装饰器本质上是一个函数，它接受一个函数作为参数，返回一个新的函数。
@decorator 语法是 func = decorator(func) 的语法糖。
常见的装饰器用途包括：日志记录、性能计时、权限检查、缓存等。
functools.wraps 装饰器用于保留原函数的元信息（如 __name__、__doc__）。
带参数的装饰器需要三层嵌套：外层接收装饰器参数，中层接收函数，内层是包装逻辑。
类装饰器使用 __call__ 方法实现，可以保持状态。
装饰器可以叠加使用，执行顺序是从下到上（靠近函数定义的先执行）。""",
    },
    {
        "topic": "RESTful API 设计",
        "content": """REST（Representational State Transfer）是一种 Web API 设计风格。
核心原则：
1. 资源导向：URL 表示资源（名词），HTTP 方法表示操作（动词）
2. 无状态：每个请求包含所有必要信息，服务器不保存客户端状态
3. 统一接口：使用标准 HTTP 方法（GET/POST/PUT/DELETE/PATCH）
4. 表现层：资源可以有多种表示（JSON、XML、HTML）
最佳实践：
- 使用名词复数形式：/users 而不是 /getUsers
- 版本化 API：/v1/users
- 使用合适的 HTTP 状态码：200成功、201创建、400错误请求、404未找到、500服务器错误
- 分页：?page=1&limit=20
- 过滤和排序：?status=active&sort=-created_at""",
    },
]


async def seed():
    print("Starting seed data import...")
    pool = await get_pool()
    print(f"Connected to database (pool size: {pool.get_size()})")

    for item in SEED_DATA:
        count = await load_text(
            text=item["content"],
            source_name=item["topic"],
            metadata={"topic": item["topic"]},
        )
        print(f"  [{item['topic']}] → {count} chunks inserted")

    await close_pool()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
