from fastapi import APIRouter, File, HTTPException, Depends, UploadFile
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import io
import skimage.io
from app.db.base import get_db
from app.repositories.openai_repository import OpenAIRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.xray_scan_evaluation_repository import XRayScanEvaluationRepository
from app.schemes.message_schemes import MessageToSend, MessageSent, RoleEnum
from app.schemes.message_schemes import ChatToLoad, ChatToSend, ChatLoaded

openai_router = APIRouter(
    prefix="/openai",
    tags=["openAI"],
    responses={404: {"description": "Not found"}},
)

@openai_router.get(
    '/azure_demo',
    summary="Get Azure OpenAI demo response",
    description="Get a demo response from Azure OpenAI",
    response_description="Demo response successful",
    status_code=200,
    responses={
        200: {"description": "Demo response successful"},
        500: {"description": "Internal server error"}
    }
)
async def get_azure_demo_response() -> str:
    """
    Get a demo response from Azure OpenAI.
    - **Returns**: A string response from the OpenAI model.
    """
    openai_repo = OpenAIRepository()
    try:
        response = openai_repo.get_azure_demo_prediction()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def __create_new_chat(
    message: MessageToSend,
    db: Session,
    ) -> MessageSent:
    """
    Create a new chat with the OpenAI model.
    - **chat**: The chat object to be sent to the OpenAI model.
    - **Returns**: A JSON response with the chat result.
    - **Raises**: 400 if the input is invalid, 500 for internal server errors.
    """
    try:
        openai_repo = OpenAIRepository()
        new_chat = openai_repo.get_new_chat_with_base_assistant(message)
        chat_repo = ChatRepository()
        new_chat = chat_repo.insert_chat(db, new_chat)
        completion = openai_repo.get_chat_completion(new_chat)
        completion_inserted = chat_repo.insert_message(db, completion)
        return completion_inserted
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@openai_router.post(
    '/new_chat',
    summary="Create a new chat",
    description="Create a new chat with the OpenAI model",
    response_description="Chat created successfully",
    response_model=MessageSent,
    status_code=200,
    responses={
        200: {"description": "Chat created successfully"},
        400: {"description": "Invalid input"},
        500: {"description": "Internal server error"}
    }
)
async def create_new_chat(
    message: MessageToSend,
    db: Session = Depends(get_db),
    ) -> MessageSent:
    """
    Create a new chat with the OpenAI model.
    - **chat**: The chat object to be sent to the OpenAI model.
    - **Returns**: A JSON response with the chat result.
    - **Raises**: 400 if the input is invalid, 500 for internal server errors.
    """
    return await __create_new_chat(message, db)


@openai_router.post(
    '/load_chat',
    summary="Load a chat",
    description="Load a chat with the OpenAI model",
    response_description="Chat loaded successfully",
    response_model=ChatLoaded,
    status_code=200,
    responses={
        200: {"description": "Chat loaded successfully"},
        400: {"description": "Invalid input"},
        404: {"description": "Chat not found"},
        500: {"description": "Internal server error"}
    }
)
async def load_chat(
    chat: ChatToLoad,
    db: Session = Depends(get_db),
    ) -> ChatLoaded:
    """
    Load a chat with the OpenAI model.
    - **chat**: The chat object to be sent to the OpenAI model.
    - **Returns**: A JSON response with the chat result.
    - **Raises**: 400 if the input is invalid, 500 for internal server errors.
    """
    try:
        chat_repo = ChatRepository()
        loaded_chat = chat_repo.load_chat(db, chat)
        if not loaded_chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return loaded_chat
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@openai_router.post(
    '/message',
    summary="Send a message and get a response",
    description="Send a message to the OpenAI model and get a response",
    response_description="Response received successfully",
    response_model=MessageSent,
    status_code=200,
    responses={
        200: {"description": "Response received successfully"},
        400: {"description": "Invalid input"},
        500: {"description": "Internal server error"}
    }
)
async def message(
    message: MessageToSend,
    db: Session = Depends(get_db),
    ) -> MessageSent:
    """
    Send a message to the OpenAI model and get a response.
    It loads the previous chat from the database if it exists.
    - **message**: The message object to be sent to the OpenAI model.
    - **Returns**: A JSON response with the message result.
    - **Raises**: 400 if the input is invalid, 500 for internal server errors.
    """
    try:
        chat_repo = ChatRepository()
        loaded_chat = chat_repo.load_chat_by_message(db, message)
        if not loaded_chat.messages:
            return await __create_new_chat(message, db)
        messageSent = chat_repo.insert_message(db, message)
        loaded_chat.append(messageSent)
        openai_repo = OpenAIRepository()
        completion = openai_repo.get_chat_completion(loaded_chat)
        completion_inserted = chat_repo.insert_message(db, completion)
        return completion_inserted
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

async def __get_xray_evaluation(xray_scan_upload: UploadFile) -> dict:
    """
    Get the prediction for the X-ray scan.
    - **xray_scan**: The X-ray scan file to be evaluated.
    - **Returns**: A dict response with the evaluation result.
    """
    evaluater = XRayScanEvaluationRepository()
    # Read the image file
    image_bytes = await xray_scan_upload.read()
    xray_scan = skimage.io.imread(io.BytesIO(image_bytes))
    if xray_scan is None:
        raise ValueError("Error: Image is not valid.")
    result = evaluater.evaluate_xray_scan(xray_scan)
    return result

@openai_router.post(
    '/interpret_xray_scan',
    summary="Interpret X-ray scan",
    description="Interpret X-ray scan and provide diagnosis",
    response_description="Interpretation successful",
    status_code=200,
    responses={
        200: {"description": "Interpretation successful"},
        400: {"description": "Invalid input"},
        500: {"description": "Internal server error"}
    }
)
async def evaluate_xray_scan(
    content: str,
    user_id: str = 'test_user',
    chat_id: str = 'test_chat',
    xray_scan_upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    ) -> MessageSent:
    """
    Evaluate X-ray scan and provide diagnosis.
    - **xray_scan**: The X-ray scan file to be evaluated.
    - **Returns**: A JSON response with the evaluation result.
    - **Raises**: 400 if the input is invalid, 500 for internal server errors.
    """
    try:
        xray_scan_evaluation = await __get_xray_evaluation(xray_scan_upload)
        openai_repo = OpenAIRepository()
        message = MessageToSend(
            role=RoleEnum.user.value,
            content=content,
            user_id=user_id,
            chat_id=chat_id,
        )
        chat_repo = ChatRepository()
        previous_chat = chat_repo.load_chat_by_message(db, message)
        if previous_chat is None:
            previous_chat = ChatToSend.from_first_user_message(
                first_message_from_user=message,
            )
        evaluation_chat = openai_repo.interpret_xray_scan_evaluation(
            xray_scan_evaluation=xray_scan_evaluation,
            previous_chat=previous_chat,
            first_message_from_user=message,
        )
        inserted_chat = chat_repo.insert_chat(db, evaluation_chat)
        return inserted_chat.messages[-1]
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error") 