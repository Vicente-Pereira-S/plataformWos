from fastapi import APIRouter

router = APIRouter()

@router.get("/grupos/test")
def test_group():
    return {"mensaje": "¡Funciona router de grupos!"}
