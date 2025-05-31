from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

import redis.asyncio as redis 

from typing import Annotated
import asyncio
import json


from ..database.models import User
from ..utils.auth import get_current_user

router = APIRouter()

async def status_event_generator(request: Request, user: User):
    message_queue = f"taskmessages:{user.id}"
    redis_connection = redis.Redis(connection_pool=request.app.state.redis_pool)
    try:
        while True:       
            if await request.is_disconnected():
                print('client disconnected')
                break
            message = await redis_connection.brpop(message_queue)
            # print(f"[hihihi] {message} received")
            yield json.loads(message[1])
    except asyncio.CancelledError as e:
        print(f"disconnected from client {request.client}")
    except json.JSONDecodeError:
        print(f"Invalid message json format")
    finally:
        await redis_connection.close()


@router.get('/notifications')
async def run(
        request: Request,
        current_user: Annotated[User, Depends(get_current_user)]
):
    event_generator = status_event_generator(request, current_user)
    return EventSourceResponse(event_generator)