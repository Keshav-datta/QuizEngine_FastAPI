from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_question_service, get_admin
from app.models.db.user import User
from app.models.dto.common import APIResponse
from app.models.dto.questions import CreateQuestionRequest, OptionResponse, QuestionResponse
from app.services.question_service import QuestionService

router = APIRouter()


@router.post("/quizzes/{quiz_id}/questions")
async def add_question(
    quiz_id: UUID,
    data: CreateQuestionRequest,
    current_user: User = Depends(get_admin),
    service: QuestionService = Depends(get_question_service)
):
    question = await service.add_question(
        quiz_id,
        data,
        current_user.id,
    )

    return APIResponse(
        success=True,
        message="Question added successfully",
        data=QuestionResponse(
            public_id=question.public_id,
            type=question.type,
            question_text=question.question_text,
            marks=question.marks,
            negative_marks=question.negative_marks,
            options=[
                OptionResponse(public_id=option.public_id, option_text=option.option_text)
                for option in question.options
            ],
        ),
    )


@router.get("/quizzes/{quiz_id}/questions")
async def get_questions(
    quiz_id: UUID,
    service: QuestionService = Depends(get_question_service)
):
    questions = await service.get_questions(quiz_id)

    data = [
        QuestionResponse(
            public_id=question.public_id,
            type=question.type,
            question_text=question.question_text,
            marks=question.marks,
            negative_marks=question.negative_marks,
            options=[
                OptionResponse(public_id=option.public_id, option_text=option.option_text)
                for option in question.options
            ],
        )
        for question in questions
    ]

    return APIResponse(
        success=True,
        message="Questions fetched successfully",
        data=data,
    )


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: UUID,
    current_user: User = Depends(get_current_user),
    service: QuestionService = Depends(get_question_service)
):
    await service.delete_question(question_id, current_user.id)

    return APIResponse(
        success=True,
        message="Question deleted successfully",
        data=None,
    )
