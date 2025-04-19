import random
import string

def generar_codigo_grupo(longitud: int = 6) -> str:
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choices(caracteres, k=longitud))
