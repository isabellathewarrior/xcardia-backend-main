from sqlalchemy import desc
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.models.message_model import MessageModel
from app.schemes.message_schemes import MessageToSend, MessageSent, RoleEnum
from app.schemes.message_schemes import ChatToLoad, ChatToSend, ChatLoaded



class ChatRepository:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatRepository, cls).__new__(cls)
        return cls._instance

    def insert_message(
            self, 
            db: Session,
            message: MessageToSend,
        ) -> MessageSent:
        """
        Insert a new message into the database.
        - **db**: The database session.
        - **message**: The message object to be inserted.
        - **Returns**: The inserted message object.
        """
        db_message = MessageModel(**message.model_dump())
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return MessageSent.model_validate(db_message.to_dict())

    def __insert_messages_if_not_exists(
            self,
            db: Session, 
            messages: list[MessageModel],
        ) -> None:
        for msg in messages:
            stmt = insert(MessageModel).values(
                user_id=msg.user_id,
                chat_id=msg.chat_id,
                role=msg.role,
                content=msg.content,
            ).on_conflict_do_nothing()  # Ignore if conflict on unique constraint
            db.execute(stmt)
        db.commit()
        return
        
    def insert_chat(
            self, 
            db: Session,
            chat: ChatToSend,
        ) -> ChatLoaded:
        """
        Insert a new chat into the database.
        - **db**: The database session.
        - **chat**: The chat object to be inserted.
        - **Returns**: The inserted chat object.
        """
        db_messages = [
            MessageModel(**message.model_dump())
            for message in chat.messages
        ]
        try:
            self.__insert_messages_if_not_exists(db, db_messages) 
            refreshed_messages = db.query(MessageModel).filter(
                MessageModel.chat_id == chat.id,
                MessageModel.user_id == chat.user_id
            ).order_by(MessageModel.id.asc()).all()
            messagesSent = [
                MessageSent.model_validate(m.to_dict()) 
                for m in refreshed_messages
            ]
            return ChatLoaded(
                id=chat.id,
                user_id=chat.user_id,
                created_at=messagesSent[0].created_at,
                messages=messagesSent,
            )
        except Exception as e:
            db.rollback()
            print(f"Error inserting chat: {e}")
            raise e


    def load_chat(
            self, 
            db: Session,
            chat: ChatToLoad,
        ) -> ChatLoaded:
        """
        Load a chat from the database.
        - **db**: The database session.
        - **chat**: The chat object to be loaded.
        - **Returns**: The loaded chat object.
        """
        limit = chat.message_count_limit
        if limit < 0:
            limit = 1000000
        db_messages = db.query(MessageModel).filter(
            MessageModel.chat_id == chat.id,
            MessageModel.user_id == chat.user_id,
            MessageModel.role != RoleEnum.system,
        ).order_by(MessageModel.id.asc()).limit(limit).all()
        messagesLoaded = [
            MessageSent.model_validate(m.to_dict()) for m in db_messages
        ]
        return ChatLoaded(
            id=chat.id,
            user_id=chat.user_id,
            messages=messagesLoaded,
            message_count_limit=chat.message_count_limit,
        )

    def load_chat_by_message(
            self, 
            db: Session,
            message: MessageToSend,
        ) -> ChatLoaded:
        """
        Load a chat from the database using a message object.
        - **db**: The database session.
        - **message**: The message object to be used for loading the chat.
        - **Returns**: The loaded chat object.
        """
        chatToLoad = ChatToLoad(
            id=message.chat_id,
            user_id=message.user_id,
        )
        return self.load_chat(db, chatToLoad) 