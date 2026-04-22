from fastapi import APIRouter, status, Depends, HTTPException, Body
from fastapi.security import HTTPBearer

from sqlalchemy import select

from auth.password import hash_password, verify_password
from database.connection import get_session
from user.request import SignUpRequest, LogInRequest, HealthProfileRequest
from user.models import User, HealthProfile
from user.response import UserResponse
from auth.jwt import create_access_token, verify_user

router = APIRouter(tags=["User"])

@router.post(
    "/users",
    summary="회원가입 API",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
)
async def signup_handler(
    body: SignUpRequest,
    session = Depends(get_session),
):
    # 1) 이메일 중복 검사
    stmt = select(User).where(User.email == body.email)
    result = await session.execute(stmt)
    user = result.scalar()

    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 가입된 이메일입니다."
        )

    # 2) 비밀번호 해싱(암호화)
    password_hash = hash_password(plain_password=body.password)

    # 3) 회원 데이터 저장
    new_user = User(
        email=body.email,
        password_hash=password_hash,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user) # id, created_at 새로고침
    
    return new_user


    # 1) 데이터 입력 (이메일, 비밀번호)
    # 2) 이메일 중복 검사 -> 이미 DB에 저장된 회원 데이터 중 해당 이메일로 가입한 사람이 이미 있는지 확인
    # 3) 비밀번호 해싱(암호화)
    # 4) 회원 데이터 저장
    # 5) 응답


@router.post(
    "/users/login",
    summary="로그인 API",
    status_code=status.HTTP_200_OK,
)
async def login_handler(
    body: LogInRequest,
    session = Depends(get_session)
):
    # 1) 데이터 입력 (email, password)
    # 2) email로 사용자 조회
    stmt = select(User).where(User.email == body.email)
    result = await session.execute(stmt)
    user = result.scalar()

     # 3) body.password <-> 사용자.password_hash 비교 검증
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="등록되지 않은 이메일입니다.",
        )
   
    verified = verify_password(
        plain_password=body.password,
        password_hash=user.password_hash
    )

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 일치하지 않습니다.",
        )
    # 4) JWT(JSON Web Token) 토큰 발급 
    access_token = create_access_token(user_id=user.id)
    return {"access_token" : access_token}


@router.post(
    "/health-profiles",
    summary="건강 프로필 생성 API",
    status_code=status.HTTP_201_CREATED,
)
async def create_health_profile_handler(
    # 클라이언트가 보낸 Authorization Header를 읽어줌
    user_id = Depends(verify_user),
    body: HealthProfileRequest = Body(...),
    session = Depends(get_session),
):
    
    # 1)건강 프로필 데이터 입력

    # 2)건강 프로필 중복 검사
    stmt = (
        select(HealthProfile)
        .where(HealthProfile.user_id == user_id)
    )
    result = await session.execute(stmt)
    existing_profile = result.scalar()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 건강 프로필이 존재합니다.",
        )

    # 3) 건강 프로필 생성 & 저장
    profile_data: dict = body.model_dump()
    new_profile = HealthProfile(user_id=user_id, **profile_data)

    session.add(new_profile)
    await session.commit()
    await session.refresh(new_profile)
    # 4) 응답
    return new_profile