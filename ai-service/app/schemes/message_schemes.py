from pydantic import BaseModel, Field, AwareDatetime
from typing import List, Optional, Union
from enum import Enum
from datetime import datetime


class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


class MessageToSend(BaseModel):
    content: str
    role: RoleEnum = RoleEnum.user
    user_id: str = 'test_user'
    chat_id: str = 'test_chat'

    def to_llm_message(self) -> dict:
        return {
            "role": self.role.value,
            "content": self.content
        }


class MessageSent(MessageToSend):
    id: int
    created_at: datetime
    updated_at: Union[datetime, None] = None


class ChatToLoad(BaseModel):
    id: str
    user_id: str
    message_count_limit: int = 10


class ChatToSend(ChatToLoad):
    messages: List[MessageToSend]

    def append(self, message: MessageToSend) -> None:
        self.messages.append(message)

    def to_llm_chat(self) -> List[dict]:
        return [message.to_llm_message() for message in self.messages]

    @classmethod
    def from_list_of_dicts(cls, messages: List[dict], id: str, user_id: str) -> "ChatToSend":
        chat = cls(id=id, user_id=user_id, messages=[])
        for message in messages:
            chat.append(MessageToSend(
                content=message["content"],
                role=RoleEnum(message["role"]),
                user_id=user_id,
                chat_id=id
            ))
        return chat


class ChatLoaded(ChatToSend):
    pass 