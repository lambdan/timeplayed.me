from fastapi import HTTPException


def bad_request(msg="Bad request"):
    raise HTTPException(status_code=400, detail=msg)


def unauthorized(msg="Unauthorized"):
    raise HTTPException(status_code=401, detail=msg)


def not_found(msg="Not found"):
    raise HTTPException(status_code=404, detail=msg)


def service_unavailable(msg="Service unavailable"):
    raise HTTPException(status_code=503, detail=msg)
