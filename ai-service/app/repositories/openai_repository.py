from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import AzureOpenAI
import os
import json
from typing import Union

from app.schemes.message_schemes import MessageToSend, ChatToSend, RoleEnum

# Load environment variables from .env file
load_dotenv('.env.prod')

class OpenAIRepository:
    _instance = None
    _openAI_api_version: Union[str, None] = None
    _openAI_endpoint: Union[str, None] = None
    _openAI_model_name: Union[str, None] = None
    _openAI_deployment: Union[str, None] = None
    _openAI_api_key: Union[str, None] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenAIRepository, cls).__new__(cls)
            cls._instance._openAI_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
            cls._instance._openAI_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            cls._instance._openAI_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME")
            cls._instance._openAI_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            cls._instance._openAI_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        return cls._instance

    def __get_new_client(self):
        return AzureOpenAI(
                api_version=self._openAI_api_version,
                azure_endpoint=self._openAI_endpoint,
                api_key=self._openAI_api_key,
            )
    
    def __load_azure_demo_chat(self) -> list:
        """
        Load the Azure OpenAI demo chat messages from a JSON file.
        - **Returns**: A list of messages for the chat completion.
        """
        b = os.path.dirname(os.path.abspath(__file__))
        demo_chat_file_name = "azure_openai_demo_chat.json"
        file_path = os.path.join(b, "..", "data", demo_chat_file_name)
        with open(file_path, 'r') as file:
            messages = json.load(file)
        return messages
    
    def get_azure_demo_prediction(self) -> str:
        """
        Get a demo prediction from Azure OpenAI.
        - **Returns**: A string response from the OpenAI model.
        """
        client = self.__get_new_client()
        messages=self.__load_azure_demo_chat()
        response = client.chat.completions.create(
            messages=messages,
            max_completion_tokens=250,
            model=self._openAI_model_name,
        )
        return response.choices[0].message.content.strip()
    
    def __load_initial_chat_with_assistant(self, file_name: str) -> list:
        """
        Load the initial chat with the base assistant from a JSON file.
        - **Returns**: A ChatLoaded object with the initial chat data.
        """
        b = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(b, "..", "data", file_name)
        chat_data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            chat_data = json.load(file)
        return chat_data
 
    def __load_initial_chat_with_base_assistant(self) -> list:
        """
        Load the initial chat with the base assistant from a JSON file.
        - **Returns**: A ChatLoaded object with the initial chat data.
        """
        initial_chat_file_name = "initial_chat_with_base_assistant.json"
        return self.__load_initial_chat_with_assistant(initial_chat_file_name)
    
    def __expand_initial_messages_with_user(
            self, 
            initial_chat_messages: list,
            first_message_from_user: MessageToSend,
        ) -> list:
        for message in initial_chat_messages:
            message["user_id"] = first_message_from_user.user_id
            message["chat_id"] = first_message_from_user.chat_id
        return initial_chat_messages

    def __get_initial_chat_with_base_assistant(
            self, 
            first_message_from_user: MessageToSend,
        ) -> list:
        initial_chat_messages = self.__load_initial_chat_with_base_assistant()
        initial_chat_messages = self.__expand_initial_messages_with_user(
            initial_chat_messages,
            first_message_from_user,
        )
        return initial_chat_messages

    def get_new_chat_with_base_assistant(
            self, 
            first_message_from_user: MessageToSend,
        ) -> ChatToSend:
        """
        Initialize a new chat with the OpenAI model.
        - **chat**: The chat object to be sent to the OpenAI model.
        - **Returns**: A JSON response with the chat result.
        """
        initial_chat_messages = self.__get_initial_chat_with_base_assistant(
            first_message_from_user,
        )
        new_chat = ChatToSend.from_first_user_message(
            first_message_from_user=first_message_from_user,
            messages=initial_chat_messages,
        )
        new_chat.append(first_message_from_user)
        return new_chat

    def get_chat_completion(
            self, 
            chat: ChatToSend,
        ) -> MessageToSend:
        """
        Get a chat completion from the OpenAI model.
        - **chat**: The chat object to be sent to the OpenAI model.
        - **Returns**: A JSON response with the chat result.
        """
        client = self.__get_new_client()
        response = client.chat.completions.create(
            messages=chat.to_llm_messages(),
            max_completion_tokens=5000,
            model=self._openAI_model_name,
        )
        return MessageToSend(
            role=response.choices[0].message.role,
            content=response.choices[0].message.content.strip(),
            chat_id=chat.id,
            user_id=chat.user_id,
        )
    
    def __load_initial_chat_with_xray_assistant(self) -> list:
        """
        Load the initial chat with the base assistant from a JSON file.
        - **Returns**: A ChatLoaded object with the initial chat data.
        """
        initial_chat_file_name = "initial_chat_with_xray_assistant.json"
        return self.__load_initial_chat_with_assistant(initial_chat_file_name)
    
    def __get_initial_chat_with_xray_assistant(
            self, 
            xray_scan_evaluation: dict,
            first_message_from_user: MessageToSend,
        ) -> list:
        initial_chat_messages = self.__load_initial_chat_with_xray_assistant()
        content = initial_chat_messages[0]["content"] 
        content = content + "\n" + json.dumps(xray_scan_evaluation, indent=4)
        initial_chat_messages[0]["content"] = content
        initial_chat_messages = self.__expand_initial_messages_with_user(
            initial_chat_messages,
            first_message_from_user,
        )
        return initial_chat_messages
 
    def interpret_xray_scan_evaluation(
            self, 
            previous_chat: ChatToSend,
            xray_scan_evaluation: dict,
            first_message_from_user: MessageToSend,
        ) -> ChatToSend:
        """
        Interpret the X-ray scan evaluation and provide a diagnosis.
        - **chat**: The chat object to be sent to the OpenAI model.
        - **Returns**: A JSON response with the chat result.
        """
        initial_chat_messages = self.__get_initial_chat_with_xray_assistant(
            xray_scan_evaluation,
            first_message_from_user,
        )
        xray_assistant_chat = ChatToSend.from_first_user_message(
            first_message_from_user=first_message_from_user,
            messages=initial_chat_messages,
        )
        complete_chat = ChatToSend(
            id=previous_chat.id,
            user_id=previous_chat.user_id,
            messages=previous_chat.messages + xray_assistant_chat.messages,
        )
        xray_assistant_chat.append(first_message_from_user)
        interpretation = self.get_chat_completion(chat=complete_chat)
        xray_assistant_chat.append(interpretation)
        return xray_assistant_chat 