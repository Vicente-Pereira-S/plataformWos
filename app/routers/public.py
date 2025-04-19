from fastapi import APIRouter

router = APIRouter()

@router.get("/publico/test")
def test_public():
    return {"mensaje": "¡Funciona router público!"}
