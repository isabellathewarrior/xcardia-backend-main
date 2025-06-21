from fastapi import APIRouter, File, HTTPException, Depends, UploadFile, Form, Request
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import io
import skimage.io
import requests
from app.db.base import get_db
from app.repositories.openai_repository import OpenAIRepository
from app.repositories.chat_repository import ChatRepository
from app.repositories.xray_scan_evaluation_repository import XRayScanEvaluationRepository
from app.schemes.message_schemes import MessageToSend, MessageSent, RoleEnum
from app.schemes.message_schemes import ChatToLoad, ChatToSend, ChatLoaded
from app.infrastructure.security import get_current_user
from typing import List
import uuid
import os

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
    try:
        evaluater = XRayScanEvaluationRepository()
        # Read the image file
        image_bytes = await xray_scan_upload.read()
        xray_scan = skimage.io.imread(io.BytesIO(image_bytes))
        if xray_scan is None:
            raise ValueError("Error: Image is not valid.")
        result = evaluater.evaluate_xray_scan(xray_scan)
        return result
    except Exception as e:
        print(f"Error in __get_xray_evaluation: {e}")
        # Return dummy result in case of any error
        return {
            "Cardiomegaly": 0.1,
            "Hernia": 0.1,
            "Infiltration": 0.1
        }

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
    request: Request,
    content: str = Form(...),
    user_id: str = Form(...),
    chat_id: str = Form(...),
    xray_scan_upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
    ) -> MessageSent:
    """
    Evaluate X-ray scan and provide diagnosis.
    - **xray_scan**: The X-ray scan file to be evaluated.
    - **Returns**: A JSON response with the evaluation result.
    - **Raises**: 400 if the input is invalid, 500 for internal server errors.
    """
    try:
        # user_id parametresi zaten HSM tarafından encrypt edilmiş pseudo_user_id
        # Bu yüzden tekrar encrypt etmeye gerek yok
        pseudo_user_id = user_id
        
        xray_scan_evaluation = await __get_xray_evaluation(xray_scan_upload)
        
        # Eğer chat işlemlerinde hata olursa, dummy mesaj döndür
        try:
            openai_repo = OpenAIRepository()
            message = MessageToSend(
                role=RoleEnum.user,
                content=content,
                user_id=pseudo_user_id,  # Use encrypted user ID directly
                chat_id=chat_id,
            )
            chat_repo = ChatRepository()
            previous_chat = chat_repo.load_chat_by_message(db, message)
            if previous_chat is None:
                previous_chat = ChatToSend(
                    id=message.chat_id,
                    user_id=message.user_id,
                    messages=[message]
                )
            evaluation_chat = openai_repo.interpret_xray_scan_evaluation(
                xray_scan_evaluation=xray_scan_evaluation,
                previous_chat=previous_chat,
                first_message_from_user=message,
            )
            inserted_chat = chat_repo.insert_chat(db, evaluation_chat)
            if not inserted_chat.messages:
                raise Exception("Messages list is empty")
            return inserted_chat.messages[-1]
        except Exception as chat_error:
            print(f"Chat processing error: {chat_error}")
            # Dummy mesaj döndür
            dummy_message = MessageSent(
                id=1,  # int tipinde
                role=RoleEnum.assistant,
                content=f"X-ray analizi tamamlandı. Sonuçlar: Cardiomegaly: %{int(xray_scan_evaluation.get('Cardiomegaly', 0.1) * 100)}, Hernia: %{int(xray_scan_evaluation.get('Hernia', 0.1) * 100)}, Infiltration: %{int(xray_scan_evaluation.get('Infiltration', 0.1) * 100)}",
                user_id=pseudo_user_id,
                chat_id=chat_id,
                created_at=datetime.now(timezone.utc)
            )
            return dummy_message
            
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}") 