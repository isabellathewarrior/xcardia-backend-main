from pydantic import BaseModel, AwareDatetime
from typing import Union

from enum import Enum


class RoleEnum(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class MessageToSend(BaseModel):
    content: str
    role: RoleEnum = RoleEnum.user
    user_id: str = 'test_user'
    chat_id: str = 'test_chat'

    def to_llm_message(self) -> dict:
        """
        Convert the message to a format suitable for LLM processing.
        - **Returns**: A dictionary representing the message.
        """
        return {
            "role": self.role.value,
            "content": self.content,
        }


class MessageSent(MessageToSend):
    id: str
    created_at: AwareDatetime
    updated_at: Union[AwareDatetime, None] = None


class ChatToLoad(BaseModel):
    id: str
    user_id: str
    message_count_limit: int = 10


class ChatToSend(ChatToLoad):
    messages: list[MessageToSend]

    def append(self, message: MessageToSend) -> None:
        """
        Append a new message to the chat.
        - **message**: The message to be appended.
        """
        self.messages.append(message)

    def extend(self, messages: list[MessageToSend]) -> None:
        """
        Extend the chat with a list of messages.
        - **messages**: A list of messages to be appended.
        """
        self.messages.extend(messages)

    def to_llm_messages(self) -> list[dict]:
        """
        Convert the chat messages to a format suitable for LLM processing.
        - **Returns**: A list of dictionaries representing the messages.
        """
        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in self.messages
        ]

    @classmethod
    def from_first_user_message(
        cls, 
        first_message_from_user: MessageToSend,
        messages: list[dict] = [], 
        ) -> "ChatToSend":
        """
        Create a ChatToSend object from LLM messages.
        - **messages**: A list of dictionaries representing the messages.
        - **user_id**: The ID of the user.
        - **Returns**: A ChatToSend object.
        """
        chat = cls(
            id=first_message_from_user.chat_id,
            user_id=first_message_from_user.user_id,
            messages=[MessageToSend(**message) for message in messages],
        )
        return chat

class ChatLoaded(ChatToSend):
    pass 