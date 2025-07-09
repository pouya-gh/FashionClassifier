from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from typing import Annotated
import asyncio
import json


from ..database.models import User
from ..utils.auth import get_current_user

router = APIRouter()

# a dictionarry of connected users queues
connected_clients_queues = dict()
# a lock for the list of connected clients queues to prevent race conditions
clients_list_lock = asyncio.Lock()

async def status_event_generator(request: Request, user: User):
    message_queue = f"taskmessages:{user.id}"

    # create a new queue for this user and add it to the dictionary
    # with the way this is implementated, if a user have different connection
    # to this endpoint, they will receive messages on all their connections
    queue = asyncio.Queue()
    async with clients_list_lock:
        connected_clients_queues[message_queue] = queue

    try:
        while True:       
            if await request.is_disconnected():
                print('client disconnected')
                break

            message = await queue.get()
            queue.task_done() # inform this queue that the message has been processed
            yield message
    except asyncio.CancelledError as e:
        print(f"disconnected from client {request.client}")
    except json.JSONDecodeError:
        print(f"Invalid message json format")
    finally:
        async with clients_list_lock:
            del connected_clients_queues[message_queue]


@router.get('/notifications')
async def run(
        request: Request,
        current_user: Annotated[User, Depends(get_current_user)]
):
    event_generator = status_event_generator(request, current_user)
    return EventSourceResponse(event_generator)